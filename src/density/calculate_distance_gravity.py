import os
from pathlib import Path
from typing import Iterable, Union

import geoarrow as ga  # noqa: F401
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import pyogrio
from pyarrow import csv
from pyproj import Geod

StrPath = str | os.PathLike[str]


def load_population_csv(path: Union[str, os.PathLike]) -> pa.Table:
    # Load and join in population numbers
    convert_options = csv.ConvertOptions(
        include_columns=["GEOIDFQ", "POP20"],
        column_types={
            "GEOIDFQ": pa.string(),
            "NAME": pa.string(),
            "POP20": pa.int64(),
        },
    )

    population_tbl = csv.read_csv(path, convert_options=convert_options)
    return population_tbl


def cast_col_to_float64(tbl: pa.Table, column: str) -> pa.Table:
    casted = pc.cast(tbl.column(column), pa.float64())
    return tbl.set_column(tbl.column_names.index(column), column, casted)


def self_cross_join(tbl: pa.Table, suffix=("_U", "_V")) -> pa.Table:
    u_col_names = {col_name: col_name + suffix[0] for col_name in tbl.column_names}
    u_tbl = tbl.rename_columns(u_col_names).add_column(0, "dummy_key", [[1] * len(tbl)])

    v_col_names = {col_name: col_name + suffix[1] for col_name in tbl.column_names}
    v_tbl = tbl.rename_columns(v_col_names).add_column(0, "dummy_key", [[1] * len(tbl)])

    cross_tbl = u_tbl.join(v_tbl, keys="dummy_key").drop_columns(["dummy_key"])
    return cross_tbl


def get_population_table(
    geo_file_path: StrPath | Iterable[StrPath],
    population_file_path: StrPath,
    geoidfq_prefix: str | None = None,
) -> pa.Table:
    if isinstance(geo_file_path, Iterable):
        tables = []
        for x in geo_file_path:
            _, tbl_instance = pyogrio.read_arrow(Path(x).absolute())
            tables.append(tbl_instance)
        tbl = pa.concat_tables(tables)
    else:
        _, tbl = pyogrio.read_arrow(Path(geo_file_path).absolute())

    tbl = tbl.rename_columns(
        {name: name.removesuffix("20") for name in tbl.column_names}
    )

    population_tbl = load_population_csv(population_file_path)

    if "GEOIDFQ" not in tbl.column_names:
        if geoidfq_prefix is None:
            raise ValueError("Must supply GEOIDFQ prefix")

        geoidfq = pc.binary_join_element_wise(
            pa.array([geoidfq_prefix] * len(tbl), type=pa.string()), tbl["GEOID"], ""
        )
        tbl = tbl.append_column("GEOIDFQ", geoidfq)

    tbl = tbl.join(population_tbl, keys="GEOIDFQ")

    # Convert Lat/Lon to floats
    tbl = cast_col_to_float64(tbl, "INTPTLAT")
    tbl = cast_col_to_float64(tbl, "INTPTLON")

    # Add a numeric ID to the table
    rec_count = len(tbl)
    id_arr = pa.array(range(rec_count), type=pa.int64())
    tbl = tbl.add_column(0, "NODE_ID", id_arr)

    return tbl


def calculate_distances(tbl: pa.Table) -> pa.Table:
    lat_u = tbl["INTPTLAT_U"].to_numpy()
    lon_u = tbl["INTPTLON_U"].to_numpy()
    lat_v = tbl["INTPTLAT_V"].to_numpy()
    lon_v = tbl["INTPTLON_V"].to_numpy()

    geod = Geod(ellps="WGS84")

    az_uv, az_vu, distance = geod.inv(
        lon_u,
        lat_u,
        lon_v,
        lat_v,
    )

    tbl = (
        tbl.append_column("AZ_UV", pa.array(az_uv))
        .append_column("AZ_VU", pa.array(az_vu))
        .append_column("DISTANCE", pa.array(distance / 1000))
    )
    return tbl


def calculate_gravity(tbl: pa.Table) -> pa.Table:
    gravity = pc.divide(
        pc.multiply(tbl["POP_U"], tbl["POP_V"]),
        pc.power(tbl["DISTANCE"], pa.scalar(2)),
    )

    return tbl.append_column("GRAVITY", gravity)


