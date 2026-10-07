import io
import time
from typing import Dict, Any, List, Optional
from PIL import Image, ImageChops, ImageEnhance

class ImageForensicsService:
    """
    Enterprise Image Forensics & Perceptual Hashing Subsystem.
    Performs EXIF inspection, Error Level Analysis (ELA), Difference Hashing (dHash),
    and perceptual image similarity matching.
    """

    @staticmethod
    def compute_dhash(image: Image.Image, hash_size: int = 8) -> str:
        """
        Calculates Difference Hash (dHash) for an image.
        Resizes to (hash_size + 1, hash_size), converts to grayscale, and compares adjacent pixels.
        Returns a hex string representation of the perceptual hash.
        """
        try:
            # Convert to grayscale and resize
            resized = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
            pixels = list(resized.getdata())

            # Compare adjacent pixels horizontally
            difference = []
            for row in range(hash_size):
                for col in range(hash_size):
                    left_pixel = pixels[row * (hash_size + 1) + col]
                    right_pixel = pixels[row * (hash_size + 1) + col + 1]
                    difference.append(left_pixel > right_pixel)

            # Convert boolean array to hex string
            decimal_value = 0
            for i, val in enumerate(difference):
                if val:
                    decimal_value |= (1 << i)
            
            return f"{decimal_value:016x}"
        except Exception:
            return "0000000000000000"

    @staticmethod
    def calculate_hamming_distance(hash1: str, hash2: str) -> int:
        """Computes Hamming distance between two hexadecimal perceptual hashes."""
        try:
            val1 = int(hash1, 16)
            val2 = int(hash2, 16)
            return bin(val1 ^ val2).count('1')
        except Exception:
            return 64  # Maximum distance on error

    @staticmethod
    def analyze_image_manipulation(image_bytes: bytes) -> Dict[str, Any]:
        flags = []
        is_manipulated = False
        ela_score = 15.0  # Low baseline noise

        try:
            image = Image.open(io.BytesIO(image_bytes))
            dhash_val = ImageForensicsService.compute_dhash(image)

            width, height = image.size

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

            # 2. Error Level Analysis (ELA)
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
            tamper_score = round(ela_score / 100.0, 2)

            return {
                "is_manipulated": is_manipulated or ela_score > 60.0,
                "ela_score": round(ela_score, 2),
                "tamper_score": tamper_score,
                "perceptual_hash": dhash_val,
                "dimensions": f"{width}x{height}",
                "camera_info": f"{camera_make} {camera_model}".strip(),
                "software_signature": software or "Clean / Original Camera JPEG",
                "suspicious_flags": flags,
                "forensic_risk": "HIGH" if ela_score > 60.0 else "MEDIUM" if ela_score > 30.0 else "LOW"
            }

        except Exception as e:
            return {
                "is_manipulated": False,
                "ela_score": 0.0,
                "tamper_score": 0.0,
                "perceptual_hash": "0000000000000000",
                "dimensions": "0x0",
                "camera_info": "Unknown",
                "software_signature": "Unreadable",
                "suspicious_flags": [f"FORENSIC_READ_ERROR: {str(e)}"],
                "forensic_risk": "UNKNOWN"
            }

    @staticmethod
    def analyze_image(file_path: str) -> Dict[str, Any]:
        """Wrapper method taking file path directly for forensic analysis."""
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            return ImageForensicsService.analyze_image_manipulation(content)
        except Exception as e:
            return {"tamper_score": 0.0, "ela_score": 0.0, "is_manipulated": False, "perceptual_hash": "0000000000000000"}
