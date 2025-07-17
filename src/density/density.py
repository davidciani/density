from pathlib import Path

import geopandas as gpd
import pandas as pd
from rich.progress import (
    ProgressColumn,
    Task,
    filesize,
)
from rich.text import Text

TIGER_DATA_DIR = Path("data_tiger2024")
CENSUS_DATA_DIR = Path("data_census")

pd.set_option("display.float_format", lambda x: f"{x:,.0f}")


class RateColumn(ProgressColumn):
    """Renders human readable processing rate."""

    def render(self, task: "Task") -> Text:
        """Render the speed in iterations per second."""
        speed = task.finished_speed or task.speed
        if speed is None:
            return Text("", style="progress.percentage")
        unit, suffix = filesize.pick_unit_and_suffix(
            int(speed),
            ["", "×10³", "×10⁶", "×10⁹", "×10¹²"],
            1000,
        )
        data_speed = speed / unit
        return Text(f"{data_speed:.1f}{suffix} it/s", style="progress.percentage")


# cross_file_dtype = np.dtype(
#     [
#         ("index_near", "<i8"),
#         ("index_far", "<i8"),
#         ("pop_near", "<i8"),
#         ("pop_far", "<i8"),
#         ("distance", "<i8"),
#     ]
# )


# place_schema = pa.schema(
#     [
#         pa.field("index", pa.uint64()),
#         pa.field("geoidfq", pa.string()),
#         pa.field("pop", pa.uint64()),
#         pa.field("name", pa.string()),
#     ]
# )

# pair_schema = pa.schema(
#     [
#         pa.field("index_x", pa.uint64()),
#         pa.field("index_y", pa.uint64()),
#         pa.field("distance", pa.uint64()),
#         pa.field("gravity_score", pa.uint64()),
#     ]
# )

# index_dtype = np.dtype(
#    [
#        ("index", "<i64"),
#        ("geoidfq", "<U16"),
#        ("pop", "<i64"),
#        ("name", "<U64"),
#    ]
# )


def main():

    places_df = pd.read_csv(
       Path("../datasets/places/tl_2020_us_place.csv")
    )[['GEOID','NAME','LSAD','PCICBSA', 'ALAND','AWATER','INTPTLAT','INTPTLON']]

    places_df["GEOIDFQ"] =  "1600000US" + places_df["GEOID"].astype('str')

    
    print(place_pop_df.columns)
    print(place_pop_df)



    place_pop_df.hist(bins=4)


if __name__ == "__main__":
    main()
