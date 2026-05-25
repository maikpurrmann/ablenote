#!/usr/bin/env python3
"""Creates the Ablenote app icon (Ableton-style) and menu bar icon."""

from PIL import Image, ImageDraw, ImageFont
import math
import os


SIZE = 1024
INSET = 40


def create_app_icon():
    """Creates the main app icon in Ableton Live style."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    bg_color = (162, 155, 192, 255)
    radius = 220
    draw.rounded_rectangle(
        [INSET, INSET, SIZE - INSET, SIZE - INSET],
        radius=radius,
        fill=bg_color,
    )
    draw.rounded_rectangle(
        [INSET, INSET, SIZE - INSET, SIZE - INSET],
        radius=radius,
        outline=(180, 174, 210, 255),
        width=3,
    )

    try:
        for font_path in [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNSDisplay.ttf",
            "/System/Library/Fonts/SFNS.ttf",
        ]:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, 200)
                break
        else:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    text_color = (60, 55, 80, 255)
    text = "Ablenote"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (SIZE - text_w) / 2
    y = (SIZE - text_h) / 2 - 20
    draw.text((x, y), text, fill=text_color, font=font)

    return img


def create_menubar_icon():
    """Creates a clean eighth note icon for the macOS menu bar.

    Renders at 8x size (352×352) for smooth anti-aliasing, then
    downscales to 44×44 (@2x for 22pt menu bar).
    """
    render_size = 352
    final_size = 44
    img = Image.new("RGBA", (render_size, render_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    color = (0, 0, 0, 255)

    # Note head (filled ellipse, tilted ~30°)
    head_cx, head_cy = 130, 270
    head_rx, head_ry = 52, 38

    points = []
    angle_offset = math.radians(-30)
    for i in range(64):
        theta = 2 * math.pi * i / 64
        px = head_rx * math.cos(theta)
        py = head_ry * math.sin(theta)
        rx = px * math.cos(angle_offset) - py * math.sin(angle_offset)
        ry = px * math.sin(angle_offset) + py * math.cos(angle_offset)
        points.append((head_cx + rx, head_cy + ry))
    draw.polygon(points, fill=color)

    # Stem (vertical line from note head up)
    stem_x = head_cx + head_rx * math.cos(angle_offset) - 4
    stem_bottom = head_cy - head_ry * math.sin(angle_offset) + 5
    stem_top = 60
    stem_width = 14
    draw.rectangle(
        [stem_x, stem_top, stem_x + stem_width, stem_bottom],
        fill=color,
    )

    # Flag (curved stroke from top of stem)
    flag_start_x = stem_x + stem_width
    flag_start_y = stem_top

    for i in range(100):
        t = i / 99.0
        # Bezier curve for the flag
        x = flag_start_x + t * 90 * math.sin(t * math.pi * 0.6)
        y = flag_start_y + t * 130
        thickness = 14 * (1 - t * 0.6)
        draw.ellipse(
            [x - thickness / 2, y - thickness / 2,
             x + thickness / 2, y + thickness / 2],
            fill=color,
        )

    # Downscale with high-quality resampling
    img = img.resize((final_size, final_size), Image.LANCZOS)
    return img


def save_iconset(img, output_dir):
    """Creates a .iconset and converts to .icns."""
    iconset_dir = os.path.join(output_dir, "Ablenote.iconset")
    os.makedirs(iconset_dir, exist_ok=True)

    sizes = [16, 32, 64, 128, 256, 512, 1024]
    for size in sizes:
        resized = img.resize((size, size), Image.LANCZOS)
        resized.save(os.path.join(iconset_dir, f"icon_{size}x{size}.png"))
        if size <= 512:
            resized2x = img.resize((size * 2, size * 2), Image.LANCZOS)
            resized2x.save(os.path.join(iconset_dir, f"icon_{size}x{size}@2x.png"))

    icns_path = os.path.join(output_dir, "Ablenote.icns")
    os.system(f'iconutil -c icns "{iconset_dir}" -o "{icns_path}"')

    import shutil
    shutil.rmtree(iconset_dir)

    return icns_path


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))

    app_icon = create_app_icon()
    png_path = os.path.join(script_dir, "icon_preview.png")
    app_icon.save(png_path)
    print(f"App icon preview: {png_path}")

    icns_path = save_iconset(app_icon, script_dir)
    print(f"App icon: {icns_path}")

    menubar_icon = create_menubar_icon()
    menubar_path = os.path.join(script_dir, "icon_menubar.png")
    menubar_icon.save(menubar_path)
    print(f"Menu bar icon: {menubar_path}")
