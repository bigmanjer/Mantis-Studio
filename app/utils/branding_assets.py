"""Runtime extraction utilities for MANTIS branding assets.

This avoids committing additional binary slices while still exposing
individual branding elements derived from the master brand board.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

try:
    from PIL import Image, ImageChops
except Exception:  # pragma: no cover - defensive dependency fallback
    Image = None  # type: ignore[assignment]
    ImageChops = None  # type: ignore[assignment]

# Crop boxes are measured against the 1536x1024 source image and represent
# high-resolution (2x) slices.
_BRANDING_SPECS = {
    "mantis_emblem": (76, 54, 462, 336),
    "mantis_wordmark": (706, 118, 1504, 292),
    "mantis_lockup": (706, 394, 1492, 600),
    "mantis_favicon": (47, 871, 169, 993),
}


def _generated_dir(assets_dir: Path) -> Path:
    return assets_dir / ".generated_branding"


def _source_image(assets_dir: Path) -> Path:
    return assets_dir / "NEW MANTIS BRANDING.png"


def _extract_alpha_mask(image: "Image.Image") -> "Image.Image":
    """Build alpha from brightness to remove the dark board background.

    This keeps white/green marks opaque while fading low-luminance backdrop
    so branding elements integrate with the app theme instead of appearing as
    hard-edged rectangles from the source board.
    """
    r, g, b, _ = image.split()
    max_rgb = ImageChops.lighter(ImageChops.lighter(r, g), b)

    floor = 20
    ceiling = 150

    def alpha_curve(v: int) -> int:
        if v <= floor:
            return 0
        if v >= ceiling:
            return 255
        return int((v - floor) * 255 / (ceiling - floor))

    return max_rgb.point(alpha_curve)


def _prepare_branding_slice(image: "Image.Image") -> "Image.Image":
    rgba = image.convert("RGBA")
    alpha = _extract_alpha_mask(rgba)
    rgba.putalpha(alpha)
    return rgba


def ensure_branding_asset(assets_dir: Path, filename: str) -> Optional[Path]:
    """Ensure a generated branding file exists and return its path.

    Supported input format: ``branding/<name>.png`` or ``branding/<name>@2x.png``.
    """
    if not filename.startswith("branding/"):
        return None
    if Image is None:
        return None

    leaf = Path(filename).name
    if not leaf.endswith(".png"):
        return None

    retina = leaf.endswith("@2x.png")
    base_name = leaf[:-7] if retina else leaf[:-4]
    if base_name not in _BRANDING_SPECS:
        return None

    source = _source_image(assets_dir)
    if not source.exists():
        return None

    out_dir = _generated_dir(assets_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / leaf

    if out_path.exists() and out_path.stat().st_mtime >= source.stat().st_mtime:
        return out_path

    crop_box = _BRANDING_SPECS[base_name]
    with Image.open(source).convert("RGBA") as src:
        cropped = src.crop(crop_box)
        processed = _prepare_branding_slice(cropped)
        if not retina:
            processed = processed.resize(
                (max(1, processed.width // 2), max(1, processed.height // 2)),
                Image.Resampling.LANCZOS,
            )
        processed.save(out_path, optimize=True, compress_level=9)

    return out_path


def read_asset_bytes(assets_dir: Path, filename: str) -> Optional[bytes]:
    """Read an asset either from disk or by generating a branding slice."""
    path = assets_dir / filename
    if not path.exists():
        generated = ensure_branding_asset(assets_dir, filename)
        if generated is None:
            return None
        path = generated

    return path.read_bytes()


def resolve_asset_path(assets_dir: Path, filename: str) -> Optional[Path]:
    """Resolve an on-disk path for an asset, generating branding slices as needed."""
    path = assets_dir / filename
    if path.exists():
        return path
    return ensure_branding_asset(assets_dir, filename)
