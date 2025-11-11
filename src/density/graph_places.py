from math import asin, cos, sin, sqrt

import adbc_driver_postgresql.dbapi
import geopandas
import networkx as nx
import numpy as np
import pynndescent
from matplotlib import pyplot as plt
from numba import njit
from shapely import LineString
from shapely.geometry import LineString


# @njit(float64(float64[::1], float64[::1]))
@njit
def haversine_metric(x: tuple[float, float], y: tuple[float, float]) -> float:
    """
    Calculate the great-circle distance between two points on the earth (specified in radians).
    This version is optimized with Numba.

    Args:
        x: A tuple of (latitude, longitude) in radians for the first point.
        y: A tuple of (latitude, longitude) in radians for the second point.

    Returns:
        The great-circle distance in radians.
    """
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


def main():
    """
    Main function to generate and visualize a Relative Neighborhood Graph (RNG)
    for US census places based on their population centers.
    """
    # 1. DATA LOADING AND PREPARATION
    # Connect to the PostgreSQL database and read place population center data.
    uri = "postgresql://david@localhost/census"
    conn = adbc_driver_postgresql.dbapi.connect(uri)
    place_gdf: geopandas.GeoDataFrame = geopandas.read_postgis(
        sql="place_popcenter", con=conn, geom_col="geometry"
    )  # type: ignore

    # Filter for the contiguous United States, excluding Alaska (02), Hawaii (15), and territories (>56).
    place_gdf: geopandas.GeoDataFrame = place_gdf[
        (place_gdf["state"].astype("int") < 60) & ~place_gdf["state"].isin(["02", "15"])
    ]

    print(place_gdf)

    # Extract point coordinates (longitude, latitude) into a NumPy array.
    coords_degrees = np.array([[point.x, point.y] for point in place_gdf.geometry])

    # Convert coordinates from degrees to radians and swap to (latitude, longitude) order
    # for the haversine metric function.
    coords_radians = np.radians(coords_degrees[:, ::-1])

    # Set up pynndescent index with the custom haversine metric
    k = 128  # Number of nearest neighbors
    index = pynndescent.NNDescent(
        coords_radians,
        n_neighbors=k,
        metric=haversine_metric,
    )
    index.prepare()

    # 2. NEAREST NEIGHBOR SEARCH
    # Query the index to find the k nearest neighbors for each point.
    # This provides a candidate set of neighbors for the RNG construction.
    indices, distances = index.query(coords_radians, k=k)

    # 3. RELATIVE NEIGHBORHOOD GRAPH (RNG) CONSTRUCTION
    G = nx.Graph()
    G.add_nodes_from(range(len(coords_radians)))

    # Iterate through each point and its approximate nearest neighbors to build the RNG.
    for i in range(len(coords_radians)):
        for j_idx in range(k):
            j = indices[i, j_idx]
            if i >= j:
                continue

            d_ij = distances[i, j_idx]
            is_rng_edge = True

            # An edge (i, j) exists in the RNG if no other point k is closer to both i and j.
            # We check this condition only against the union of the approximate k-NNs of i and j for efficiency.
            neighbors_to_check_i = set(indices[i])
            neighbors_to_check_j = set(indices[j])
            candidate_interlopers = neighbors_to_check_i.union(neighbors_to_check_j)

            for k_node in candidate_interlopers:
                if k_node == i or k_node == j:
                    continue

                # Recalculate distances as they might not be in the pre-computed list.
                d_ik = haversine_metric(coords_radians[i], coords_radians[k_node])
                d_jk = haversine_metric(coords_radians[j], coords_radians[k_node])

                if d_ij > max(d_ik, d_jk):
                    is_rng_edge = False
                    break

            if is_rng_edge:
                G.add_edge(i, j)

    # 4. GEODATAFRAME CREATION AND VISUALIZATION
    # Create LineString geometries for each edge in the graph.
    lines = [LineString([coords_degrees[u], coords_degrees[v]]) for u, v in G.edges()]

    gdf_lines = geopandas.GeoDataFrame(geometry=lines, crs=place_gdf.crs)
    gdf_lines["source"] = [u for u, v in G.edges()]
    gdf_lines["target"] = [v for u, v in G.edges()]

    print(gdf_lines.head())

    # Optional: Save the graph edges to a PostGIS table.
    # engine = create_engine(uri)
    # gdf_lines.to_postgis("place_relative_neighbors_graph", engine, if_exists="replace")

    # Plot the original points and the RNG edges.
    ax = place_gdf.plot(color="black", markersize=20, figsize=(10, 8))
    gdf_lines.plot(ax=ax, color="red", linewidth=0.8)
    plt.title("Relative Neighborhood Graph")
    plt.xlabel("Longitude (degrees)")
    plt.ylabel("Latitude (degrees)")
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    main()
