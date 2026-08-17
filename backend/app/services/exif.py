"""EXIF extraction: GPS, camera model, capture timestamp."""
from PIL import ExifTags, Image
from PIL.ExifTags import GPSTAGS


def _to_degrees(value) -> float:
    d, m, s = value
    return float(d) + float(m) / 60 + float(s) / 3600


def extract_exif(path: str) -> dict:
    out: dict = {"camera": None, "captured_at": None, "gps": None, "raw": {}}
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            if not exif:
                return out
            tags = {ExifTags.TAGS.get(k, str(k)): v for k, v in exif.items()}

            make = tags.get("Make", "").strip() if isinstance(tags.get("Make"), str) else ""
            model = tags.get("Model", "").strip() if isinstance(tags.get("Model"), str) else ""
            if make or model:
                out["camera"] = f"{make} {model}".strip()

            out["captured_at"] = tags.get("DateTimeOriginal") or tags.get("DateTime")

            gps_ifd = exif.get_ifd(0x8825)  # GPSInfo IFD
            if gps_ifd:
                gps = {GPSTAGS.get(k, str(k)): v for k, v in gps_ifd.items()}
                lat, lon = gps.get("GPSLatitude"), gps.get("GPSLongitude")
                if lat and lon:
                    latitude = _to_degrees(lat)
                    longitude = _to_degrees(lon)
                    if gps.get("GPSLatitudeRef") == "S":
                        latitude = -latitude
                    if gps.get("GPSLongitudeRef") == "W":
                        longitude = -longitude
                    out["gps"] = {"lat": round(latitude, 6), "lon": round(longitude, 6)}

            out["raw"] = {
                k: str(v) for k, v in tags.items()
                if k in ("Make", "Model", "Software", "DateTime", "DateTimeOriginal",
                         "LensModel", "FNumber", "ISOSpeedRatings", "ExposureTime")
            }
    except Exception:  # noqa: BLE001 - corrupt EXIF is common
        pass
    return out
