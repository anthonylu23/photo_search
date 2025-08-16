from PIL import Image, ExifTags
from PIL.ExifTags import TAGS, GPSTAGS
import os
from img_loader import ImageLibraryLoader
from enum import IntEnum

# img_data = ImageLibraryLoader("/Users/anthony/Documents/CS/Coding/photo_query/test_photos")
# img_generator = img_data.load_images()
# count = 0
# for image in img_generator:
#     print(f"Processing: {image['filename']}")
#     print(f"Metadata: {image['metadata']}")
#     print(f"Path: {image['img_path']}")
#     print(f"GPS_longitude: {image['metadata']['GPSInfo']['GPS_longitude']}")
#     print(f"GPS_latitude: {image['metadata']['GPSInfo']['GPS_latitude']}")
#     print("--------------------------------")
#     count += 1

# print(count)
def get_decimal_from_dms(dms, ref):
    """Converts DMS (degrees, minutes, seconds) to decimal degrees."""
    degrees = dms[0]
    minutes = dms[1] / 60.0
    seconds = dms[2] / 3600.0

    decimal = degrees + minutes + seconds

    # South and West coordinates are negative
    if ref in ['S', 'W']:
        decimal = -decimal

    return decimal

test_img = Image.open("/Users/anthony/Documents/CS/Coding/photo_query/test_photos/IMG_5260.jpg")
exif_data = test_img._getexif()
decoded_exif = {TAGS.get(key): val for key, val in exif_data.items()}
print(decoded_exif["Make"])