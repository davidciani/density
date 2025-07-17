import re
import shutil
import subprocess
from pathlib import Path


def main():
    for zip_file in sorted(Path("data_tmp_tiger/no_import/FACES").glob("*.zip")):
        m = re.match(r".*_(.*)\.zip", zip_file.name)
        file_stem = m.group(1)
        print((zip_file.name, file_stem))

        temp_file = Path(shutil.copy(zip_file, "temp.shp.zip"))

        subprocess.run(
            [
                "ogr2ogr",
                "-append",
                "-nln",
                f"tiger_2020_{file_stem}",
                "-nlt",
                "PROMOTE_TO_MULTI",
                "-lco",
                "GEOMETRY_NAME=geom",
                "-lco",
                "FID=gid",
                "-lco",
                "PRECISION=NO",
                "PG:dbname=census host=localhost user=david",
                str(temp_file),
            ]
        )
        temp_file.unlink()


"""
ADDR
ADDRFEAT
ADDRFN
AIANNH
AITSN
ANRC
AREALM
AREAWATER
BG
CBSA
CD
CNECTA
COASTLINE
CONCITY
COUNTY
COUSUB
CSA
EDGES
ELSD
ESTATE
FACES
FACESAH
FACESAL
FACESMIL
FEATNAMES
LINEARWATER
METDIV
MIL
NECTA
NECTADIV
PLACE
POINTLM
PRIMARYROADS
PRISECROADS
PUMA20
RAILS
ROADS
SCSD
SLDL
SLDU
STATE
SUBBARRIO
TABBLOCK20
TBG
TRACT
TTRACT
UAC
UNSD
ZCTA520
"""
if __name__ == "__main__":
    main()
