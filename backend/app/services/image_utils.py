"""
HomeCare+ — Image preparation for AI vision models.

Why this exists
---------------
Browsers lie about content types, phones produce 12 MP HEIC/JPEG files with
EXIF rotation, X-rays often arrive as 16-bit PNGs, and every vision API has
hard limits (Anthropic: 5 MB/image, Groq: 4 MB base64, none accept BMP).
Sending the raw upload is the #1 cause of "image analysis fails".

`prepare_image()` therefore:
  * detects the real format from the bytes (not the client's Content-Type)
  * fixes EXIF orientation and flattens transparency
  * converts 16-bit / palette / CMYK images to a normal 8-bit image
  * downsizes to a sensible resolution and re-encodes under the API size limit
  * strips all metadata (EXIF/GPS/DICOM-ish tags) — privacy for health images
  * runs cheap quality heuristics (too small / dark / flat / blurry) so the
    model and the user are told when the picture itself is the problem
"""
from __future__ import annotations

import base64
import io
from dataclasses import dataclass, field
from typing import List

from PIL import Image, ImageFilter, ImageOps, ImageStat, UnidentifiedImageError

from app.config.settings import settings

# Hard ceiling for the *base64* payload — the strictest provider (Groq) allows 4 MB.
MAX_ENCODED_BYTES = 3_800_000
MAX_RAW_BYTES = MAX_ENCODED_BYTES * 3 // 4

# Refuse absurd pixel counts (decompression bombs) before decoding fully.
Image.MAX_IMAGE_PIXELS = 120_000_000


class ImageError(ValueError):
    """The upload cannot be turned into an analysable image. Message is user-safe."""


@dataclass
class PreparedImage:
    b64: str
    media_type: str                      # always image/jpeg after preparation
    width: int
    height: int
    original_format: str
    original_size: tuple
    resized: bool
    quality_notes: List[str] = field(default_factory=list)

    @property
    def meta(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "original_format": self.original_format,
            "original_width": self.original_size[0],
            "original_height": self.original_size[1],
            "resized": self.resized,
        }


def sniff_kind(data: bytes) -> str:
    """Return 'pdf', 'image', 'text' or 'unknown' from magic bytes."""
    head = data[:16]
    if head.startswith(b"%PDF"):
        return "pdf"
    if (
        head.startswith(b"\xff\xd8\xff")                       # JPEG
        or head.startswith(b"\x89PNG\r\n\x1a\n")               # PNG
        or head[:4] == b"RIFF" and data[8:12] == b"WEBP"       # WEBP
        or head.startswith(b"BM")                              # BMP
        or head[:4] in (b"II*\x00", b"MM\x00*")                # TIFF
        or head[:6] in (b"GIF87a", b"GIF89a")                  # GIF
    ):
        return "image"
    if b"\x00" not in data[:2048]:
        try:
            data[:4096].decode("utf-8")
            return "text"
        except UnicodeDecodeError:
            pass
    if data[128:132] == b"DICM":
        return "dicom"
    return "unknown"


