import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from math import gamma
import calendar

# --- Step 1: Find and load latest wind speed data CSV ---
import os
import glob

# Find all offshore_ca_wind_*.csv files in project directory
csv_files = glob.glob("g:\\My Drive\\UT_Austin_MSSD\\Semester 2\\03 Sustainable Energy for Built Env\\34 Final project\\Sustainable\\offshore_ca_wind_*.csv")

# Sort by modification time and get most recent
if csv_files:
    latest_file = max(csv_files, key=os.path.getmtime)
    print(f"Using latest wind data file: {latest_file}")
    df = pd.read_csv(latest_file)
else:
    raise FileNotFoundError("No offshore wind data CSV files found in project directory")

# Process data
df.columns = ['year', 'month', 'day_fraction', 'hour', 'minute', 'wind_speed_80m', 'wind_speed_100m', 'wind_speed_120m', 'wind_dir_80m', 'wind_dir_100m', 'wind_dir_120m']

# Filter out invalid wind speeds and outliers
def filter_wind_speeds(speeds):
    """Remove zeros and outliers from wind speed data"""
    speeds = speeds[speeds > 0]  # Remove zeros
    q1, q3 = np.percentile(speeds, [25, 75])
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    return speeds[(speeds >= lower_bound) & (speeds <= upper_bound)]

# Store all heights for reference and comparison
wind_speeds_80m = filter_wind_speeds(df['wind_speed_80m'].dropna().values)
wind_speeds_100m = filter_wind_speeds(df['wind_speed_100m'].dropna().values)
wind_speeds_120m = filter_wind_speeds(df['wind_speed_120m'].dropna().values)

def find_optimal_height():
    """
    Determines the optimal height based on maximum average wind speed.
    
    Returns:
        tuple: (optimal_height, max_avg_speed) in meters and m/s
    """
    heights = [80, 100, 120]
    avg_speeds = [
        np.mean(wind_speeds_80m),
        np.mean(wind_speeds_100m),
        np.mean(wind_speeds_120m)
    ]
    
    max_idx = np.argmax(avg_speeds)
    return heights[max_idx], avg_speeds[max_idx]

# Determine optimal height for calculations
optimal_height, _ = find_optimal_height()
if optimal_height == 80:
    wind_speeds = df['wind_speed_80m'].dropna().values
elif optimal_height == 100:
    wind_speeds = df['wind_speed_100m'].dropna().values
else:
    wind_speeds = df['wind_speed_120m'].dropna().values

# Store all heights for reference and comparison
wind_speeds_80m = df['wind_speed_80m'].dropna().values
wind_speeds_100m = df['wind_speed_100m'].dropna().values
wind_speeds_120m = df['wind_speed_120m'].dropna().values

print(f"Using wind speeds from optimal height: {optimal_height}m")

# --- Step 2: Calculate Weibull Parameters ---
def weibull(v, k, c):
    """Calculate Weibull probability density function using the exact formula"""
    return (k/c) * (v/c)**(k-1) * np.exp(-(v/c)**k)

# Estimate Weibull parameters using method of moments
mean = np.mean(wind_speeds)
std = np.std(wind_speeds)
shape_k = (std/mean)**-1.086
scale_c = mean / gamma(1 + 1/shape_k)

# Validate parameters
if shape_k <= 0 or scale_c <= 0:
    raise ValueError("Invalid Weibull parameters: shape and scale must be positive")

# Validate parameters
if shape_k <= 0 or scale_c <= 0:
    raise ValueError("Invalid Weibull parameters: shape and scale must be positive")

# Validate parameters
if shape_k <= 0 or scale_c <= 0:
    raise ValueError("Invalid Weibull parameters: shape and scale must be positive")

# --- Step 3: Define Wind Turbine Parameters ---

# Initialize wind speed range for power curve calculations
v_range = np.linspace(0.1, 30, 1000)

from suse.wind.turbine_models import turbine_models

# Load power curve data from CSV (digitized from PNG)
power_curve_df = pd.read_csv(r'g:\My Drive\UT_Austin_MSSD\Semester 2\03 Sustainable Energy for Built Env\34 Final project\Sustainable\power_curve_data.csv')
power_curve_speeds = power_curve_df['wind_speed'].values
power_curve_powers = power_curve_df['power_output'].values


