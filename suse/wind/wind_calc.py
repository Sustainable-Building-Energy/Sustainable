import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import weibull_min
import calendar
import os
import glob

# --- Wind Speed Utilities ---
def interpolate_wind_speed(speed, height_from, height_to, alpha=0.14):
    return speed * (height_to / height_from) ** alpha

def filter_wind_speeds(speeds):
    speeds = speeds[speeds > 0]
    q1, q3 = np.percentile(speeds, [25, 75])
    iqr = q3 - q1
    bounds = (q1 - 1.5 * iqr, q3 + 1.5 * iqr)
    return speeds[(speeds >= bounds[0]) & (speeds <= bounds[1])]

# --- Weibull and Rayleigh Functions ---
def fit_weibull_distribution(data):
    params = weibull_min.fit(data, floc=0)
    k, loc, c = params
    return k, c

def weibull(v, k, c):
    return (k/c) * (v/c)**(k-1) * np.exp(-(v/c)**k)

def rayleigh(v, c):
    return (v / c**2) * np.exp(- (v**2) / (2 * c**2))

# --- Power Curve Estimation ---
def region_based_power_output(v):
    v = np.array(v, ndmin=1)
    output = np.zeros_like(v)
    region1 = (v >= cut_in) & (v < rated)
    region2 = (v >= rated) & (v < cut_out)
    output[region1] = rated_power * ((v[region1] - cut_in) / (rated - cut_in)) ** 3
    output[region2] = rated_power
    return output

def betz_limit_curve(v, area, rho=1.225):
    power = 0.5 * rho * area * v**3
    return 0.593 * power

def calculate_cp(power_output, wind_speed, area, rho=1.225):
    wind_power = 0.5 * rho * area * wind_speed ** 3
    with np.errstate(divide='ignore', invalid='ignore'):
        cp = np.where(wind_power != 0, power_output / wind_power, 0)
    return cp

# --- Load Wind Data ---
def load_wind_data(data_dir):
    csv_files = glob.glob(os.path.join(data_dir, "offshore_ca_wind_*.csv"))
    if not csv_files:
        raise FileNotFoundError("No offshore wind data CSV files found")
    latest_file = max(csv_files, key=os.path.getmtime)
    print(f"Using latest wind data file: {latest_file}")
    df = pd.read_csv(latest_file)
    if 'wind_speed_140m' in df.columns:
        df.columns = ['year', 'month', 'day_fraction', 'hour', 'minute',
                     'wind_speed_80m', 'wind_speed_100m', 'wind_speed_120m', 'wind_speed_140m',
                     'wind_dir_80m', 'wind_dir_100m', 'wind_dir_120m']
    else:
        df.columns = ['year', 'month', 'day_fraction', 'hour', 'minute',
                     'wind_speed_80m', 'wind_speed_100m', 'wind_speed_120m',
                     'wind_dir_80m', 'wind_dir_100m', 'wind_dir_120m']
        df['wind_speed_140m'] = df.apply(lambda row: interpolate_wind_speed(
            row['wind_speed_120m'], 120, 140), axis=1)
    return df

# --- Main Processing ---
data_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
df = load_wind_data(data_dir)
wind_speeds = filter_wind_speeds(df['wind_speed_140m'].dropna().values)
shape_k, scale_c = fit_weibull_distribution(wind_speeds)

from suse.wind.turbine_models import turbine_models
active_turbine = 'Siemens_Gamesa_SG_14_236_DD'
turbine_model = turbine_models[active_turbine]
rated_power = turbine_model['rated_power']
cut_in = turbine_model['cut_in']
rated = turbine_model['rated']
cut_out = turbine_model['cut_out']
hub_height = turbine_model['hub_height']
rotor_diameter = turbine_model['rotor_diameter']

v_range = np.linspace(0.1, 30, 1000)
prob_density = weibull(v_range, shape_k, scale_c)

power_curve = np.vectorize(region_based_power_output)
power_values = power_curve(v_range)
rotor_area = np.pi * (rotor_diameter / 2)**2
betz_values = betz_limit_curve(v_range, rotor_area)

hours_per_year = 8760
expected_power = np.trapezoid(power_values * prob_density, v_range)
annual_energy_wh = expected_power * hours_per_year
annual_energy_kwh = annual_energy_wh / 1000
annual_energy_mwh = annual_energy_wh / 1e6
capacity_factor = annual_energy_kwh / (rated_power * hours_per_year / 1000)
co2_saved_kg = annual_energy_kwh * 0.3

