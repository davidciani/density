pacman::p_load("tidyverse", "arrow", "sf","units")


uac20_points = sf::read_sf("../data_tmp_out/uac20_points.gpkg")

uac20_distance_matrix = st_distance(uac20_points,uac20_points) |> set_units("km")

colnames(uac20_distance_matrix) = uac20_points$GEOID20
rownames(uac20_distance_matrix) = cities$name 
uac20_points |> rlang::set_names()
uac20_points_distance
