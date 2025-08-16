from PIL.ExifTags import TAGS, GPSTAGS
from PIL import Image, ExifTags
import PIL.TiffImagePlugin
import os
import numpy as np
import fractions

def get_float_from_rational(rational):
    res = rational
    if isinstance(rational, PIL.TiffImagePlugin.IFDRational):
        numerator = rational.numerator
        denominator = rational.denominator
        frac = fractions.Fraction(numerator, denominator)
        res = float(frac)
    return res

class Metadata:
    class GPS:
        def __init__(self, gps_info):
            self.decoded_gps = {GPSTAGS.get(key): val for key, val in gps_info.items()}
            self.GPSLatitude = None
            self.GPSLongitude = None
            self.GPSAltitude = None
            self.GPSDirection = None
            self.set_GPSInfo()
        
        def get_decimal_from_dms(self, dms, ref):
            """Converts DMS (degrees, minutes, seconds) to decimal degrees."""
            try:
                degrees = float(get_float_from_rational(dms[0]))
                minutes = float(get_float_from_rational(dms[1])) / 60.0
                seconds = float(get_float_from_rational(dms[2])) / 3600.0
            except Exception:
                try:
                    d0, d1, d2 = dms
                    degrees = float(get_float_from_rational(d0))
                    minutes = float(get_float_from_rational(d1)) / 60.0
                    seconds = float(get_float_from_rational(d2)) / 3600.0
                except Exception:
                    return None

            decimal = degrees + minutes + seconds
            # South and West coordinates are negative
            if ref in ['S', 'W']:
                decimal = -decimal

            return float(decimal)
        
        def set_GPSInfo(self):
            self.setLatitude()
            self.setLongitude()
            self.setAltitude()
            self.setDirection()
        
        def setLatitude(self):
            if "GPSLatitudeRef" in self.decoded_gps.keys() and "GPSLatitude" in self.decoded_gps.keys():
                GPSLatitudeRef = self.decoded_gps['GPSLatitudeRef']
                self.GPSLatitude = self.get_decimal_from_dms(self.decoded_gps['GPSLatitude'], GPSLatitudeRef)
        
        def setLongitude(self):
            if "GPSLongitudeRef" in self.decoded_gps.keys() and "GPSLongitude" in self.decoded_gps.keys():
                GPSLongitudeRef = self.decoded_gps['GPSLongitudeRef']
                self.GPSLongitude = self.get_decimal_from_dms(self.decoded_gps['GPSLongitude'], GPSLongitudeRef)
        
        def setAltitude(self):
            if "GPSAltitudeRef" in self.decoded_gps.keys() and "GPSAltitude" in self.decoded_gps.keys():
                ref = self.decoded_gps['GPSAltitudeRef']
                altitude = get_float_from_rational(self.decoded_gps['GPSAltitude'])
                if altitude is None:
                    self.GPSAltitude = None
                    return
                # Normalize ref to an integer 0/1
                ref_val = 0
                try:
                    if isinstance(ref, (int, float)):
                        ref_val = int(ref)
                    elif isinstance(ref, (bytes, bytearray)):
                        ref_list = list(ref)
                        ref_val = ref_list[0] if len(ref_list) > 0 else 0
                    else:
                        ref_val = int(str(ref))
                except Exception:
                    ref_val = 0
                self.GPSAltitude = float(altitude) if ref_val == 0 else -1.0 * float(altitude)
        
        def setDirection(self):
            if "GPSImgDirection" in self.decoded_gps.keys():
                direction = self.decoded_gps['GPSImgDirection']
                direction = get_float_from_rational(direction)
                try:
                    self.GPSDirection = float(direction)
                except Exception:
                    self.GPSDirection = None
        
        def get_dict(self):
            return {
                "GPSLatitude": self.GPSLatitude,
                "GPSLongitude": self.GPSLongitude,
                "GPSAltitude": self.GPSAltitude,
                "GPSDirection": self.GPSDirection
            }

        def __repr__(self):
            def _fmt_coord(value):
                if value is None:
                    return None
                try:
                    return round(float(value), 6)
                except Exception:
                    return value
            return (
                f"GPS("
                f"Latitude={_fmt_coord(self.GPSLatitude)}, "
                f"Longitude={_fmt_coord(self.GPSLongitude)}, "
                f"Altitude={self.GPSAltitude!r}, "
                f"Direction={self.GPSDirection!r})"
            )

    def __init__(self, image_path, exif_data):
        self.decoded_exif = {TAGS.get(key): val for key, val in (exif_data.items() if exif_data else [])}
        self.image_path = image_path
        self.exif_data = exif_data
        self.GPSInfo = None
        self.Make = None
        self.Model = None
        self.Software = None
        self.DateTime = None
        self.XResolution = None
        self.YResolution = None
        self.Flash = None
        self.FocalLength = None
        self.LensMake = None
        self.LensModel = None
        self.set_metadata()
    
    def set_metadata(self):
        self.set_GPSInfo()
        self.set_Make()
        self.set_Model()
        self.set_Software()
        self.set_DateTime()
        self.set_XResolution()
        self.set_YResolution()
        self.set_Flash()
        self.set_FocalLength()
        self.set_LensMake()
        self.set_LensModel()
    
    def set_GPSInfo(self):
        if "GPSInfo" in self.decoded_exif.keys():
            self.GPSInfo = self.GPS(self.decoded_exif['GPSInfo'])
    
    def set_Make(self):
        if "Make" in self.decoded_exif.keys():
            self.Make = self._sanitize_value(self.decoded_exif['Make'])
    
    def set_Model(self):
        if "Model" in self.decoded_exif.keys():
            self.Model = self._sanitize_value(self.decoded_exif['Model'])
    
    def set_Software(self):
        if "Software" in self.decoded_exif.keys():
            self.Software = self._sanitize_value(self.decoded_exif['Software'])
    
    def set_DateTime(self):
        if "DateTime" in self.decoded_exif.keys():
            self.DateTime = self._sanitize_value(self.decoded_exif['DateTime'])
    
    def set_XResolution(self):
        if "XResolution" in self.decoded_exif.keys():
            x_resolution = self.decoded_exif['XResolution']
            x_resolution = get_float_from_rational(x_resolution)
            try:
                self.XResolution = float(x_resolution)
            except Exception:
                self.XResolution = self._sanitize_value(x_resolution)
    
    def set_YResolution(self):
        if "YResolution" in self.decoded_exif.keys():
            y_resolution = self.decoded_exif['YResolution']
            y_resolution = get_float_from_rational(y_resolution)
            try:
                self.YResolution = float(y_resolution)
            except Exception:
                self.YResolution = self._sanitize_value(y_resolution)
    
    def set_Flash(self):
        if "Flash" in self.decoded_exif.keys():
            value = self.decoded_exif['Flash']
            if isinstance(value, bool):
                self.Flash = value
            else:
                try:
                    self.Flash = int(value)
                except Exception:
                    self.Flash = self._sanitize_value(value)
    
    def set_FocalLength(self):
        if "FocalLength" in self.decoded_exif.keys():
            focal_length = self.decoded_exif['FocalLength']
            focal_length = get_float_from_rational(focal_length)
            try:
                self.FocalLength = float(focal_length)
            except Exception:
                self.FocalLength = self._sanitize_value(focal_length)
    
    def set_LensMake(self):
        if "LensMake" in self.decoded_exif.keys():
            self.LensMake = self._sanitize_value(self.decoded_exif['LensMake'])
    
    def set_LensModel(self):
        if "LensModel" in self.decoded_exif.keys():
            self.LensModel = self._sanitize_value(self.decoded_exif['LensModel'])

    @staticmethod
    def _sanitize_value(value):
        """Coerce EXIF-derived values to allowed primitive types: str, int, float, bool, or None."""
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, (bytes, bytearray)):
            try:
                return value.decode('utf-8', errors='ignore')
            except Exception:
                try:
                    return value.decode('latin-1', errors='ignore')
                except Exception:
                    return str(value)
        try:
            import numpy as _np
            if isinstance(value, (_np.integer, _np.floating, _np.bool_)):
                return value.item()
        except Exception:
            pass
        try:
            return float(value)
        except Exception:
            pass
        return str(value)
    
    def get_dict(self):
        if self.GPSInfo is not None:
            gps_dict = self.GPSInfo.get_dict()
        else:
            gps_dict = {}
        meta_dict = {
            "GPSLatitude": None,
            "GPSLongitude": None,
            "GPSAltitude": None,
            "GPSDirection": None,
            "Make": self.Make,
            "Model": self.Model,
            "Software": self.Software,
            "DateTime": self.DateTime,
            "XResolution": self.XResolution,
            "YResolution": self.YResolution,
            "Flash": self.Flash,
            "FocalLength": self.FocalLength,
            "LensMake": self.LensMake,
            "LensModel": self.LensModel
        }
        meta_dict.update(gps_dict)
        return {k: self._sanitize_value(v) for k, v in meta_dict.items()}

    def __repr__(self):
        fields = {
            "GPSInfo": self.GPSInfo,
            "Make": self.Make,
            "Model": self.Model,
            "Software": self.Software,
            "DateTime": self.DateTime,
            "XResolution": self.XResolution,
            "YResolution": self.YResolution,
            "Flash": self.Flash,
            "FocalLength": self.FocalLength,
            "LensMake": self.LensMake,
            "LensModel": self.LensModel
        }
        out = ""
        for key, value in fields.items():
            if value is not None:
                out += f"{key}: {value}\n"
        return out

