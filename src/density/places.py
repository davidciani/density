from pathlib import Path
from typing import cast

import geopandas as gpd
import osmnx
import pandas as pd


def merge_places():
    population = pd.read_csv("data/census/DECENNIALDHC2020.P1-Data.csv")
    population = population.set_index("GEOID")["POP20"]

    place_zips = Path("data/tiger/PLACE/").glob("*.zip")
    place_gdfs = [gpd.read_file(x) for x in place_zips]
    places = pd.concat(place_gdfs)
    places["GEOID"] = "1600000US" + places["GEOID"]
    places = places.set_index("GEOID").sort_index()[
        [
            "STATEFP",
            "NAME",
            # "LSAD",
            "CLASSFP",
            "ALAND",
            "AWATER",
            "geometry",
        ]
    ]

    places = places[~places["STATEFP"].isin(["60", "66", "69", "78"])]
    places = cast(gpd.GeoDataFrame, places.join(population))
    places.to_file("data/out/us_places.gpkg", layer="places_whole")


def trim_places_to_land():
    land = gpd.read_file(
        "data/natural_earth/natural_earth_vector.gpkg/packages/natural_earth_vector.gpkg",
        layer="ne_10m_land",
    )
    places = gpd.read_file("data/out/us_places.gpkg", layer="places_whole")

    land_polygon = land.union_all()
    land_places = places.intersection(land_polygon)

    places = places.set_geometry(land_places)
    places.to_file("data/out/us_places.gpkg", layer="places_trimmed")


def place_representative_point():
    places = gpd.read_file("data/out/us_places.gpkg", layer="places_trimmed")

    # Explode multiparts
    places_exploded = cast(gpd.GeoDataFrame, places.explode(index_parts=True))

    # Calculate the area of each geometry
    places_exploded_projected = places_exploded.to_crs(crs="EPSG:5070")
    places_exploded["area"] = places_exploded_projected.area

    # Get the original index
    places_exploded["original_index"] = places_exploded.index.get_level_values(0)

    # Group by the original index and find the index of the largest geometry
    idx = places_exploded.groupby("original_index")["area"].idxmax()

    # Select the largest geometry for each original multi-part geometry
    largest_geometries = cast(gpd.GeoDataFrame, places_exploded.loc[idx])
    largest_geometries = cast(
        gpd.GeoDataFrame, largest_geometries.reset_index(1, drop=True)
    )
    largest_geometries["point"] = largest_geometries.representative_point()
    print(largest_geometries)

    places = cast(gpd.GeoDataFrame, places.join(largest_geometries["point"]))
    print(places)
    active_geometry_name = places.active_geometry_name
    places.set_geometry("point").drop(columns=active_geometry_name).to_file(
        "data/out/us_places.gpkg",
        layer="place_points",
    )


def places_on_graph():
    G = osmnx.load_graphml(
        "data/out/california-highways-tertiary.graphml", edge_dtypes={"osmid": str}
    )
    places = gpd.read_file("data/out/us_places.gpkg", layer="place_points")

    # places = places[~places["STATEFP"].isin(["02","15"])]
    places = cast(gpd.GeoDataFrame, places[places["STATEFP"] == "06"])

    places_sample = places.sample(100)

    coordinates: pd.DataFrame = places_sample.geometry.get_coordinates()

    places_sample["nearest_node"] = osmnx.nearest_nodes(
        G, coordinates["x"], coordinates["y"]
    )

    print(places_sample)


def main():
    places_on_graph()


if __name__ == "__main__":
    main()
