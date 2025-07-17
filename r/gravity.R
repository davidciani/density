pacman::p_load("tidyverse", "sf", "units")


pop = read_csv("../data_census/DECENNIALDHC2020.P1-Data.csv")

uac20_points = sf::read_sf("../data_tmp_out/uac20_points.gpkg") |> 
    left_join(pop |> select(GEOID, POP20), by=c("GEOIDFQ20"="GEOID"))

uac20_distance_matrix = st_distance(uac20_points,uac20_points) |> set_units("km")

colnames(uac20_distance_matrix) = uac20_points$GEOID20
rownames(uac20_distance_matrix) = uac20_points$GEOID20 

ua_edges = uac20_distance_matrix |>
    as_tibble() |>
    mutate(from=uac20_points$GEOID20) |> 
    pivot_longer(cols=-from, names_to="to", values_to = "distance") |> 
    left_join(uac20_points |> select(from=GEOID20, name_from=NAME20, pop_from=POP20), by = join_by(from)) |> 
    left_join(uac20_points |> select(to=GEOID20, name_to=NAME20, pop_to=POP20), by = join_by(to)) |> 
    filter(from != to, pop_to > pop_from | (pop_to == pop_from & from < to)) |> 
    mutate(gravity = (pop_from * pop_to)/distance^2)



ua_in_range_edges = ua_edges |> 
    filter(distance > set_units(75, km), distance < set_units(1000, km)) |> 
    mutate(geom.line = st_union(geom.x, geom.y, by_feature = TRUE) |> st_cast("LINESTRING"))


uac_inrange_nodes = uac20_points |>
    filter(GEOID20 %in% ua_in_range_edges$from | GEOID20 %in% ua_in_range_edges$to)
    

ua_in_range_edges |> 
    st_set_geometry("geom.line") |> 
    write_sf("../data_tmp_out/uac20_inrange_lines.gpkg", layer = "uac20_inrange_lines.gpkg")