class Library:
    image_types = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".ico", ".webp", ".heic", ".heif"]
    def __init__(self, directory_path):
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"The folder path {directory_path} does not exist.")
        self.directory_path = directory_path
        self.data = self.load_images()
    
    def load_images(self):
        id_counter = 1
        for filename in os.listdir(self.directory_path):
            file_path = os.path.join(self.directory_path, filename)
            if os.path.isfile(file_path) and os.path.splitext(filename)[1].lower() in self.image_types:
                try:
                    img = Image.open(file_path)
                    exif_data = img._getexif()
                    img_np = np.array(img)
                    yield {
                        "id": f"id{id_counter}",
                        "filename": filename,
                        "file_path": file_path,
                        "image_np": img_np,
                        "metadata": Metadata(file_path, exif_data)
                    }
                except Exception as e:
                    print(f"Error loading image {filename}: {e}")
                    continue
                id_counter += 1

    def __repr__(self):
        return f"Library(num_images={len(self.metadata)}"
    
if __name__ == "__main__":
    library = Library("/Users/anthony/Documents/CS/Coding/photo_query/test_photos")
    for data in library.data:
        metadata = data["metadata"]
        for key, value in metadata.get_dict().items():
            print(f"{key}: {value} ({type(value)})")
   
        print("--------------------------------")