def compare_turbine_models(wind_speeds):
    """
    Compare performance of all available turbine models
    """
    results = []
    
    for model, specs in turbine_models.items():
        # Calculate power output
        power_curve = np.vectorize(lambda v: 0 if v < specs['cut_in'] or v >= specs['cut_out'] else 
            np.interp(v, power_curve_speeds, power_curve_powers))
        
        # Calculate expected power
        power_values = power_curve(v_range)
        expected_power = np.trapz(power_values * prob_density, v_range)
        
        # Calculate annual energy
        annual_energy_kwh = (expected_power * 8760) / 1000
        
        # Calculate capacity factor
        cf = expected_power / specs['rated_power']
        
        results.append({
            'model': model,
            'annual_energy_kwh': annual_energy_kwh,
            'capacity_factor': cf
        })
    
    return pd.DataFrame(results)

# Compute Weibull PDF and Power Output
v_range = np.linspace(0.1, 30, 1000)
prob_density = weibull(v_range, shape_k, scale_c)

# Compare all turbine models
turbine_comparison = compare_turbine_models(wind_speeds)

# Plot comparison results
plt.figure(figsize=(12, 6))
plt.bar(turbine_comparison['model'], turbine_comparison['annual_energy_kwh'], color='blue')
plt.title('Annual Energy Production by Turbine Model')
plt.xlabel('Turbine Model')
plt.ylabel('Annual Energy (kWh)')
plt.xticks(rotation=45)
plt.grid(True)
plt.tight_layout()
plt.show()

# Select best turbine model
best_turbine = turbine_comparison.loc[turbine_comparison['annual_energy_kwh'].idxmax()]
print(f"\nBest Turbine Model: {best_turbine['model']} with {best_turbine['annual_energy_kwh']:.2f} kWh/year")

# Select active turbine model
active_turbine = best_turbine['model']
rated_power = turbine_models[active_turbine]['rated_power']
cut_in = turbine_models[active_turbine]['cut_in']
rated = turbine_models[active_turbine]['rated']
cut_out = turbine_models[active_turbine]['cut_out']

# Load power curve data from CSV (digitized from PNG)
power_curve_df = pd.read_csv(r'g:\My Drive\UT_Austin_MSSD\Semester 2\03 Sustainable Energy for Built Env\34 Final project\Sustainable\power_curve_data.csv')
power_curve_speeds = power_curve_df['wind_speed'].values
power_curve_powers = power_curve_df['power_output'].values

# --- Step 4: Define Turbine Power Curve Function ---
def power_output(v):
    """Calculate power output using interpolation of real power curve data from CSV"""
    if v < cut_in or v >= cut_out:
        return 0
    return np.interp(v, power_curve_speeds, power_curve_powers)

power_curve = np.vectorize(power_output)

# --- Step 5: Compute Weibull PDF and Power Output ---
v_range = np.linspace(0.1, 30, 1000)
prob_density = weibull(v_range, shape_k, scale_c)
power_values = power_curve(v_range)

# --- Step 6: Estimate Annual Energy Output ---
hours_per_year = 8760
# Calculate expected power output by integrating power curve weighted by probability
expected_power = np.trapz(power_values * prob_density, v_range)
annual_energy_wh = expected_power * hours_per_year
annual_energy_kwh = annual_energy_wh / 1000

# --- Step 7: Capacity Factor and CO2 Savings ---
# Calculate capacity factor
cf = expected_power / rated_power
co2_saved_kg = annual_energy_kwh * 0.3  # Assuming 0.3 kg CO2/kWh

# --- Step 8: Monthly Calculations ---
monthly_results = []
for month in range(1, 13):
    monthly_data = df[df['month'] == month]
    # Use wind speeds from optimal height
    if optimal_height == 80:
        monthly_speeds = monthly_data['wind_speed_80m'].dropna().values
    elif optimal_height == 100:
        monthly_speeds = monthly_data['wind_speed_100m'].dropna().values
    else:
        monthly_speeds = monthly_data['wind_speed_120m'].dropna().values
    
    # Filter monthly speeds
    monthly_speeds = filter_wind_speeds(monthly_speeds)
    
    if len(monthly_speeds) > 0:
        # Estimate monthly Weibull parameters
        mean = np.mean(monthly_speeds)
        std = np.std(monthly_speeds)
        k = (std/mean)**-1.086
        c = mean / gamma(1 + 1/k)
        
        # Calculate monthly energy
        monthly_prob = weibull(v_range, k, c)
        monthly_energy = np.trapz(power_values * monthly_prob, v_range) * (hours_per_year / 12)
        monthly_energy_mwh = monthly_energy / 1e6
        
        # Calculate monthly capacity factor
        monthly_cf = monthly_energy / (rated_power * (hours_per_year / 12))
        
        monthly_results.append({
            'month': month,
            'k': k,
            'c': c,
            'energy_mwh': monthly_energy_mwh,
            'capacity_factor': monthly_cf
        })

