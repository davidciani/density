import adbc_driver_postgresql.dbapi
import geopandas
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from shapely import LineString
from sklearn.neighbors import NearestNeighbors
from sqlalchemy import create_engine

# read cbsa data from the database
uri = "postgresql://david@localhost/census"
conn = adbc_driver_postgresql.dbapi.connect(uri)
cbsa_gdf = geopandas.read_postgis(sql="cbsa_popcenter", con=conn, geom_col="geometry")  # type: ignore

# Extract coordinates (longitude, latitude) into a NumPy array
coords_degrees = np.array([[point.x, point.y] for point in cbsa_gdf.geometry])

# Convert coordinates from degrees to radians
# haversine metric requires (latitude, longitude) in radians
coords_radians = np.radians(coords_degrees[:, ::-1])


# Set up the NearestNeighbors model
nbrs = NearestNeighbors(
    n_neighbors=len(coords_radians), algorithm="ball_tree", metric="haversine"
)
nbrs.fit(coords_radians)

# Query for the distance and indices of all neighbors
distances, indices = nbrs.kneighbors(coords_radians)

G = nx.Graph()
G.add_nodes_from(range(len(coords_degrees)))

# Construct the Relative Neighborhood Graph
for i in range(len(coords_degrees)):
    for j in range(i + 1, len(coords_degrees)):
        d_ij = distances[i, indices[i] == j][0]
        is_rng_edge = True

        for k_idx in range(len(coords_degrees)):
            k = indices[i, k_idx]
            if k == i or k == j:
                continue

            d_ik = distances[i, k_idx]
            d_jk_query_result = distances[j, indices[j] == k]

            if d_jk_query_result.size > 0:
                d_jk = d_jk_query_result[0]
                if d_ij > max(d_ik, d_jk):
                    is_rng_edge = False
                    break

        if is_rng_edge:
            G.add_edge(i, j)

lines = [LineString([coords_degrees[u], coords_degrees[v]]) for u, v in G.edges()]

gdf_lines = geopandas.GeoDataFrame(geometry=lines, crs=cbsa_gdf.crs)
gdf_lines["source"] = [u for u, v in G.edges()]
gdf_lines["target"] = [v for u, v in G.edges()]

print(gdf_lines.head())

#engine = create_engine(uri)
#gdf_lines.to_postgis("cbsa_relative_neighbors_graph", engine)

ax = cbsa_gdf.plot(color="black", markersize=10, figsize=(20, 16))
gdf_lines.plot(ax=ax, color="red", linewidth=0.5)
plt.title("Relative Neighborhood Graph")
plt.xlabel("Longitude (degrees)")
plt.ylabel("Latitude (degrees)")
plt.grid(True)
plt.show()
