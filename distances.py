"""
haversine distances from each fan origin to venue

Adds two columns to the coordinate-attached match table:
    dist_a_km : capital of team_a, venue
    dist_b_km : capital of team_b, venue
Oneway distances, round trip is applied later in the emissions step
"""
import numpy as np
from geo import attach_coords


def haversine(lat1, lon1, lat2, lon2):
    """Great circle distance in km between two (lat, lon) points (vectorized)"""
    R = 6371.0088                       # mean Earth radius [km]
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def add_distances(df):
    df = df.copy()
    df["dist_a_km"] = haversine(df["a_lat"], df["a_lon"], df["venue_lat"], df["venue_lon"])
    df["dist_b_km"] = haversine(df["b_lat"], df["b_lon"], df["venue_lat"], df["venue_lon"])
    return df


if __name__ == "__main__":
    df = add_distances(attach_coords("worldcup_matches.csv"))
    show = df[["match_id", "host_city", "team_a", "dist_a_km", "team_b", "dist_b_km"]].copy()
    show["dist_a_km"] = show["dist_a_km"].round().astype(int)
    show["dist_b_km"] = show["dist_b_km"].round().astype(int)
    print(show.to_string(index=False))