# Convert to DataFrame for better display
monthly_df = pd.DataFrame(monthly_results)

# Format monthly results table
monthly_df['month'] = monthly_df['month'].apply(lambda x: calendar.month_abbr[x])
monthly_df['energy_mwh'] = monthly_df['energy_mwh'].round(2)
# Store numeric capacity factors before formatting
capacity_factors = monthly_df['capacity_factor'].copy()
monthly_df['capacity_factor'] = monthly_df['capacity_factor'].apply(lambda x: f"{x:.1%}")
monthly_df['k'] = monthly_df['k'].round(2)
monthly_df['c'] = monthly_df['c'].round(2)

# Rename columns for display
monthly_df = monthly_df.rename(columns={
    'month': 'Month',
    'k': 'Weibull k',
    'c': 'Weibull c (m/s)',
    'energy_mwh': 'Energy (MWh)',
    'capacity_factor': 'Capacity Factor'
})

# --- Step 9: Print Results ---
print("\nMonthly Wind Statistics and Energy Production:")
print("="*60)
print(monthly_df.to_string(index=False, justify='center'))
print("="*60)

print("\nAnnual Results:")
print(f"Weibull Shape Factor (k): {shape_k:.2f}")
print(f"Weibull Scale Factor (c): {scale_c:.2f} m/s")
print(f"Annual Energy Output: {annual_energy_kwh:.2f} kWh")
print(f"Capacity Factor: {cf:.2%}")
print(f"CO2 Saved: {co2_saved_kg / 1000:.2f} metric tons/year")

# --- Step 10: Determine Optimal Wind Direction ---
def find_optimal_direction(wind_dir_data):
    """
    Determines the optimal wind direction based on maximum average wind speed.
    
    Args:
        wind_dir_data: Pandas Series containing wind direction data in degrees
        
    Returns:
        tuple: (optimal_direction, average_speed) in degrees and m/s
    """
    # Group directions into 16 cardinal directions (22.5 degree bins)
    bins = np.linspace(0, 360, 17)
    labels = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
              'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    
    # Calculate average speed for each direction bin
    dir_bins = pd.cut(wind_dir_data, bins=bins, labels=labels, include_lowest=True)
    avg_speeds = df.groupby(dir_bins)['wind_speed_120m'].mean()
    
    # Find direction with maximum average speed
    optimal_dir = avg_speeds.idxmax()
    max_avg_speed = avg_speeds.max()
    
    # Calculate turbine orientation angle (0-360 degrees)
    optimal_angle = bins[labels.index(optimal_dir)] + 11.25  # Center of bin
    
    return optimal_dir, max_avg_speed, optimal_angle


# --- Step 11: Plot Power Curve vs Weibull Distribution ---
plt.figure(figsize=(10, 5))
plt.title("Turbine Power Curve & Weibull Wind Speed Distribution (LA Offshore)")
plt.plot(v_range, power_values / 1e6, label='Power Output (MW)', color='orange')
plt.ylabel("Power Output (MW)", color='orange')
plt.xlabel("Wind Speed (m/s)")
plt.grid(True)

plt.twinx()
plt.plot(v_range, prob_density, label='Weibull PDF', color='blue')
plt.ylabel("Probability Density", color='blue')

plt.legend(loc='upper right')
plt.tight_layout()
plt.show()

# --- Step 11: Detailed Power Curve Visualization ---
plt.figure(figsize=(10, 5))
plt.title("GE 2.5-120 Turbine Power Curve")
plt.plot(v_range, power_values / 1e6, label='Power Output', color='green', linewidth=2)

# Mark key operational points
plt.axvline(x=cut_in, color='red', linestyle='--', label=f'Cut-in Speed ({cut_in} m/s)')
plt.axvline(x=rated, color='blue', linestyle='--', label=f'Rated Speed ({rated} m/s)')
plt.axvline(x=cut_out, color='black', linestyle='--', label=f'Cut-out Speed ({cut_out} m/s)')
plt.axhline(y=rated_power/1e6, color='purple', linestyle=':', label=f'Rated Power ({rated_power/1e6} MW)')

# Add annotations
plt.annotate('Cut-in', xy=(cut_in, 0), xytext=(cut_in-1, 0.1),
             arrowprops=dict(facecolor='black', shrink=0.05))
plt.annotate('Rated', xy=(rated, rated_power/1e6), xytext=(rated+1, rated_power/1e6-0.1),
             arrowprops=dict(facecolor='black', shrink=0.05))
plt.annotate('Cut-out', xy=(cut_out, 0), xytext=(cut_out-2, 0.1),
             arrowprops=dict(facecolor='black', shrink=0.05))

