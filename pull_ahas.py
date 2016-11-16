"""
pull_ahas.py
Python Version 2.7

An automated procedure for extracting and georeferencing raster BAM files from AHAS and converting them to an Esri ArcGIS consumable format.

AHAS: The Avian Hazard Advisory System (AHAS) was constructed with the best available geospatial bird data to reduce the risk of bird collisions with aircraft. Its use for flight planning can reduce the likelihood of a bird collision but will not eliminate the risk. The AHAS organizations are not liable for losses incurred as a result of bird strikes.

BAM: The United States Air Force has developed a Bird Avoidance Model (BAM) using Geographic Information System (GIS) technology as a key tool for analysis and correlation of bird habitat, migration, and breeding characteristics, combined with key environmental, and man-made geospatial data.

Requirements:
    -Standalone Python script.
    -Python version 2.7
    -This script requires the use of ArcGIS 10.1 or greater.
    -See requirements.txt for full list of required python modules
    -Be aware that this script accesses a public facing DOD information system that is under DOD surveillance.  Travel to the website manually first if you are interested in seeing the disclaimer discussing this surveillance.
        http://www.usahas.com/
"""
__author__ = "Chaz Mateer"
__credits__ = ["Chaz Mateer", "USAHAS"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Chaz Mateer"
__email__ = "chaz.mateer@gmail.com"
__status__ = "Production"

# Import modules
# System modules
import os
import sys
import urllib
import zipfile

# Third party modules
import arcpy
from bs4 import BeautifulSoup

# Download and write file
def download_file(download_url, file_name):
    """
    Attempts to download a file from the given URL and save it to a specified file location.  If the procedure fails, the script will throw an error message and exit.

    Arguements:
        download_url
            The URL for the file you would like to donwload.

        file_name
            The path of the output file where the download will be saved.
    """
    try:
        print "Downloading {0}...".format(download_url)
        urllib.urlretrieve(download_url, file_name)
        print "Sucessfully downloaded and saved to {0}".format(file_name)
    except Exception as e:
        abort("Download and write procedure failed!\n", e)

# Unzip
def unzip(in_file, out_file):
    """Unzip a zip file and output to a folder."""
    try:
        print "Unzipping {0}".format(in_file)
        with zipfile.ZipFile(in_file, 'r') as zip_ref:
            zip_ref.extractall(out_file)
        print "Successfully unzipped to {0}".format(out_file)
    except Exception as e:
        abort("Unzip procedure failed!\n", e)

# Extract image URL from KML
def extract_kml_image(kml_file, output_folder):
    """
    TODO - assumes that the format of the BAM KMLs doesn't change.

    Edit later to output error instead of exiting on failure.
    """
    try:
        print "Extracting information from {0}".format(kml_file)
        with open(kml_file, 'r') as k:
            # Make soup
            soup = BeautifulSoup(k, "html.parser")

            # Get image url from KML
            image_url = soup.kml.groundoverlay.icon.href.contents[0]

            # Get human readable name from KML
            image_name = soup.find_all("name")[0].string

            # Create output path
            image_output = os.path.join(output_folder, image_name + ".png")

            # Attempt download
            download_file(image_url, image_output)
    except Exception as e:
        abort("KML extraction failed!\n", e)

# Warp
def warp(input_image, output_gdb):
    """Georeference the input raster by a predetermined extent."""
    try:
        # Set output workspace
        arcpy.env.workspace = output_gdb

        # Output raster
        output_raster = os.path.basename(input_image.replace("-", "_").replace(" ", "_").replace(".png", ""))

        # Predefined extents
        src_pnt = "'-0.5  0.5';'4330.5 0.5';'-0.5 -1796.5';'4330.5 -1796.5'"
        tar_pnt = "'-179.77501667257 71.7596743910802';'-65.5369154883902 71.7596743910802';'-179.77501667257 24.3665227454068';'-65.5369154883902 24.3665227454068'"

        # Run warp
        arcpy.Warp_management(input_image, src_pnt, tar_pnt, output_raster)

        # Define SRS
        srs = arcpy.SpatialReference("WGS 1984")
        arcpy.DefineProjection_management(output_raster, srs)
    except Exception as e:
        abort("Warp procedure failed!\n", e)

# Abort message
def abort(message, error_code):
    """Print message and error code to console and exit the program."""
    print message, error_code
    sys.exit()

# Main method
if __name__ == '__main__':
    """Main execution procedure."""
    # Local variables
    dir_path = os.path.dirname(os.path.realpath(__file__))
    ahas_url = "http://www.usahas.com/Downloads/GE_BAM.zip"
    ahas_zip = os.path.join(dir_path, r"working\GE_BAM.zip")
    kml_folder = os.path.join(dir_path, r"working\kmls")
    images_folder = os.path.join(dir_path, r"working\images")
    output_gdb = os.path.join(dir_path, r"working\BAM.gdb")

    # Download BAM from AHAS
    download_file(ahas_url, ahas_zip)

    # Unzip BAM data
    unzip(ahas_zip, kml_folder)

    # Extract KMLs
    for kml in os.listdir(kml_folder):
        print kml
        extract_kml_image(os.path.join(kml_folder, kml), images_folder)

    # Warp and send to GDB
    for image in os.listdir(images_folder):
        print image
        warp(os.path.join(images_folder, image), output_gdb)
