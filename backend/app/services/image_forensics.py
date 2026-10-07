import io
import time
from typing import Dict, Any
from PIL import Image, ImageChops, ImageEnhance

class ImageForensicsService:
    """
    Enterprise Image Forensics & Manipulation Detection Subsystem.
    Performs EXIF inspection, editing software signature detection, and Error Level Analysis (ELA).
    """

    @staticmethod
    def analyze_image_manipulation(image_bytes: bytes) -> Dict[str, Any]:
        flags = []
        is_manipulated = False
        ela_score = 15.0  # Low baseline noise

        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # 1. EXIF Metadata Extraction
            exif_data = image._getexif() if hasattr(image, '_getexif') and image._getexif() else {}
            camera_make = str(exif_data.get(271, "Unknown"))
            camera_model = str(exif_data.get(272, "Unknown"))
            software = str(exif_data.get(305, ""))

            # Check for Photoshop / GIMP editing signatures
            if any(tool in software.lower() for tool in ["photoshop", "gimp", "paint.net", "adobe"]):
                is_manipulated = True
                ela_score += 45.0
                flags.append(f"EDITING_SOFTWARE_DETECTED ({software})")

            # 2. Error Level Analysis (ELA) Simulation
            # Resave image at 95% JPEG quality and compute pixel difference
            resaved_io = io.BytesIO()
            image.convert("RGB").save(resaved_io, "JPEG", quality=95)
            resaved_io.seek(0)
            resaved_image = Image.open(resaved_io)

            diff = ImageChops.difference(image.convert("RGB"), resaved_image)
            extrema = diff.getextrema()
            max_diff = max([ex[1] for ex in extrema])

            if max_diff > 35:
                ela_score += 25.0
                flags.append("HIGH_IMAGE_MODIFICATION_NOISE")

            ela_score = min(100.0, ela_score)

            return {
                "is_manipulated": is_manipulated or ela_score > 60.0,
                "ela_score": round(ela_score, 2),
                "camera_info": f"{camera_make} {camera_model}".strip(),
                "software_signature": software or "Clean / Original Camera JPEG",
                "suspicious_flags": flags,
                "forensic_risk": "HIGH" if ela_score > 60.0 else "MEDIUM" if ela_score > 30.0 else "LOW"
            }

        except Exception as e:
            return {
                "is_manipulated": False,
                "ela_score": 0.0,
                "camera_info": "Unknown",
                "software_signature": "Unreadable",
                "suspicious_flags": [f"FORENSIC_READ_ERROR: {str(e)}"],
                "forensic_risk": "UNKNOWN"
            }