# --- Plotting ---
plt.figure(figsize=(12, 6))
ax1 = plt.gca()
ax2 = ax1.twinx()
ax1.plot(v_range, power_values / 1e6, 'b-', label='Power Curve')
ax1.plot(v_range, betz_values / 1e6, 'k--', label='Betz Limit')
ax1.set_ylabel('Power Output (MW)', color='b')
ax2.plot(v_range, prob_density, 'r-', label='Weibull Distribution')
ax2.set_ylabel('Probability Density', color='r')
ax1.set_xlabel('Wind Speed (m/s)')
ax1.axvline(x=cut_in, color='g', linestyle='--', label='Cut-in')
ax1.axvline(x=rated, color='y', linestyle='--', label='Rated')
ax1.axvline(x=cut_out, color='r', linestyle='--', label='Cut-out')
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
plt.title('Power Curve, Weibull Distribution, and Betz Limit')
plt.grid(True)
plt.tight_layout()
plt.savefig('power_curve_with_betz_weibull.png')
plt.close()

# --- Monthly Energy and Capacity Factor Plots ---
# --- Export Monthly Results ---
def calculate_monthly_stats():
    results = []
    for m in range(1, 13):
        monthly_data = filter_wind_speeds(df[df['month'] == m]['wind_speed_140m'].dropna().values)
        if len(monthly_data) > 0:
            k, c = fit_weibull_distribution(monthly_data)
            monthly_prob = weibull(v_range, k, c)
            power_vals = power_curve(v_range)
            energy = np.trapezoid(power_vals * monthly_prob, v_range) * (hours_per_year / 12)
            results.append({
                'Month': calendar.month_abbr[m],
                'Weibull k': round(k, 2),
                'Weibull c (m/s)': round(c, 2),
                'Energy (MWh)': round(energy / 1e6, 2),
                'Capacity Factor': f"{energy / (rated_power * (hours_per_year / 12)):.1%}"
            })
    return pd.DataFrame(results)

def plot_monthly_stats(monthly_df):
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()
    ax1.bar(monthly_df['Month'], monthly_df['Energy (MWh)'], color='b', alpha=0.6, label='Energy (MWh)')
    ax2.plot(monthly_df['Month'], [float(x.strip('%'))/100 for x in monthly_df['Capacity Factor']], 
             'r-o', label='Capacity Factor')
    ax1.set_xlabel('Month')
    ax1.set_ylabel('Energy Production (MWh)', color='b')
    ax2.set_ylabel('Capacity Factor', color='r')
    ax1.tick_params(axis='y', colors='b')
    ax2.tick_params(axis='y', colors='r')
    fig.legend(loc='upper right', bbox_to_anchor=(1, 1), bbox_transform=ax1.transAxes)
    plt.title('Monthly Energy Production and Capacity Factor')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('monthly_energy_capacity_factor.png')
    plt.close()

# --- Export Monthly Results ---
monthly_df = calculate_monthly_stats()
plot_monthly_stats(monthly_df)
def calculate_monthly_stats():
    results = []
    for m in range(1, 13):
        monthly_data = filter_wind_speeds(df[df['month'] == m]['wind_speed_140m'].dropna().values)
        if len(monthly_data) > 0:
            k, c = fit_weibull_distribution(monthly_data)
            monthly_prob = weibull(v_range, k, c)
            power_vals = power_curve(v_range)
            energy = np.trapezoid(power_vals * monthly_prob, v_range) * (hours_per_year / 12)
            results.append({
                'Month': calendar.month_abbr[m],
                'Weibull k': round(k, 2),
                'Weibull c (m/s)': round(c, 2),
                'Energy (MWh)': round(energy / 1e6, 2),
                'Capacity Factor': f"{energy / (rated_power * (hours_per_year / 12)):.1%}"
            })
    return pd.DataFrame(results)

monthly_df = calculate_monthly_stats()
monthly_df.to_csv("monthly_energy_output.csv", index=False)

print("\nAnnual Results:")
print(f"Annual Energy Production: {annual_energy_mwh:.2f} MWh")
print(f"Capacity Factor: {capacity_factor:.2%}")
print(f"CO2 Savings: {co2_saved_kg:.2f} kg CO2")

print("\nMonthly Statistics:")
print(monthly_df.to_string(index=False))
