pacman::p_load("tidyverse", "sf","units")

GPKG = "../../datasets_nobak/natural_earth/natural_earth_vector.gpkg/packages/natural_earth_vector.gpkg"

st_layers(GPKG)

usa_states = read_sf(GPKG, layer="ne_10m_admin_1_states_provinces_lakes") |> 
    filter(adm0_a3 == "USA")

lower_48 = usa_states |> 
    filter(name != "Alaska", name != "Hawaii") |> 
    st_transform(4269)



pop = read_csv("../data_census/DECENNIALDHC2020.P1-Data.csv")

uac20_points = sf::read_sf("../data_tmp_out/uac20_points.gpkg") |> 
    left_join(pop |> select(GEOID, POP20), by=c("GEOIDFQ20"="GEOID")) |>
    st_filter(lower_48, .predicate=st_within)


uac20_points |> select(-INTPTLAT20, -INTPTLON20) |> mutate(geom = st_as_text(geom)) |> write_csv("../data_tmp_out/uac20_points.csv")

# ------------------------------------------------------------------------------
pairs = uac20_points |>
    cross_join(uac20_points, suffix = c("_from","_to")) |>
    filter(GEOID20_from != GEOID20_to, POP20_from > POP20_to | (POP20_from == POP20_to & NAME20_from < NAME20_to))

uac20_distance_matrix = st_distance(uac20_points,uac20_points) |> set_units("km")
colnames(uac20_distance_matrix) = uac20_points$GEOID20
rownames(uac20_distance_matrix) = uac20_points$GEOID20 



ua_edges = uac20_distance_matrix |>
    as_tibble() |>
    mutate(from = uac20_points$GEOID20) |>
    pivot_longer(cols = -from,
                 names_to = "to",
                 values_to = "distance") |>
    left_join(uac20_points |> select(
        from = GEOID20,
        name_from = NAME20,
        pop_from = POP20
    ),
    by = join_by(from)) |>
    left_join(uac20_points |> select(
        to = GEOID20,
        name_to = NAME20,
        pop_to = POP20
    ),
    by = join_by(to)) |>
    filter(from != to, pop_to > pop_from |
               (pop_to == pop_from & from < to)) |>
    mutate(
        gravity = (pop_from * pop_to) / distance^2,
        geom.line = st_union(geom.x, geom.y, by_feature = TRUE) |>
            st_cast("LINESTRING")
        )



ggplot() +
    geom_sf(data=lower_48) +
    geom_sf(data=ua_edges, aes(geometry = geom.line), linewidth = 0.01)