plt.xlabel("Wind Speed (m/s)")
plt.ylabel("Power Output (MW)")
plt.legend(loc='upper left')
plt.grid(True)
plt.tight_layout()
plt.show()

# Plot monthly energy production
plt.figure(figsize=(10, 5))
plt.bar(monthly_df['Month'], monthly_df['Energy (MWh)'], color='green')
plt.title("Monthly Energy Production (MWh)")
plt.xlabel("Month")
plt.ylabel("Energy (MWh)")
plt.xticks(range(1, 13))
plt.grid(True)
plt.show()

# Plot monthly capacity factors
plt.figure(figsize=(10, 5))
plt.plot(monthly_df['Month'], capacity_factors, 'o-', color='purple')
plt.title("Monthly Capacity Factors")
plt.xlabel("Month")
plt.ylabel("Capacity Factor")
plt.xticks(range(1, 13))
plt.grid(True)
plt.show()

# --- Step 12: Wind Speed Comparison and Optimal Height Analysis ---
plt.figure(figsize=(12, 6))
plt.title(f"Wind Speed Comparison at Different Heights (Optimal: {optimal_height}m)")

# Create boxplot
box = plt.boxplot([wind_speeds_80m, wind_speeds_100m, wind_speeds_120m], 
                 labels=['80m', '100m', '120m'], patch_artist=True)

# Highlight optimal height
colors = ['lightblue', 'lightblue', 'lightblue']
colors[optimal_height//40 - 2] = 'green'
for patch, color in zip(box['boxes'], colors):
    patch.set_facecolor(color)

plt.ylabel("Wind Speed (m/s)")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

def find_optimal_height():
    """
    Determines the optimal height based on maximum average wind speed.
    
    Returns:
        tuple: (optimal_height, max_avg_speed) in meters and m/s
    """
    heights = [80, 100, 120]
    avg_speeds = [
        np.mean(wind_speeds_80m),
        np.mean(wind_speeds_100m),
        np.mean(wind_speeds_120m)
    ]
    
    max_idx = np.argmax(avg_speeds)
    return heights[max_idx], avg_speeds[max_idx]

optimal_height, max_avg_speed = find_optimal_height()
print(f"\nOptimal Height Analysis:")
print(f"80m Avg Speed: {np.mean(wind_speeds_80m):.2f} m/s")
print(f"100m Avg Speed: {np.mean(wind_speeds_100m):.2f} m/s")
print(f"120m Avg Speed: {np.mean(wind_speeds_120m):.2f} m/s")
print(f"\nOptimal Height: {optimal_height}m (Avg speed: {max_avg_speed:.2f} m/s)")

# --- Step 13: Wind Direction Analysis ---
# Calculate optimal directions for all heights
optimal_dir_80m, max_avg_speed_80m, optimal_angle_80m = find_optimal_direction(df['wind_dir_80m'])
optimal_dir_100m, max_avg_speed_100m, optimal_angle_100m = find_optimal_direction(df['wind_dir_100m'])
optimal_dir_120m, max_avg_speed_120m, optimal_angle_120m = find_optimal_direction(df['wind_dir_120m'])
print(f"\nOptimal Wind Directions:")
print(f"80m: {optimal_dir_80m} (Avg speed: {max_avg_speed_80m:.2f} m/s, Angle: {optimal_angle_80m:.1f}°)")
print(f"100m: {optimal_dir_100m} (Avg speed: {max_avg_speed_100m:.2f} m/s, Angle: {optimal_angle_100m:.1f}°)")
print(f"120m: {optimal_dir_120m} (Avg speed: {max_avg_speed_120m:.2f} m/s, Angle: {optimal_angle_120m:.1f}°)")

# Plot wind direction frequency
plt.figure(figsize=(10, 5))
plt.title("Wind Direction Frequency (120m height)")

# Create wind rose plot
ax = plt.subplot(111, polar=True)
bins = np.linspace(0, 2*np.pi, 17)
labels = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
          'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']

# Calculate direction frequency
wind_dirs = np.radians(df['wind_dir_120m'].dropna())
counts, _ = np.histogram(wind_dirs, bins=bins)

# Plot wind rose
bars = ax.bar(bins[:-1], counts, width=0.4, color='blue', alpha=0.7)
ax.set_theta_zero_location('N')
ax.set_theta_direction(-1)
ax.set_xticks(bins[:-1])
ax.set_xticklabels(labels)

# Highlight optimal direction
optimal_idx = labels.index(optimal_dir_120m)
bars[optimal_idx].set_color('red')

plt.tight_layout()
plt.show()
