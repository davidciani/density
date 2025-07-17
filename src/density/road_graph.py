"""
road_graph.py - transform OSM road data into a graph.


Osmium command to extract arterial road network:

osmium tags-filter us-latest.osm.pbf w/highway=motorway,motorway_link,trunk,trunk_link,primary_primary_link,secondary,secondary_link,tertiary,tertiary_link -o us-highways-tertiary.osm.pbf

"""

from pathlib import Path

import geopandas as gpd
import osmnx
import osmnx.truncate
import quackosm as qosm
import shapely
from rich.console import Console

console = Console()

REGION = "california"


def main():
    console.log("Loading PBF")
    pbf_path = Path(f"data/osm/{REGION}-latest.osm.pbf")

    tags_filter = {
        "highway": [
            "motorway",
            "motorway_link",
            "trunk",
            "trunk_link",
            "primary",
            "primary_link",
            "secondary",
            "secondary_link",
            "tertiary",
            "tertiary_link",
        ]
    }

    edges = qosm.convert_pbf_to_geodataframe(
        pbf_path,
        tags_filter=tags_filter,
        explode_tags=False,
        keep_all_tags=True,
    )
    edges = edges[edges.index.str.contains("way")]
    edges = edges[edges.geometry.type == "LineString"]

    console.log("Extracting nodes")
    nodes = (
        edges["geometry"]
        .apply(lambda x: shapely.MultiPoint(list(x.coords)))
        .explode()
        .drop_duplicates(ignore_index=True)
    )

    console.log("Getting node coordinates")
    gdf_nodes = gpd.GeoDataFrame(
        nodes.get_coordinates(), geometry=nodes.geometry
    ).rename_axis(index="osmid")

    console.log("Linking edges with node ids")
    # get start and end points
    edges["start_point"] = shapely.get_point(edges.geometry, 0)
    edges["end_point"] = shapely.get_point(edges.geometry, -1)

    edges = edges.reset_index()

    edges = edges.merge(
        gdf_nodes.reset_index(),
        how="left",
        left_on="start_point",
        right_on="geometry",
        suffixes=(None, "_y"),
    ).rename(columns={"osmid": "u"})

    edges = edges.merge(
        gdf_nodes.reset_index(),
        how="left",
        left_on="start_point",
        right_on="geometry",
        suffixes=(None, "_y"),
    ).rename(columns={"osmid": "v"})

    edges["key"] = edges.groupby(["u", "v"]).cumcount() + 1
    edges = edges.set_index(["u", "v", "key"])
    print(edges)

    gdf_edges = edges.rename(columns={"feature_id": "osmid"})[
        [
            "osmid",
            "tags",
            "geometry",
        ]
    ]

    # gdf_edges = edges[~edges.index.duplicated(keep="first")]

    console.log("Creating Graph")
    G = osmnx.convert.graph_from_gdfs(gdf_nodes, gdf_edges)
    # console.log(osmnx.stats.basic_stats(G))

    # console.log("simplify_graph")
    # G_simp = osmnx.simplify_graph(G)
    #
    # console.log("consolidate_intersections")
    # G_cons = osmnx.consolidate_intersections(G_simp)

    console.log("Saving Graph")
    osmnx.io.save_graph_geopackage(G, f"data/out/{REGION}-highways-tertiary.gpkg")
    osmnx.save_graphml(G, f"data/out/{REGION}-highways-tertiary.graphml")


if __name__ == "__main__":
    main()