def _to_8bit_rgb(img: Image.Image) -> Image.Image:
    mode = img.mode

    # 16-bit / 32-bit grayscale (typical for X-ray/CT exports): scale properly,
    # otherwise Pillow clips everything above 255 and the image turns white.
    if mode in ("I;16", "I;16L", "I;16B", "I"):
        if mode != "I":
            img = img.convert("I")
        lo, hi = img.getextrema()
        scale = 255.0 / (hi - lo) if hi > lo else 1.0
        img = img.point(lambda p: (p - lo) * scale).convert("L")
        return img.convert("RGB")

    if mode in ("RGBA", "LA", "PA") or (mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        bg = Image.new("RGB", rgba.size, (255, 255, 255))
        bg.paste(rgba, mask=rgba.split()[-1])
        return bg

    if mode == "CMYK":
        return img.convert("RGB")

    if mode == "L":
        return img.convert("RGB")

    return img.convert("RGB")


def _quality_notes(img_rgb: Image.Image, original_size: tuple) -> List[str]:
    notes: List[str] = []
    min_side = min(original_size)
    if min_side < 400:
        notes.append(f"Low resolution ({original_size[0]}×{original_size[1]} px) — fine detail may be lost.")

    gray = img_rgb.convert("L")
    # Work on a small copy: fast and enough for global statistics.
    probe = gray.copy()
    probe.thumbnail((512, 512))
    stat = ImageStat.Stat(probe)
    mean, std = stat.mean[0], stat.stddev[0]

    if std < 12:
        notes.append("Very low contrast — the image looks flat or washed out.")
    if mean < 25:
        notes.append("Image is very dark.")
    elif mean > 235:
        notes.append("Image is very bright / overexposed.")

    # Blur estimate: variance of an edge-filtered copy. Small = few sharp edges.
    edges = probe.filter(ImageFilter.FIND_EDGES)
    edge_var = ImageStat.Stat(edges).var[0]
    if edge_var < 15 and std >= 12:
        notes.append("Image appears blurry or out of focus.")

    return notes


def prepare_image(data: bytes) -> PreparedImage:
    if not data:
        raise ImageError("The uploaded file is empty.")

    kind = sniff_kind(data)
    if kind == "pdf":
        raise ImageError("This is a PDF, not an image. Use the Report Summarizer for PDF reports.")
    if kind == "dicom":
        raise ImageError("DICOM (.dcm) files are not supported yet. Export the scan as a JPG or PNG image first.")
    if kind not in ("image",):
        raise ImageError("Unsupported or corrupted file. Please upload a JPG, PNG, WEBP, BMP, TIFF or GIF image.")

    try:
        img = Image.open(io.BytesIO(data))
        original_format = (img.format or "UNKNOWN").upper()
        img.load()                      # force full decode now so corruption surfaces here
    except Image.DecompressionBombError:
        raise ImageError("The image has too many pixels to process safely. Please upload a smaller version.")
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
        raise ImageError("The image file looks corrupted and could not be read. Please try another copy.")

    try:
        if getattr(img, "n_frames", 1) > 1:
            img.seek(0)                 # animated GIF / multi-page TIFF: first frame only
    except Exception:
        pass

    img = ImageOps.exif_transpose(img)  # honour phone camera rotation
    original_size = img.size

    if min(original_size) < settings.VISION_MIN_EDGE:
        raise ImageError(
            f"The image is too small ({original_size[0]}×{original_size[1]} px) to analyse. "
            f"Please upload at least {settings.VISION_MIN_EDGE}px on the shorter side."
        )

    rgb = _to_8bit_rgb(img)
    notes = _quality_notes(rgb, original_size)

    resized = False
    max_edge = settings.VISION_MAX_EDGE
    if max(rgb.size) > max_edge:
        rgb.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
        resized = True

    # Re-encode as JPEG (metadata-free); step quality/size down until it fits.
    quality = 90
    work = rgb
    while True:
        buf = io.BytesIO()
        work.save(buf, format="JPEG", quality=quality, optimize=True)   # no exif= -> metadata stripped
        raw = buf.getvalue()
        if len(raw) <= MAX_RAW_BYTES:
            break
        if quality > 70:
            quality -= 8
        else:
            w, h = work.size
            if max(w, h) <= 512:
                raise ImageError("The image could not be compressed enough to analyse. Please upload a smaller image.")
            work = work.resize((int(w * 0.85), int(h * 0.85)), Image.Resampling.LANCZOS)
            resized = True

    return PreparedImage(
        b64=base64.standard_b64encode(raw).decode("ascii"),
        media_type="image/jpeg",
        width=work.size[0],
        height=work.size[1],
        original_format=original_format,
        original_size=original_size,
        resized=resized,
        quality_notes=notes,
    )
