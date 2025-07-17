library(tidyverse)
library(fs)
library(units)

install_unit("people")

DATA_DIR = path("~/data_projects/datasets-nobackup")

specs = list()


specs$dhc_geo = cols(
    FILEID = col_factor(),
    STUSAB = col_factor(),
    SUMLEV = col_factor(),
    GEOVAR = col_factor(),
    GEOCOMP = col_factor(),
    CHARITER = col_factor(),
    CIFSN = col_factor(),
    LOGRECNO = col_number(),
    GEOID = col_character(),
    GEOCODE = col_character(),
    REGION = col_factor(),
    DIVISION = col_factor(),
    STATE = col_factor(),
    STATENS = col_factor(),
    COUNTY = col_factor(),
    COUNTYCC = col_factor(),
    COUNTYNS = col_factor(),
    COUSUB = col_factor(),
    COUSUBCC = col_factor(),
    COUSUBNS = col_factor(),
    SUBMCD = col_factor(),
    SUBMCDCC = col_factor(),
    SUBMCDNS = col_factor(),
    ESTATE = col_factor(),
    ESTATECC = col_factor(),
    ESTATENS = col_factor(),
    CONCIT = col_factor(),
    CONCITCC = col_factor(),
    CONCITNS = col_factor(),
    PLACE = col_factor(),
    PLACECC = col_factor(),
    PLACENS = col_factor(),
    TRACT = col_factor(),
    BLKGRP = col_factor(),
    BLOCK = col_factor(),
    AIANHH = col_factor(),
    AIHHTLI = col_factor(),
    AIANHHFP = col_factor(),
    AIANHHCC = col_factor(),
    AIANHHNS = col_factor(),
    AITS = col_factor(),
    AITSFP = col_factor(),
    AITSCC = col_factor(),
    AITSNS = col_factor(),
    TTRACT = col_factor(),
    TBLKGRP = col_factor(),
    ANRC = col_factor(),
    ANRCCC = col_factor(),
    ANRCNS = col_factor(),
    CBSA = col_factor(),
    MEMI = col_factor(),
    CSA = col_factor(),
    METDIV = col_factor(),
    NECTA = col_factor(),
    NMEMI = col_factor(),
    CNECTA = col_factor(),
    NECTADIV = col_factor(),
    CBSAPCI = col_factor(),
    NECTAPCI = col_factor(),
    UA = col_factor(),
    UATYPE = col_factor(),
    UR = col_factor(),
    CD116 = col_factor(),
    CD118 = col_factor(),
    CD119 = col_factor(),
    CD120 = col_factor(),
    CD121 = col_factor(),
    SLDU18 = col_factor(),
    SLDU22 = col_factor(),
    SLDU24 = col_factor(),
    SLDU26 = col_factor(),
    SLDU28 = col_factor(),
    SLDL18 = col_factor(),
    SLDL22 = col_factor(),
    SLDL24 = col_factor(),
    SLDL26 = col_factor(),
    SLDL28 = col_factor(),
    VTD = col_factor(),
    VTDI = col_factor(),
    ZCTA = col_factor(),
    SDELM = col_factor(),
    SDSEC = col_factor(),
    SDUNI = col_factor(),
    PUMA = col_factor(),
    AREALAND = col_number(),
    AREAWATR = col_number(),
    BASENAME = col_character(),
    NAME = col_character(),
    FUNCSTAT = col_factor(),
    GCUNI = col_factor(),
    POP100 = col_number(),
    HU100 = col_number(),
    INTPTLAT = col_character(),
    INTPTLON = col_character(),
    LSADC = col_factor(),
    PARTFLAG = col_factor(),
    UGA = col_factor()
)

dhc_geo_files = dir_ls(path(DATA_DIR, "census2020", "dhc"), glob = "*.dhc.zip") |>
    map(function(zip_path) {
        unzip(zip_path, list = TRUE)
    }) |>
    list_rbind(names_to = "zip_path") |>
    filter(str_detect(Name, "geo"))

dhc_geo = dhc_geo_files |>
    mutate(data = map2(zip_path, Name, function(zip_path, file_name) {
        rlang::inform(sprintf("Reading file `%s`", file_name))
        
        read_delim(
            unz(zip_path, file_name),
            delim = "|",
            col_names = names(specs$dhc_geo$cols),
            col_types = specs$dhc_geo
        )
    })) |>
    select(data) |>
    unnest_longer(data) |>
    unpack(data) |>
    mutate(
        AREALAND = set_units(AREALAND, m ^ 2),
        AREAWATR = set_units(AREAWATR, m ^ 2),
        POP100 = set_units(POP100, people),
        HU100 = set_units(HU100, people),
    )


dhc_geo |> write_rds(path(DATA_DIR, "census2020", "dhc_geo.rds"))
