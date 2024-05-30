# given a csv file and a directory, assign exif data to all images in a given
# directory. we can assume the images in the directories are labelled
# sequentially.
# 
# the program checks if exiftool is installed, and if not, it will prompt the
# user to install it.
# 
# the csv file should be formatted as follows (header included):
# Shot #, SS or exposure time, Aperture, Focal length, Date, Location,
# Longitude, Latitude
# 
# note that date is in string format, and location is in string format.
# 
# the program uses argparse to take in the csv file and the directory as
# arguments.
# 

import argparse
import csv
import os
import datetime
import sys
from pathlib import Path
from enum import Enum

# argparse
parser = argparse.ArgumentParser()
parser.add_argument("csv_file", help="path to csv file")
parser.add_argument("directory", help="path to directory")
parser.add_argument("camera", choices=['canonet', 'fm10'], help="camera model")

# csv enum
class CSV(Enum):
    SHOT = 0
    EXP_TIME = 1
    APERTURE = 2
    FOCAL_LENGTH = 3
    LENS = 4
    LENS_MODEL = 5
    FILM = 6
    ISO = 7
    FORMAT = 8
    DATE = 9
    LOCATION = 10
    LATITUDE = 11
    LONGITUDE = 12
    NOTES = 13
    STARS = 14

def check_exiftool() -> bool:
    """check if exiftool is installed"""
    if os.system("exiftool -ver") == 0:
        print("exiftool is installed.")
        return True
    else:
        return False
    
def get_images(directory: Path) -> list:
    """get all images in a directory"""
    images = []
    for file in directory.iterdir():
        if file.suffix == ".jpg":
            images.append(file)

    # images.sort(key=lambda x: int(x.stem))
    try:
        images.sort(key=lambda x: int(x.stem.split("-")[-1]))
    except ValueError:
        images.sort()

    for image in images:
        print(image)
    return images

def get_exif_data(csv_file: Path, has_header=True) -> list:
    """get exif data from csv file"""
    exif_data = []
    with open(csv_file, newline="") as csvfile:
        reader = csv.reader(csvfile)
        if has_header:
            next(reader, None)
        for row in reader:
            if row:
                exif_data.append(row)
    
    return exif_data

def check_match(images, exif_data) -> bool:
    """check if number of images and number of exif data match"""
    # first get a list of shot #s
    # for row in exif_data:
    #     print(row)

    # for image in images:
    #     print(image)

    if len(images) != len(exif_data):
        print("number of images and number of exif data do not match.")
        return False
        
    return True

def ss_to_float(ss: str) -> float:
    """convert shutter speed (either in the format of 1/Ks or K") to float"""
    if ss == '-':
        return ''

    if ss.endswith('s'):
        return 1 / float(ss[2:-1])
    else:
        return float(ss[:-2])

def main():
    args = parser.parse_args()
    csv_file = Path(args.csv_file)
    directory = Path(args.directory)
    
    # check if exiftool is installed
    if not check_exiftool():
        print("exiftool is not installed. please install it before proceeding.")
        return
    
    # get images
    images = get_images(directory)
    
    # get exif data
    exif_data = get_exif_data(csv_file)
    
    # assign exif data to images
    if not check_match(images, exif_data):
        return
    
    for image, row in zip(images, exif_data):
        shot_num = row[CSV.SHOT.value]
        ss = row[CSV.EXP_TIME.value]
        aperture = row[CSV.APERTURE.value]
        focal_length = row[CSV.FOCAL_LENGTH.value]
        lens = row[CSV.LENS.value]
        lens_model = row[CSV.LENS_MODEL.value]
        film = row[CSV.FILM.value]
        iso = row[CSV.ISO.value]
        film_format = row[CSV.FORMAT.value]
        date = row[CSV.DATE.value]
        location = row[CSV.LOCATION.value]
        latitude = row[CSV.LATITUDE.value]
        longitude = row[CSV.LONGITUDE.value]


        # ss or exposure time must be in float (seconds)
        try:
            ss = ss_to_float(ss)
        except ValueError:
            ss = ''

        # try to convert aperture to float
        try:
            if aperture.startswith("f:"):
                aperture = aperture[2:]
            aperture = float(aperture)
        except ValueError:
            aperture = ''

        # convert date to exif format
        # csv date is in the format of "Dec 13, 2023 at 13:36"
        # exif date is in the format of "2023:12:13 13:36:00"
        date = datetime.datetime.strptime(date, "%b %d, %Y at %H:%M").strftime("%Y:%m:%d %H:%M:%S")

        # longitude and latitude
        if longitude and latitude:
            gps_data = f'-GPSLongitudeRef="W" -GPSLongitude="{longitude}" -GPSLatitudeRef="N" -GPSLatitude="{latitude}" -GPSAltitudeRef="Above Sea Level" -GPSAltitude="0"'
        else:
            gps_data = ""

        # Other exif data
        # print(f'{image} {date} {location} {longitude} {latitude} {ss} {aperture} {focal_length} {iso}')

        ss_cmd = f'-ExposureTime="{ss}" ' if ss else ''
        aperture_cmd = f'-FNumber="{aperture}" ' if aperture else ''

        camera_info = ''
        if args.camera == 'canonet':
            camera_info = f'-Make="Canon" -Model="Canon Canonet QL17 Giii" -LensMake="Canon"'
        elif args.camera == 'fm10':
            camera_info = f'-Make="Nikon" -Model="Nikon FM10" -LensMake="Nikon"'

        # assign exif data
        os.system(
            f'exiftool -overwrite_original '
            f'-AllDates="{date}" '
            f'{gps_data}'
            f'-ImageDescription="{location}" '
            f'-Artist="Muchen He" '
            # f'-ImageUniqueID="{shot_num}" '
            f'{ss_cmd} {aperture_cmd}'
            f'-FocalLength="{focal_length}" -FocalLengthIn35mmFormat="{focal_length}" '
            f'{camera_info} '
            f'-LensModel="{lens_model}" '

            f'-ISO="{iso}" '
            f'{image}'
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("program terminated by user.")
        sys.exit()
    except Exception as e:
        print(e)
