pacman::p_load(terra, fs, sf, tidyverse, rayshader, magick)

SRTM_HGT = fs::path("/Volumes/TheTank/datasets/SRTM_HGT")

files = tibble(
        path = fs::dir_ls(SRTM_HGT)
    ) |>
    mutate(
        cord = str_match(path, "(?<latdir>N|S)(?<lat>\\d+)(?<londir>W|E)(?<lon>\\d+)") |>
            magrittr::set_colnames(c("location","latdir","lat","londir","lon")) |>
            as_tibble()
    ) |>
    unnest(cord) |>
    mutate(
        lat = as.integer(lat),
        lon = as.integer(lon)
    ) |>
    filter() |>
    arrange(lon, lat)

elevation_collection = files$path |>
    map(\(x) terra::rast(x)) |>
    sprc()

elevation_merged = terra::merge(elevation_collection, algo=3)

mry = list(terra::rast(path(SRTM_HGT, "N36W122.SRTMGL1.hgt.zip")),
           terra::rast(path(SRTM_HGT, "N37W122.SRTMGL1.hgt.zip")),
           terra::rast(path(SRTM_HGT, "N36W121.SRTMGL1.hgt.zip")),
           terra::rast(path(SRTM_HGT, "N37W121.SRTMGL1.hgt.zip"))) |>
    sprc() |>
    merge(algo = 3)


# -124.41060660766607,32.5342307609976,-114.13445790587905,42.00965914828148
california = rast(
    xmin = -124.41060660766607,
    ymin = 32.5342307609976,
    xmax = -114.13445790587905,
    ymax = 42.00965914828148
)


elevation_ca_cropped = crop(elevation_merged, california)
scale_factor = sqrt(size(elevation_ca_cropped) / 3200000)
elevation_ca = aggregate(elevation_ca_cropped, fact = scale_factor, fun="mean")
size(elevation_ca)

temp_filename = "../../datasets_nobak/data_tmp_out/elevation.tif"
terra::writeRaster(elevation_ca, temp_filename, overwrite=TRUE)


pl
ca_matrix = raster_to_matrix(temp_filename)
size(elevation_ca)

plot(elevation_ca)


ca_height_shade = height_shade(ca_matrix)
ca_sphere_shade = sphere_shade(
    ca_matrix,
    texture = "bw",
    zscale = 4,
    colorintensity = 5
)
ca_lamb_shade = lamb_shade(ca_matrix, zscale = 6)
ca_ambient_shade = ambient_shade(ca_matrix)
ca_texture_shade = texture_shade(
    ca_matrix,
    detail = 8 / 10,
    contrast = 9,
    brightness = 11
)



ca_height_shade %>%
    #add_overlay(mry_sphere_shade, alphalayer = 0.5) %>%
    #add_shadow(mry_lamb_shade, 0) %>%
    #add_shadow(mry_ambient_shade, 0) %>%
    #add_shadow(mry_texture_shade, 0.1) %>%
    plot_map()


ca_sphere_shade |> add_shadow(ca_texture_shade) |> plot_map()
