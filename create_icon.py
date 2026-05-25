#!/usr/bin/env python3
"""Creates the Ablenote app icon (Ableton-style) and menu bar icon."""

from PIL import Image, ImageDraw, ImageFont
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
    """Creates a clean quarter note icon for the macOS menu bar.

    Uses the ♩ glyph from Apple Symbols for pixel-perfect rendering.
    Renders at high resolution, scaled to 75% within 44×44 (@2x for 22pt).
    """
    render_size = 400
    final_size = 44
    scale = 0.75

    font = ImageFont.truetype("/System/Library/Fonts/Apple Symbols.ttf", 340)
    img = Image.new("RGBA", (render_size, render_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    bbox = draw.textbbox((0, 0), "♩", font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (render_size - w) / 2 - bbox[0]
    y = (render_size - h) / 2 - bbox[1]
    draw.text((x, y), "♩", fill=(0, 0, 0, 255), font=font)

    content_bbox = img.getbbox()
    if content_bbox:
        pad = 4
        crop = (
            max(0, content_bbox[0] - pad),
            max(0, content_bbox[1] - pad),
            min(render_size, content_bbox[2] + pad),
            min(render_size, content_bbox[3] + pad),
        )
        img = img.crop(crop)

    w, h = img.size
    side = max(w, h)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(img, ((side - w) // 2, (side - h) // 2))

    icon_px = int(final_size * scale)
    scaled = square.resize((icon_px, icon_px), Image.LANCZOS)
    result = Image.new("RGBA", (final_size, final_size), (0, 0, 0, 0))
    offset = (final_size - icon_px) // 2
    result.paste(scaled, (offset, offset))
    return result


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
