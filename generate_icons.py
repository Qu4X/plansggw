"""
Skrypt do generowania rastrowych ikon PWA (PNG) dla Planu SGGW
z motywem #12322a (ciemna zieleń akademicka) i liści SGGW.
"""
import os
import math
from PIL import Image, ImageDraw

WEB_DIR = os.path.join(os.path.dirname(__file__), "web")

def draw_sggw_icon(size: int, is_maskable: bool = False) -> Image.Image:
    # Supersampling for anti-aliasing
    scale = 4
    canvas_size = size * scale
    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    bg_color = (18, 50, 42, 255) # #12322a
    border_color = (45, 106, 91, 255) # #2d6a5b

    if is_maskable:
        # Full bleed background for maskable icons
        draw.rectangle([0, 0, canvas_size, canvas_size], fill=bg_color)
    else:
        # Rounded squircle for standard icons
        corner_radius = int(canvas_size * 0.22)
        border_w = max(2, int(canvas_size * 0.015))
        draw.rounded_rectangle(
            [border_w, border_w, canvas_size - border_w, canvas_size - border_w],
            radius=corner_radius,
            fill=bg_color,
            outline=border_color,
            width=border_w
        )

    # Safe zone factor
    factor = 0.60 if is_maskable else 0.72
    center = canvas_size / 2
    span = canvas_size * factor

    # Draw curved stem
    stem_width = max(3, int(canvas_size * 0.028))
    stem_color = (230, 244, 234, 255)

    stem_points = []
    # Curve from lower-left to upper-right
    for t in [i / 50.0 for i in range(51)]:
        # Cubic bezier approx
        x0, y0 = center - span * 0.35, center + span * 0.35
        x1, y1 = center - span * 0.1, center + span * 0.3
        x2, y2 = center + span * 0.15, center + span * 0.05
        x3, y3 = center + span * 0.30, center - span * 0.38
        
        x = (1-t)**3 * x0 + 3*(1-t)**2*t * x1 + 3*(1-t)*t**2 * x2 + t**3 * x3
        y = (1-t)**3 * y0 + 3*(1-t)**2*t * y1 + 3*(1-t)*t**2 * y2 + t**3 * y3
        stem_points.append((x, y))

    for i in range(len(stem_points) - 1):
        draw.line([stem_points[i], stem_points[i+1]], fill=stem_color, width=stem_width)

    # Leaf drawing helper
    def draw_leaf(start_x, start_y, tip_x, tip_y, bulge_left, bulge_right, fill_col):
        pts = []
        # Upper edge
        for t in [i / 20.0 for i in range(21)]:
            nx = (1-t)*start_x + t*tip_x + math.sin(t*math.pi)*bulge_left[0]
            ny = (1-t)*start_y + t*tip_y + math.sin(t*math.pi)*bulge_left[1]
            pts.append((nx, ny))
        # Lower edge
        for t in [i / 20.0 for i in range(20, -1, -1)]:
            nx = (1-t)*start_x + t*tip_x + math.sin(t*math.pi)*bulge_right[0]
            ny = (1-t)*start_y + t*tip_y + math.sin(t*math.pi)*bulge_right[1]
            pts.append((nx, ny))
        draw.polygon(pts, fill=fill_col)

    # Leaf colors
    c_leaf_bright = (52, 211, 153, 255) # emerald / green
    c_leaf_mid = (34, 197, 94, 255)
    c_leaf_gold = (251, 191, 36, 255)

    # Top main leaf
    sx, sy = center + span * 0.25, center - span * 0.28
    tx, ty = center + span * 0.35, center - span * 0.42
    draw_leaf(sx, sy, tx, ty, (-span*0.06, -span*0.06), (span*0.08, span*0.04), c_leaf_bright)

    # Upper left leaf
    sx, sy = center + span * 0.15, center - span * 0.12
    tx, ty = center - span * 0.12, center - span * 0.25
    draw_leaf(sx, sy, tx, ty, (-span*0.08, span*0.06), (span*0.04, -span*0.09), c_leaf_mid)

    # Middle right leaf
    sx, sy = center + span * 0.08, center + span * 0.02
    tx, ty = center + span * 0.32, center + span * 0.08
    draw_leaf(sx, sy, tx, ty, (span*0.06, -span*0.08), (-span*0.04, span*0.08), c_leaf_bright)

    # Lower left leaf
    sx, sy = center - span * 0.05, center + span * 0.15
    tx, ty = center - span * 0.28, center + span * 0.12
    draw_leaf(sx, sy, tx, ty, (-span*0.04, -span*0.08), (span*0.06, span*0.07), c_leaf_mid)

    # Academic acorn / golden seed
    acorn_x = center + span * 0.32
    acorn_y = center - span * 0.18
    acorn_r = span * 0.05
    draw.ellipse([acorn_x - acorn_r, acorn_y - acorn_r, acorn_x + acorn_r, acorn_y + acorn_r], fill=c_leaf_gold)

    # Resample down to target size with Lanczos filter for smooth crisp edges
    resampled = img.resize((size, size), Image.Resampling.LANCZOS)
    return resampled

def generate_all_icons():
    sizes = [48, 72, 96, 128, 192, 384, 512]
    print("Generowanie ikon PWA SGGW...")

    # Standard icons
    for s in [192, 512]:
        fn = f"icon-{s}.png"
        path = os.path.join(WEB_DIR, fn)
        img = draw_sggw_icon(s, is_maskable=False)
        img.save(path, format="PNG")
        print(f" -> {fn}")

    # Apple touch icon
    apple_img = draw_sggw_icon(180, is_maskable=False)
    apple_img.save(os.path.join(WEB_DIR, "apple-touch-icon.png"), format="PNG")
    print(" -> apple-touch-icon.png")

    # Maskable icons
    for s in sizes:
        fn = f"maskable_icon_x{s}.png"
        path = os.path.join(WEB_DIR, fn)
        img = draw_sggw_icon(s, is_maskable=True)
        img.save(path, format="PNG")
        print(f" -> {fn}")

    # Aliases
    img192m = draw_sggw_icon(192, is_maskable=True)
    img192m.save(os.path.join(WEB_DIR, "icon-maskable-192.png"), format="PNG")
    img512m = draw_sggw_icon(512, is_maskable=True)
    img512m.save(os.path.join(WEB_DIR, "icon-maskable-512.png"), format="PNG")
    print(" -> icon-maskable-192.png, icon-maskable-512.png")
    print("Ikony wygenerowane pomyślnie!")

if __name__ == "__main__":
    generate_all_icons()
