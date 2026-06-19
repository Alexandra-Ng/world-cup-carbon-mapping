"""Coordinate lookups for World Cup venues and fan origin countries

HOST_CITIES      : host city: (lat, lon) of the venue
COUNTRY_CAPITALS : country (lat, lon) of its capital (the assumed fan origin)

attach_coords() reads the match CSV and adds venue and both-team coordinates,
fails if any city or country name isnt in the lookups 
"""
import pandas as pd

# host city: (lat, lon)
HOST_CITIES = {
    "Atlanta": (33.75, -84.39),
    "Boston": (42.36, -71.06),
    "Dallas": (32.78, -96.80),
    "Houston": (29.76, -95.37),
    "Kansas City": (39.10, -94.58),
    "Los Angeles": (34.05, -118.24),
    "Miami": (25.76, -80.19),
    "New York New Jersey": (40.71, -74.01),
    "Philadelphia": (39.95, -75.16),
    "San Francisco Bay Area": (37.37, -121.97),   # Levi Stadium, Santa Clara
    "Seattle": (47.61, -122.33),
    "Guadalajara": (20.67, -103.35),
    "Mexico City": (19.43, -99.13),
    "Monterrey": (25.69, -100.32),
    "Toronto": (43.65, -79.38),
    "Vancouver": (49.28, -123.12),
}

# country: (lat, lon) of capital (football capital for Scotland)
COUNTRY_CAPITALS = {
    "Mexico": (19.43, -99.13),                 # Mexico City
    "South Africa": (-25.75, 28.19),           # Pretoria
    "South Korea": (37.57, 126.98),            # Seoul
    "Czech Republic": (50.08, 14.44),          # Prague
    "Canada": (45.42, -75.70),                 # Ottawa
    "Bosnia and Herzegovina": (43.85, 18.36),  # Sarajevo
    "United States": (38.91, -77.04),          # Washington DC
    "Paraguay": (-25.28, -57.63),              # Asuncion
    "Qatar": (25.29, 51.53),                   # Doha
    "Switzerland": (46.95, 7.45),              # Bern
    "Brazil": (-15.79, -47.88),                # Brasilia
    "Morocco": (34.02, -6.83),                 # Rabat
    "Australia": (-35.28, 149.13),             # Canberra
    "Turkey": (39.93, 32.86),                  # Ankara
    "Haiti": (18.59, -72.31),                  # Port-au-Prince
    "Scotland": (55.95, -3.19),                # Edinburgh
}


def attach_coords(csv_path):
    df = pd.read_csv(csv_path)

    unknown_cities = sorted(set(df["host_city"]) - set(HOST_CITIES))
    teams = set(df["team_a"]) | set(df["team_b"])
    unknown_countries = sorted(teams - set(COUNTRY_CAPITALS))
    if unknown_cities:
        raise ValueError(f"Unknown host_city values (add to HOST_CITIES): {unknown_cities}")
    if unknown_countries:
        raise ValueError(f"Unknown countries (add to COUNTRY_CAPITALS): {unknown_countries}")

    df["venue_lat"] = df["host_city"].map(lambda c: HOST_CITIES[c][0])
    df["venue_lon"] = df["host_city"].map(lambda c: HOST_CITIES[c][1])
    df["a_lat"] = df["team_a"].map(lambda c: COUNTRY_CAPITALS[c][0])
    df["a_lon"] = df["team_a"].map(lambda c: COUNTRY_CAPITALS[c][1])
    df["b_lat"] = df["team_b"].map(lambda c: COUNTRY_CAPITALS[c][0])
    df["b_lon"] = df["team_b"].map(lambda c: COUNTRY_CAPITALS[c][1])
    return df


if __name__ == "__main__":
    df = attach_coords("worldcup_matches.csv")
    print(f"{len(df)} matches; all venues and countries resolved.\n")
    print(df[["match_id", "host_city", "venue_lat", "venue_lon",
              "team_a", "team_b"]].to_string(index=False))
