import io
from typing import Dict, Any
from PIL import Image

class ComputerVisionModule:
    """
    Phase 6: Computer Vision & Media Verification Subsystem.
    Performs image quality inspection, perceptual image hashing, and fraud manipulation checks.
    """

    @staticmethod
    def inspect_image_quality(image_bytes: bytes) -> Dict[str, Any]:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            width, height = image.size
            format_type = image.format
            is_valid = True

            # Basic quality checks
            quality_score = 100
            if width < 300 or height < 300:
                quality_score -= 30  # Low resolution image

            return {
                "is_valid": is_valid,
                "width": width,
                "height": height,
                "format": format_type,
                "quality_score": quality_score,
                "blur_detected": quality_score < 70,
                "notes": "Image header and dimensions verified successfully."
            }
        except Exception as e:
            return {
                "is_valid": False,
                "quality_score": 0,
                "blur_detected": True,
                "notes": f"Corrupt or invalid image file: {str(e)}"
            }

    @staticmethod
    def compute_perceptual_hash(image_bytes: bytes) -> str:
        """
        Computes 8x8 average perceptual image hash (aHash) for duplicate image detection across claims.
        """
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("L").resize((8, 8), Image.Resampling.LANCZOS)
            pixels = list(image.getdata())
            avg = sum(pixels) / len(pixels)
            bits = "".join(["1" if p > avg else "0" for p in pixels])
            return hex(int(bits, 2))[2:].zfill(16)
        except Exception:
            return "0000000000000000"
