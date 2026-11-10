#!/usr/bin/env python3
"""Generate an original geometric comic fixture; no third-party art or fonts."""
import argparse
import io
from pathlib import Path
import zipfile
from PIL import Image, ImageDraw, ImageFont


def demo_page():
    image = Image.new('RGB', (700, 950), 'white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=25)
    draw.text((40, 24), 'THE BRIDGE - SYNTHETIC COMIC DEMO', font=font, fill='black')
    for top in (85, 435):
        draw.rectangle((35, top, 665, top+310), outline='black', width=4)
        draw.rounded_rectangle((95, top+35, 605, top+205), radius=25, outline='black', width=3)
        # Original simple stick figure and bridge lines.
        draw.ellipse((125, top+225, 155, top+255), outline='black', width=3)
        draw.line((140, top+255, 140, top+290), fill='black', width=3)
        draw.line((110, top+270, 170, top+270), fill='black', width=3)
        draw.line((140, top+290, 120, top+305), fill='black', width=3)
        draw.line((140, top+290, 160, top+305), fill='black', width=3)
    draw.text((165, 170), 'Zara, are you ready?', font=font, fill='black')
    draw.text((135, 520), 'Yes. I will protect the bridge.', font=font, fill='black')
    draw.text((435, 355), 'WHOOSH!', font=font, fill='black')
    draw.line((85, 820, 615, 820), fill='black', width=6)
    for x in range(95, 615, 55):
        draw.line((x, 820, x, 865), fill='black', width=3)
    draw.text((65, 905), 'Original sample. Captions and sounds stay English.', font=ImageFont.load_default(size=20), fill='black')
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    image = demo_page()
    image.save(args.output/'source.png')
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    with zipfile.ZipFile(args.output/'demo.cbz', 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('page-1.png', buf.getvalue())
    print(args.output/'demo.cbz')


if __name__ == '__main__':
    main()
