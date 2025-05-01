from functools import partial
from scipy.optimize import fsolve


def equations(n_c, G_T, U_L, T_c, T_a, τα, NOCT, G_NOCT, n_ref, beta, T_c_ref, n_MPPT, n):
    return (
        n_c * G_T + U_L * (T_c - T_a) - (τα) * G_T,
        U_L * (NOCT - 20) - (τα) * G_NOCT,
        n_ref * (1 - beta * (T_c - T_c_ref)) - n_c,
        n_MPPT * n_c - n,
    )


def solve(unknowns, eqn_system):
    n_c, U_L, T_c, n = unknowns

    # eqn_system = equations3
    return eqn_system(n_c=n_c, U_L=U_L, T_c=T_c, n=n)


def compute_panel_e(
    df,
    τα=0.75,
    NOCT=45.7,
    G_NOCT=800,
    n_ref=0.151,
    beta=0.0045,
    T_c_ref=25,
    n_MPPT=0.9,
    module_area=1.66,
    PV_n_panels=16,
    module_rated_W=250,
    install_cost_per_W=1.3,
    grid_price=0.125,
    verbose=True,
):
    """_summary_

    Parameters
    ----------
    df : _type_
        _description_
    τα : float, optional
        overall transmittance absorbance product, by default 0.75
    NOCT : float, optional
        nominal operating cell temperature, by default 45.7
    G_NOCT : int, optional
        incident radiation under no load (NOCT) conditions, by default 800
    n_ref : float, optional
        module efficiency at rated condition, by default 0.151
    beta : float, optional
        temperature coefficient of module power and efficiency, by default 0.0045
    T_c_ref : int, optional
        cell temperature at rated condition, by default 25
    n_MPPT : float, optional
        maximum power tracking efficiency, by default 0.9
    PV_A : float, optional
        Area per solar panel in meters^2, by default 1.66
    PV_n_panels : int, optional
        number of solar panels to use, by default 16

    Returns
    -------
    pd.DataFrame
        _description_
    """
    if verbose:
        print(f"\nSystem rated power: {PV_n_panels*module_rated_W/1000:,} kW")
        print(f"Total install cost: ${PV_n_panels*module_rated_W*install_cost_per_W:,}")
        print(f"Total area: {PV_n_panels*module_area} m^2")

    df = df.rename(columns={"Temperature": "Dry-bulb (C)"})
    # Prefill fixed values
    # equations2(n_c,U_L,T_c,n,G_T,T_a)
    equations2 = partial(
        equations,
        τα=τα,
        NOCT=NOCT,
        G_NOCT=G_NOCT,
        n_ref=n_ref,
        beta=beta,
        T_c_ref=T_c_ref,
        n_MPPT=n_MPPT,
    )

    x0 = [0.5, 20, 20, 0.5]  # initial guess
    for row_num, row in df.iterrows():
        # Fill iterative values after which equations3 is a function where only n_c,U_L,T_c,n is not defined
        # equations3(n_c,U_L,T_c,n)
        equations3 = partial(
            equations2,
            G_T=row["G_T_fixed"],  # iter
            T_a=row["Dry-bulb (C)"],  # iter
        )
        df.loc[row_num, ["PV_n_c", "PV_U_L", "PV_T_c", "PV_n"]] = fsolve(solve, x0=x0, args=(equations3))
    df["PV_W_e"] = df["G_T_fixed"] * (PV_n_panels * module_area) * df["PV_n"]

    PV_monthly_sum = df["PV_W_e"].sum()
    PV_savings = PV_monthly_sum / 1000 * grid_price
    PV_avg_n = df["PV_n"].mean()

    # print(f'Total PV Electricity: {round(PV_monthly_sum)} W')
    if verbose:
        print(f"Total PV Electricity: {round(PV_monthly_sum/1000):,} kWh/yr")
        print(f"Total Energy Savings: ${round(PV_savings,2):,} ")
        print(f"Avg Efficiency: {round(PV_avg_n,3)}")
    return df