def urban_areas():
    # Load urban areas from shapefile
    uac_tbl = get_population_table(
        Path("data/tl_2020/UAC/tl_2020_us_uac20_corrected.zip"),
        Path("data/census/DECENNIALDHC2020.P1-Data_UAC.csv"),
        "400C200US",
    )

    # Save the urban area table for later.
    pq.write_table(uac_tbl, "data/out/uac_populations.parquet")

    # do the cross join
    uac_cross_tbl = self_cross_join(
        uac_tbl.select(["NODE_ID", "POP20", "INTPTLAT", "INTPTLON"])
    )

    # Filter out self match and second matches
    uac_cross_tbl = uac_cross_tbl.filter(pc.field("NODE_ID_U") < pc.field("NODE_ID_V"))

    uac_cross_tbl = calculate_distances(uac_cross_tbl)
    uac_cross_tbl = calculate_gravity(uac_cross_tbl)

    print(uac_cross_tbl)
    # Save the cross table.
    pq.write_table(uac_cross_tbl, "data/out/uac_pairs_gravity.parquet")


def places():
    # Load urban areas from shapefile
    place_tbl = get_population_table(
        Path("data/tl_2020/PLACE").glob("tl_2020_*_place.zip"),
        Path("data/census/DECENNIALDHC2020.P1-Data_PLACE.csv"),
        "1600000US",
    )

    # Save the places area table for later.
    pq.write_table(place_tbl, "data/out/place_populations.parquet")

    # do the cross join
    place_cross_tbl = self_cross_join(
        place_tbl.select(["NODE_ID", "POP20", "INTPTLAT", "INTPTLON"])
    )

    # Filter out self match and second matches
    place_cross_tbl = place_cross_tbl.filter(
        pc.field("NODE_ID_U") < pc.field("NODE_ID_V")
    )

    print(place_cross_tbl)
    pq.write_table(place_cross_tbl, "data/out/place_cross_tbl.parquet")
    return

    place_cross_tbl = calculate_distances(place_cross_tbl)
    place_cross_tbl = calculate_gravity(place_cross_tbl)

    print(place_cross_tbl)
    # Save the cross table.


def calculate_distance(ctx, lat_u, lon_u, lat_v, lon_v):
    geod = Geod(ellps="WGS84")

    az_uv, az_vu, distance = geod.inv(
        lon_u,
        lat_u,
        lon_v,
        lat_v,
    )
    return pa.array(distance / 1000)

in_types = {
    "lat_u": pa.float64(),
    "lon_u": pa.float64(),
    "lat_v": pa.float64(),
    "lon_v": pa.float64(),
}
out_type = pa.float64()

func_name = "calculate_distance"
func_doc = {
    "summary": "Calculate distance between two points",
    "description": "This function calculates the distance between two sets of lat/lon cordinates",
}
pc.register_scalar_function(calculate_distance, func_name, func_doc, in_types, out_type)


def places_calcs():
    place_cross_tbl = pq.read_table("data/out/place_cross_tbl.parquet")

    R = 6371

    lat1 = place_cross_tbl["INTPTLAT_U"]
    lon1 = place_cross_tbl["INTPTLON_U"]
    lat2 = place_cross_tbl["INTPTLAT_V"]
    lon2 = place_cross_tbl["INTPTLON_V"]

    distance = pc.multiply(
        pa.scalar(2 * R),
        pc.sqrt(
            pc.add(
                pc.power(
                    pc.sin(pc.divide(pc.subtract(lat2, lat1), pa.scalar(2))),
                    pa.scalar(2),
                ),
                pc.multiply(
                    pc.multiply(pc.cos(lat1), pc.cos(lat2)),
                    pc.power(
                        pc.sin(pc.divide(pc.subtract(lon2, lon1), pa.scalar(2))),
                        pa.scalar(2),
                    ),
                ),
            )
        ),
    )

    print(distance)

    gravity = pc.divide(
        pc.multiply(place_cross_tbl["POP20_U"], place_cross_tbl["POP20_V"]),
        pc.power(distance, pa.scalar(2)),
    )

    print(gravity)

    place_cross_tbl = place_cross_tbl.append_column("DISTANCE", distance)
    place_cross_tbl = place_cross_tbl.append_column("GRAVITY", gravity)

    print(place_cross_tbl)
    pq.write_table(place_cross_tbl, "data/out/place_cross_tbl_gravity.parquet")


def main():
    places_calcs()


if __name__ == "__main__":
    main()
