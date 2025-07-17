pacman::p_load(
    terra,
    elevatr,
    sf,
    geodata,
    tidyverse,
    rayshader,
    magick
)

# 2. COUNTRY BORDERS
#-------------------

path <- getwd()

country_sf <- geodata::gadm(
    country = "USA",
    level = 1,
    path = path
) |>
    sf::st_as_sf()

conus_sf = country_sf |> 
    filter(!(ISO_1 %in% c("US-AK","US-HI"))) |>
    st_union()

plot(sf::st_geometry(conus_sf))

# 4. LOAD RIVERS
#---------------

filename = "HydroRIVERS_v10_na_shp/HydroRIVERS_v10_na.shp"

country_bbox <- sf::st_bbox(conus_sf)
# xmin       ymin       xmax       ymax 
# -124.76278   24.52042  -66.94889   49.38330 

# -122.0001, -120.9999, 35.99986, 37.00014  (xmin, xmax, ymin, ymax)

bbox_wkt = "POLYGON((
    -122.0001 35.99986,
    -122.0001 37.00014,
    -120.9999 37.00014,
    -120.9999 35.99986,
    -122.0001 35.99986
))"


bbox_wkt <- "POLYGON((
    -124.76278 24.52042,
    -124.76278 49.38330,
    -66.94889 49.38330,
    -66.94889 24.52042,
    -124.76278 24.52042
))"

country_rivers <- sf::st_read(
    filename,
    wkt_filter = bbox_wkt
) |>
    sf::st_intersection(
        conus_sf
    )

plot(sf::st_geometry(country_rivers))


# 5. RIVER WIDTH
#---------------

sort(
    unique(
        country_rivers$ORD_FLOW
    )
)

#EPSG:5070 NAD83 / Conus Albers
crs_country <- "+proj=aea +lat_0=23 +lon_0=-96 +lat_1=29.5 +lat_2=45.5 +x_0=0 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs +type=crs"

country_river_width <- country_rivers |>
    dplyr::mutate(
        width = as.numeric(
            ORD_FLOW
        ),
        width = dplyr::case_when(
            width == 2 ~ 18, 
            width == 3 ~ 16, 
            width == 4 ~ 14,
            width == 5 ~ 12,
            width == 6 ~ 10,
            width == 7 ~ 8,
            width == 8 ~ 6,
            width == 9 ~ 4,
            width == 10 ~ 2,
            TRUE ~ 0
        )
    ) |>
    sf::st_as_sf() |>
    sf::st_transform(crs = crs_country)

# 6. DEM
#-------

dem <- elevatr::get_elev_raster(
    locations = country_sf,
    z = 3, clip = "locations"
)

dem_single = terra::rast("/Volumes/TheTank/datasets/SRTM/n36_w122_1arc_v3.tif")


dem_country <- dem_single |>
    terra::crop(conus_sf) |> 
    terra::project(crs_country)

dem_matrix <- rayshader::raster_to_matrix(
    dem_country
)

# 7. RENDER SCENE
#----------------

dem_matrix |>
    rayshader::height_shade(
        texture = colorRampPalette(
            c(
                "#fcc69f",
                "#c67847"
            )
        )(128)
    ) |>
    rayshader::add_overlay(
        rayshader::generate_line_overlay(
            geometry = country_river_width,
            extent = dem_country,
            heightmap = dem_matrix,
            color = "#387B9C",
            linewidth = country_river_width$width,
            data_column_width = "width"
        ), alphalayer = 1
    ) |>
    rayshader::plot_3d(
        dem_matrix,
        zscale = 20,
        solid = FALSE,
        shadow = TRUE,
        shadow_darkness = 1,
        background = "white",
        windowsize = c(600, 600),
        zoom = .5,
        phi = 89,
        theta = 0
    )


rayshader::render_camera(
    zoom = .75
)

# 8. RENDER OBJECT
#-----------------

u <- "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/4k/photo_studio_loft_hall_4k.hdr"
hdri_file <- basename(u)

download.file(
    url = u,
    destfile = hdri_file,
    mode = "wb"
)

file_name <- "usa-3d-elevation-rivers.png"

rayshader::render_highquality(
    filename = file_name,
    preview = TRUE,
    light = FALSE,
    environment_light = hdri_file,
    intensity_env = 1,
    interactive = FALSE,
    width = 3000,
    height = 3000
)
