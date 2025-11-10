import numpy as np
import rasterio


def hillshade(array, azimuth, angle_altitude):
    """Calculates the hillshade of a DEM.

    Args:
        array (numpy.ndarray): A 2D numpy array representing the DEM.
        azimuth (float): The azimuth angle of the light source in degrees.
        angle_altitude (float): The altitude angle of the light source in degrees.

    Returns:
        numpy.ndarray: A 2D numpy array representing the hillshade.
    """
    x, y = np.gradient(array)
    slope = np.pi / 2.0 - np.arctan(np.sqrt(x * x + y * y))
    aspect = np.arctan2(-y, x)
    azimuth_rad = azimuth * np.pi / 180.0
    altitude_rad = angle_altitude * np.pi / 180.0

    shaded = np.sin(altitude_rad) * np.sin(slope) + np.cos(altitude_rad) * np.cos(
        slope
    ) * np.cos(azimuth_rad - aspect)
    return 255 * (shaded + 1) / 2


# Open the DEM file
with rasterio.open("/Volumes/TheTank/datasets/SRTM_HGT/N36W122.SRTMGL1.hgt.zip") as src:
    dem = src.read(1)
    profile = src.profile

# Define the light source parameters
azimuth = 310  # Azimuth angle in degrees
angle_altitude = 45  # Altitude angle in degrees

# Calculate the hillshade
hillshade_array = hillshade(dem, azimuth, angle_altitude)

# Update the profile for the hillshade
profile.update({"driver": "GTiff", "dtype": rasterio.uint8, "count": 1, "nodata": 0})

# Save the hillshade to a new file
with rasterio.open("data/out/hillshade.tif", "w", **profile) as dst:
    dst.write(hillshade_array, 1)
