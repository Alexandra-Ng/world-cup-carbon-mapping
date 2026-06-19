"""
Aggregate fan travel emissions: headline band + per-team / per-city 

Headline is a BAND: same engine run at three local_share values
knob dominates the uncertainty
"""
import pandas as pd

from geo import attach_coords
from distances import add_distances
from emissions import add_emissions, ASSUMPTIONS

# local_share scenarios for the band (sensitivity)
BANDS = {"upper": 0.0, "central": 0.80, "lower": 0.90}


def load_full(csv_path, local_share):
    cfg = {**ASSUMPTIONS, "local_share": local_share}
    return add_emissions(add_distances(attach_coords(csv_path)), cfg)


def headline_band(csv_path, bands=BANDS):
    return {name: load_full(csv_path, ls)["co2e_t"].sum() for name, ls in bands.items()}


def per_team(df):
    a = df[["team_a", "co2e_a_t"]].rename(columns={"team_a": "team", "co2e_a_t": "co2e_t"})
    b = df[["team_b", "co2e_b_t"]].rename(columns={"team_b": "team", "co2e_b_t": "co2e_t"})
    return pd.concat([a, b]).groupby("team")["co2e_t"].sum().sort_values(ascending=False)


def per_city(df):
    return df.groupby("host_city")["co2e_t"].sum().sort_values(ascending=False)


if __name__ == "__main__":
    csv = "worldcup_matches.csv"
    band = headline_band(csv)
    print("HEADLINE (8 matches) - CO2e tonnes by local_share scenario:")
    for name, ls in BANDS.items():
        print(f"  {name:<8} local_share={ls:.2f}: {band[name]:>12,.0f} t")

    df = load_full(csv, BANDS["central"])
    obs = (~df["attendance_imputed"]).sum()
    print(f"\nCoverage: {obs}/{len(df)} matches with observed attendance")

    print("\nTop fan origins by travel emissions (central), tonnes:")
    print(per_team(df).round().astype(int).to_string())

    print("\nBy host city (central), tonnes:")
    print(per_city(df).round().astype(int).to_string())
