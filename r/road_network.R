pacman::p_load("tidyverse", "sf","fs", "sfnetworks","tidygraph", "spdep")

pri_sec_roads_dir = path_wd("../../datasets_nobak/data_tmp_tiger/import/PRISECROADS/") |> 
    path_norm()

us_bbox = st_bbox(c(
    xmin = 24.0,
    xmax = 49.5,
    ymax = -125,
    ymin = -67
), crs = st_crs(4269)) |>
    st_as_sfc() |>
    st_make_valid()

pri_sec_roads = dir_ls(pri_sec_roads_dir) |> 
    map(\(x) read_sf(paste0("/vsizip/",x))) |> 
    list_rbind() |> 
    st_sf() |> 
    st_cast("LINESTRING") |> 
    st_make_valid()

pri_sec_roads_filtered = pri_sec_roads |>
    st_filter(us_bbox, .predicate = st_covered_by)

rounded_geom = st_geometry(pri_sec_roads_filtered) |> 
    lapply(function(x) round(x, 2)) |> 
    st_sfc(crs = st_crs(pri_sec_roads_filtered))

pri_sec_roads_rounded = pri_sec_roads_filtered |> 
    st_set_geometry(rounded_geom)


net = as_sfnetwork(pri_sec_roads_rounded)

simple_net = net |> 
    activate("edges") |> 
    filter(!edge_is_multiple()) |> 
    filter(!edge_is_loop())

plot(simple_net)
