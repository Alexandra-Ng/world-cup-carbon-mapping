"""Per match fan travel CO2e assuming 50% coming from origin country.

assumptions (all tunable for scenario analysis):
  ef_air_kg_per_pkm : economy air, kg CO2e per passenger-km (DEFRA longhaul 0.15)
  rf_multiplier     : radiative-forcing uplift for aviation (DEFRA advises 1.9)
  local_share       : fraction of the crowd that's local (0 travel)
  round_trip        : count the flight home too (x2 distance)
  fill_factor       : impute missing attendance as capacity * fill_factor
"""
from distances import add_distances
from geo import attach_coords

ASSUMPTIONS = {
    "ef_air_kg_per_pkm": 0.15,
    "rf_multiplier": 1.9,
    "local_share": 0.0,        # assume no locals, by default
    "round_trip": True,
    "fill_factor": 1.0,
}


def add_emissions(df, cfg=ASSUMPTIONS):
    df = df.copy()
    # missing attendance = capacity * fill_factor, flagged
    df["attendance_imputed"] = df["attendance"].isna()
    att = df["attendance"].fillna(df["capacity"] * cfg["fill_factor"])

    travelers = att * (1 - cfg["local_share"]) * 0.5     # half from each country
    trip = 2 if cfg["round_trip"] else 1
    ef = cfg["ef_air_kg_per_pkm"] * cfg["rf_multiplier"] * trip   # kg CO2e per pkm, alin

    df["co2e_a_t"] = travelers * df["dist_a_km"] * ef / 1000.0    # tonnes
    df["co2e_b_t"] = travelers * df["dist_b_km"] * ef / 1000.0
    df["co2e_t"] = df["co2e_a_t"] + df["co2e_b_t"]
    return df


if __name__ == "__main__":
    df = add_emissions(add_distances(attach_coords("worldcup_matches.csv")))
    show = df[["match_id", "team_a", "team_b", "co2e_t"]].copy()
    show["co2e_t"] = show["co2e_t"].round().astype(int)
    print(show.to_string(index=False))
    print(f"\nTotal (8 matches): {df['co2e_t'].sum():,.0f} tonnes CO2e")
    print(f"Per-passenger avg (long-haul round trip): "
          f"{ASSUMPTIONS['ef_air_kg_per_pkm']*ASSUMPTIONS['rf_multiplier']*2*14596/1000:.1f} "
          f"t for a Pretoria to Mexico City round trip")
