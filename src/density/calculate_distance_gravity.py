from pathlib import Path

import geoarrow as ga  # noqa: F401
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import pyogrio
from pyarrow import csv
from pyproj import Geod


def main():
    # Load urban areas from shapefile
    uac_file = Path("data/tl_2020/UAC/tl_2020_us_uac20_corrected.zip").absolute()
    _, uac_tbl = pyogrio.read_arrow(uac_file)

    # Load and join in population numbers
    convert_options = csv.ConvertOptions(
        include_columns=["GEOIDFQ20", "POP20"],
        column_types={
            "GEOIDFQ20": pa.string(),
            "NAME": pa.string(),
            "POP20": pa.int64(),
        },
    )

    uac_populations_tbl = csv.read_csv(
        "data/census/DECENNIALDHC2020.P1-Data_UAC.csv",
        convert_options=convert_options,
    )

    uac_tbl = uac_tbl.join(uac_populations_tbl, keys="GEOIDFQ20")

    # Convert Lat/Lon to floats
    lat_casted = pc.cast(uac_tbl.column("INTPTLAT20"), pa.float64())
    lon_casted = pc.cast(uac_tbl.column("INTPTLON20"), pa.float64())

    uac_tbl = uac_tbl.set_column(
        uac_tbl.column_names.index("INTPTLAT20"), "INTPTLAT20", lat_casted
    ).set_column(uac_tbl.column_names.index("INTPTLON20"), "INTPTLON20", lon_casted)

    # Add a numeric ID to the table
    rec_count = len(uac_tbl)
    id_arr = pa.array(range(rec_count), type=pa.int64())
    uac_tbl = uac_tbl.add_column(0, "NODE_ID", id_arr)

    # Save the urban area table for later.
    pq.write_table(uac_tbl, "data/out/uac_populations.parquet")

    # Setup uv cross join urban areas
    uac_u_tbl = (
        uac_tbl.select(["NODE_ID", "POP20", "INTPTLAT20", "INTPTLON20"])
        .rename_columns(
            {
                "NODE_ID": "NODE_ID_U",
                "POP20": "POP_U",
                "INTPTLAT20": "LAT_U",
                "INTPTLON20": "LON_U",
            }
        )
        .add_column(0, "dummy_key", [[1] * len(uac_tbl)])
    )

    uac_v_tbl = (
        uac_tbl.select(["NODE_ID", "POP20", "INTPTLAT20", "INTPTLON20"])
        .rename_columns(
            {
                "NODE_ID": "NODE_ID_V",
                "POP20": "POP_V",
                "INTPTLAT20": "LAT_V",
                "INTPTLON20": "LON_V",
            }
        )
        .add_column(0, "dummy_key", [[1] * len(uac_tbl)])
    )

    # Do cross join and only keep one set of pairs
    uac_cross_tbl = (
        uac_u_tbl.join(uac_v_tbl, keys="dummy_key")
        .drop_columns(["dummy_key"])
        .filter(pc.field("NODE_ID_U") < pc.field("NODE_ID_V"))
    )

    lat_u = uac_cross_tbl["LAT_U"].to_numpy()
    lon_u = uac_cross_tbl["LON_U"].to_numpy()
    lat_v = uac_cross_tbl["LAT_V"].to_numpy()
    lon_v = uac_cross_tbl["LON_V"].to_numpy()

    geod = Geod(ellps="WGS84")

    az_uv, az_vu, distance = geod.inv(
        lon_u,
        lat_u,
        lon_v,
        lat_v,
    )

    uac_cross_tbl = (
        uac_cross_tbl.append_column("AZ_UV", pa.array(az_uv))
        .append_column("AZ_VU", pa.array(az_vu))
        .append_column("DISTANCE", pa.array(distance / 1000))
    )

    gravity = pc.divide(
        pc.multiply(uac_cross_tbl["POP_U"], uac_cross_tbl["POP_V"]),
        pc.power(uac_cross_tbl["DISTANCE"], 2),
    )

    uac_cross_tbl = uac_cross_tbl.append_column("GRAVITY", gravity)

    print(uac_cross_tbl)
    # Save the urban area table for later.
    pq.write_table(uac_cross_tbl, "data/out/uac_pairs_gravity.parquet")


if __name__ == "__main__":
    main()
