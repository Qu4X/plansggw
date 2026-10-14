#!/usr/bin/env python3
"""
update_icons.py — Generuje wszystkie warianty ikon PWA z pliku temp/icon.png.
Obsługuje standardowe ikony PNG (any), Apple touch icon oraz maskable icons.
"""
import os
import shutil
from PIL import Image

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_ICON = os.path.join(REPO_ROOT, "temp", "icon.png")
WEB_DIR = os.path.join(REPO_ROOT, "web")
DIST_DIR = os.path.join(REPO_ROOT, "dist")

BG_COLOR = (0, 59, 47, 255)  # Kolor tła ikony SGGW (#003b2f)


def create_maskable_base(src_img: Image.Image) -> Image.Image:
    """
    Tworzy bazowy obraz 512x512 do ikon maskowalnych:
    Pełne tło w kolorze BG_COLOR z nałożonym symbolem tak, aby mieścił się w bezpiecznej strefie (safe zone 80%).
    """
    base = Image.new("RGBA", (512, 512), BG_COLOR)

    # Skalujemy motyw tak, aby bezpiecznie mieścił się w strefie maskowania (np. 85%)
    target_size = int(512 * 0.88)
    scaled_icon = src_img.resize((target_size, target_size), Image.Resampling.LANCZOS)

    offset = ((512 - target_size) // 2, (512 - target_size) // 2)
    base.paste(scaled_icon, offset, scaled_icon)
    return base


def update_icons():
    if not os.path.exists(SRC_ICON):
        raise FileNotFoundError(f"Nie znaleziono pliku źródłowego: {SRC_ICON}")

    print(f"Reading source icon: {SRC_ICON}")
    src = Image.open(SRC_ICON).convert("RGBA")

    # 1. Standardowe ikony PWA (purpose: any)
    icon_512 = src.resize((512, 512), Image.Resampling.LANCZOS)
    icon_192 = src.resize((192, 192), Image.Resampling.LANCZOS)

    icon_512.save(os.path.join(WEB_DIR, "icon-512.png"), "PNG")
    icon_192.save(os.path.join(WEB_DIR, "icon-192.png"), "PNG")
    print("[OK] Generated icon-512.png and icon-192.png")

    # 2. Apple touch icon (180x180, bez przezroczystości)
    apple_bg = Image.new("RGBA", (180, 180), BG_COLOR)
    apple_scaled = src.resize((180, 180), Image.Resampling.LANCZOS)
    apple_bg.paste(apple_scaled, (0, 0), apple_scaled)
    apple_bg.convert("RGB").save(os.path.join(WEB_DIR, "apple-touch-icon.png"), "PNG")
    print("[OK] Generated apple-touch-icon.png")

    # 3. Ikony maskowalne (purpose: maskable)
    maskable_base = create_maskable_base(src)

    maskable_sizes = [48, 72, 96, 128, 192, 384, 512]
    for size in maskable_sizes:
        resized = maskable_base.resize((size, size), Image.Resampling.LANCZOS)
        out_name = f"maskable_icon_x{size}.png"
        resized.save(os.path.join(WEB_DIR, out_name), "PNG")
        print(f"[OK] Generated {out_name}")

    # Dodatkowe aliasy dla spójności
    maskable_base.resize((192, 192), Image.Resampling.LANCZOS).save(
        os.path.join(WEB_DIR, "icon-maskable-192.png"), "PNG"
    )
    maskable_base.save(
        os.path.join(WEB_DIR, "icon-maskable-512.png"), "PNG"
    )
    print("[OK] Generated icon-maskable-192.png and icon-maskable-512.png")

    # 4. Kopia do dist/ jeśli istnieje
    if os.path.exists(DIST_DIR):
        for fname in os.listdir(WEB_DIR):
            if fname.endswith(".png") and ("icon" in fname or "maskable" in fname):
                shutil.copy2(os.path.join(WEB_DIR, fname), os.path.join(DIST_DIR, fname))
        print("[OK] Copied all updated icons to dist/")


if __name__ == "__main__":
    update_icons()
