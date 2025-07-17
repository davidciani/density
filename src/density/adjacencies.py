from itertools import islice
from pathlib import Path
from pprint import pprint

import geopandas as gpd
import matplotlib.pyplot as plt

# DATA_DIR = Path("/Volumes/TheTank/datasets/geo/TIGER2023")
DATA_DIR = Path("data")
CALIFORNIA_DIR = Path(DATA_DIR, "06_California")


def find_adjacent_polygons(polygon, shapefile):
    adjacent_polygons = []
    for index, other_polygon in shapefile.iterrows():
        if polygon.geometry.touches(other_polygon.geometry):
            adjacent_polygons.append(other_polygon)
    return adjacent_polygons


def main():
    print(f"Hello from {__file__}!")

    # #COUNTIES
    # counties = gpd.read_file(Path(DATA_DIR, "00_National/tl_2023_us_county.zip"))[
    #     [
    #         "STATEFP",
    #         "COUNTYFP",
    #         "GEOID",
    #         "NAME",
    #         "NAMELSAD",
    #         "ALAND",
    #         "AWATER",
    #         "geometry",
    #     ]
    # ]

    # counties = counties[counties["STATEFP"] == "06"]

    # counties_cross = pd.merge(
    #     counties, counties[["GEOID", "NAME", "geometry"]], how="cross"
    # )

    # counties_cross["touches"] = counties_cross["geometry_x"].touches(
    #     counties_cross["geometry_y"]
    # )

    # counties_adj = defaultdict(set)

    # for i, row in counties_cross.loc[
    #     counties_cross["touches"], ["GEOID_x", "GEOID_y"]
    # ].iterrows():
    #     counties_adj[row.GEOID_x].add(row.GEOID_y)

    # print(counties_adj)

    # # TRACTS
    # tracts = gpd.read_file(Path(CALIFORNIA_DIR, "tl_2023_06_tract.zip"))

    # tracts_cross = pd.merge(
    #     tracts[["STATEFP", "COUNTYFP", "TRACTCE", "GEOID", "geometry"]],
    #     tracts[["STATEFP", "COUNTYFP", "TRACTCE", "GEOID", "geometry"]],
    #     how="outer",
    #     on=["STATEFP", "COUNTYFP"],
    # ).query("GEOID_x != GEOID_y")

    # tracts_cross["touches"] = tracts_cross["geometry_x"].touches(
    #     tracts_cross["geometry_y"]
    # )

    # print(tracts_cross)

    # BLOCKS
    tabblocks = gpd.read_file(Path(CALIFORNIA_DIR, "tl_2023_06_tabblock20.zip"))

    tabblocks = tabblocks.set_index("GEOID20")

    pprint(tabblocks)

    tabblocks_adj = {}

    for block in islice(tabblocks.itertuples(), 1_000_000):
        adj_blocks = tabblocks[
            tabblocks.geometry.touches(block.geometry)
        ].index.to_list()

        tabblocks_adj[block.Index] = adj_blocks

    #

    #pprint(tabblocks_adj)

    return
    ca_counties.boundary.plot()
    plt.show()
    print(polygon["NAMELSAD"])
    # Print the adjacent polygons
    for adjacent_polygon in adjacent_polygons:
        print(adjacent_polygon["NAMELSAD"])

    # print(ca_counties)


if __name__ == "__main__":
    main()
