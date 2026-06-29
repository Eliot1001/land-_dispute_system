#!/usr/bin/env python
"""
Generate PWA icons using the site's actual logo: the scales-of-justice
emoji (matches the brand mark used in every template header) on the
site's signature purple gradient.
"""
from PIL import Image, ImageDraw, ImageFont
import os

os.makedirs('landsystem/static/images', exist_ok=True)

LOGO_GLYPH = "⚖"  # scales of justice, used as the logo across all templates
GRADIENT_START = (102, 126, 234)  # #667eea
GRADIENT_END = (118, 75, 162)     # #764ba2
EMOJI_FONT = r"C:\Windows\Fonts\seguiemj.ttf"


def create_diagonal_gradient(size, color1, color2):
    """135deg gradient matching the site's CSS: linear-gradient(135deg, color1, color2)"""
    img = Image.new('RGB', (size, size))
    pixels = img.load()
    max_dist = 2 * (size - 1)
    for y in range(size):
        for x in range(size):
            ratio = (x + y) / max_dist
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            pixels[x, y] = (r, g, b)
    return img


def add_logo(img, size):
    """Draw the scales-of-justice emoji centered, sized to stay inside the
    maskable-icon safe zone (inner 80% circle)."""
    draw = ImageDraw.Draw(img)
    font_size = int(size * 0.6)
    font = ImageFont.truetype(EMOJI_FONT, font_size)

    bbox = draw.textbbox((0, 0), LOGO_GLYPH, font=font, embedded_color=True)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (size - text_width) // 2 - bbox[0]
    y = (size - text_height) // 2 - bbox[1]

    draw.text((x, y), LOGO_GLYPH, font=font, embedded_color=True)
    return img


for size in (192, 512):
    print(f"Creating {size}x{size} icon...")
    icon = create_diagonal_gradient(size, GRADIENT_START, GRADIENT_END)
    icon = add_logo(icon, size)
    path = f'landsystem/static/images/logo-{size}x{size}.png'
    icon.save(path)
    print(f"✓ {path} created")

print("\n✅ All PWA icons created successfully!")
