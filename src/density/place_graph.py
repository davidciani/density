from math import asin, cos, sin, sqrt

import adbc_driver_postgresql.dbapi
import geopandas
import networkx as nx
import numpy as np
import pynndescent
from numba import njit
from shapely import LineString
from shapely.geometry import LineString
from sqlalchemy import create_engine


# A Numba-optimized haversine distance function
# Assumes input is (lat, lon) in radians
# @njit(float64(float64[::1], float64[::1]))
@njit
def haversine_metric(x: tuple[float, float], y: tuple[float, float]) -> float:
    lat1, lon1 = x
    lat2, lon2 = y

    d_lat = lat2 - lat1
    d_lon = lon2 - lon1

    a = sin(d_lat / 2.0) ** 2 + cos(lat1) * cos(lat2) * sin(d_lon / 2.0) ** 2

    # Clip 'a' to prevent domain errors for very small numerical inaccuracies
    if a > 1:
        a = 1
    if a < 0:
        a = 0

    c = 2.0 * asin(sqrt(a))

    # Distance is in radians; multiply by Earth's radius (6371 km) to get kilometers, if needed.
    # The RNG condition depends only on the relative distances, so multiplying is not necessary.
    return c


# read place data from the database
uri = "postgresql://david@localhost/census"
conn = adbc_driver_postgresql.dbapi.connect(uri)
place_gdf = geopandas.read_postgis(sql="place_popcenter", con=conn, geom_col="geometry")  # type: ignore

# Extract coordinates (longitude, latitude) into a NumPy array
coords_degrees = np.array([[point.x, point.y] for point in place_gdf.geometry])

# Convert coordinates from degrees to radians
# haversine metric requires (latitude, longitude) in radians
coords_radians = np.radians(coords_degrees[:, ::-1])


# Set up pynndescent index with the custom haversine metric
k = 128  # Number of nearest neighbors
index = pynndescent.NNDescent(coords_radians, n_neighbors=k, metric=haversine_metric)
index.prepare()

# Query for approximate k-NN graph
indices, distances = index.query(coords_radians, k=k)


G = nx.Graph()
G.add_nodes_from(range(len(coords_radians)))

for i in range(len(coords_radians)):
    for j_idx in range(k):
        j = indices[i, j_idx]
        if i >= j:
            continue

        d_ij = distances[i, j_idx]
        is_rng_edge = True

        # Check RNG condition against the union of approximate k-NNs of i and j
        neighbors_to_check_i = set(indices[i])
        neighbors_to_check_j = set(indices[j])
        candidate_interlopers = neighbors_to_check_i.union(neighbors_to_check_j)

        for k_node in candidate_interlopers:
            if k_node == i or k_node == j:
                continue

            d_ik = haversine_metric(coords_radians[i], coords_radians[k_node])
            d_jk = haversine_metric(coords_radians[j], coords_radians[k_node])

            if d_ij > max(d_ik, d_jk):
                is_rng_edge = False
                break

        if is_rng_edge:
            G.add_edge(i, j)


lines = [LineString([coords_degrees[u], coords_degrees[v]]) for u, v in G.edges()]

gdf_lines = geopandas.GeoDataFrame(geometry=lines, crs=place_gdf.crs)
gdf_lines["source"] = [u for u, v in G.edges()]
gdf_lines["target"] = [v for u, v in G.edges()]

print(gdf_lines.head())

engine = create_engine(uri)
gdf_lines.to_postgis("place_relative_neighbors_graph", engine, if_exists="replace")

# ax = place_gdf.plot(color="black", markersize=20, figsize=(10, 8))
# gdf_lines.plot(ax=ax, color="red", linewidth=0.8)
# plt.title("Relative Neighborhood Graph")
# plt.xlabel("Longitude (degrees)")
# plt.ylabel("Latitude (degrees)")
# plt.grid(True)
# plt.show()
