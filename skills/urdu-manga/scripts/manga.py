#!/usr/bin/env python3
"""Inspect, validate, and typeset reviewed Urdu dialogue manifests over CBZ pages."""
from __future__ import annotations

import argparse
import html
import io
import json
import math
from pathlib import Path
import re
import sys
import zipfile

import pymupdf as fitz
from PIL import Image, ImageDraw, ImageOps

IMAGE_SUFFIXES = {'.png', '.jpg', '.jpeg', '.webp'}
URDU_PROBE = 'ٹڈڑںھہےیگچپژک'
LATIN_RUN = re.compile(r"([A-Za-z][A-Za-z0-9'’ .-]*[A-Za-z0-9]|[A-Za-z])")


def natural_key(value):
    return [int(part) if part.isdigit() else part.casefold()
            for part in re.split(r'(\d+)', value)]


def read_archive(path):
    """Read images without extracting archive paths onto the filesystem."""
    pages = []
    seen = set()
    with zipfile.ZipFile(path) as archive:
        for info in sorted(archive.infolist(), key=lambda entry: natural_key(entry.filename)):
            if info.is_dir() or Path(info.filename).suffix.lower() not in IMAGE_SUFFIXES:
                continue
            if info.filename in seen:
                raise ValueError(f'Duplicate archive page: {info.filename}')
            seen.add(info.filename)
            raw = archive.read(info)
            with Image.open(io.BytesIO(raw)) as image:
                image.load()
                width, height = image.size
            pages.append({'file': info.filename, 'width': width, 'height': height, 'bytes': raw})
    if not pages:
        raise ValueError('The archive contains no supported page images.')
    return pages


def prepare_output(path, overwrite=False):
    path = Path(path)
    if path.exists() and any(path.iterdir()) and not overwrite:
        raise ValueError(f'Output directory is not empty: {path}. Choose a new path or pass --overwrite.')
    path.mkdir(parents=True, exist_ok=True)
    return path


def checked_rect(value, page, label):
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError(f'{label}: expected [left, top, right, bottom].')
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in value):
        raise ValueError(f'{label}: coordinates must be finite numbers.')
    x0, y0, x1, y1 = value
    if not (0 <= x0 < x1 <= page['width'] and 0 <= y0 < y1 <= page['height']):
        raise ValueError(f'{label}: rectangle is outside its source page or has no area.')
    return fitz.Rect(value)


def validate_manifest(manifest, pages):
    if not isinstance(manifest, dict) or manifest.get('version') != 1:
        raise ValueError('Manifest version must be 1.')
    entries = manifest.get('pages')
    if not isinstance(entries, list):
        raise ValueError('Manifest pages must be a list.')
    lookup = {page['file']: page for page in pages}
    seen = set()
    regions = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError('Each manifest page must be an object.')
        filename = entry.get('file')
        if filename not in lookup or filename in seen:
            raise ValueError(f'Unknown or repeated manifest page: {filename}')
        seen.add(filename)
        rows = entry.get('regions', [])
        if not isinstance(rows, list):
            raise ValueError(f'{filename}: regions must be a list.')
        ids = set()
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError(f'{filename}: each region must be an object.')
            ident = row.get('id')
            label = f'{filename}:{ident}'
            if not isinstance(ident, str) or not ident or ident in ids:
                raise ValueError(f'{label}: region IDs must be nonempty and unique on a page.')
            ids.add(ident)
            if row.get('kind', 'dialogue') not in ('dialogue', 'monologue'):
                raise ValueError(f'{label}: only dialogue/monologue may be replaced.')
            if not isinstance(row.get('text'), str) or not row['text'].strip():
                raise ValueError(f'{label}: missing Urdu dialogue text.')
            checked_rect(row.get('box'), lookup[filename], label)
            if 'cleanup' in row:
                checked_rect(row['cleanup'], lookup[filename], label + ':cleanup')
            size = row.get('size', 32)
            if isinstance(size, bool) or not isinstance(size, (int, float)) or not math.isfinite(size) or size <= 0:
                raise ValueError(f'{label}: size must be a positive finite number.')
            for color in ('background', 'foreground'):
                rgb = row.get(color, [1, 1, 1] if color == 'background' else [0, 0, 0])
                if not isinstance(rgb, list) or len(rgb) != 3 or any(
                    isinstance(c, bool) or not isinstance(c, (int, float)) or not math.isfinite(c) or not 0 <= c <= 1 for c in rgb
                ):
                    raise ValueError(f'{label}: {color} must be an RGB list with values from 0 to 1.')
            names = row.get('preserve', [])
            if not isinstance(names, list) or any(not isinstance(name, str) or not name for name in names):
                raise ValueError(f'{label}: preserve must contain nonempty name strings.')
            for name in names:
                if name not in row['text']:
                    raise ValueError(f'{label}: preserved name missing or changed: {name}')
        regions[filename] = rows
    return regions


def check_font(path, regions):
    font = fitz.Font(fontfile=str(path))
    characters = set(URDU_PROBE)
    for rows in regions.values():
        for row in rows:
            characters.update(c for c in row['text'] if '\u0600' <= c <= '\u06ff')
    missing = sorted(c for c in characters if not font.has_glyph(ord(c)))
    if missing:
        raise ValueError('Font lacks required Urdu glyphs: ' + ' '.join(missing))
    return font.name


def make_markup(text, size, foreground):
    def escape(part):
        if re.search('[A-Za-z]', part):
            return '<span class="latin" dir="ltr">' + html.escape(part) + '</span>'
        return html.escape(part)
    content = ''.join(escape(part) for part in LATIN_RUN.split(text)).replace('\n', '<br>')
    rgb = ','.join(str(round(c * 255)) for c in foreground)
    return f'<p dir="rtl" style="font-size:{size}px;color:rgb({rgb})">{content}</p>'


def font_css(archive, font, latin_font, line_height):
    # Give each input a distinct archive prefix, even if the filenames match.
    archive.add(str(font.parent), 'urdu-font')
    src = html.escape(font.name, quote=True)
    css = f'@font-face{{font-family:urdu;src:url("urdu-font/{src}");}}'
    if latin_font:
        archive.add(str(latin_font.parent), 'latin-font')
        latin = html.escape(latin_font.name, quote=True)
        css += f'@font-face{{font-family:latin;src:url("latin-font/{latin}");}}'
    else:
        css += '.latin{font-family:sans-serif;}'
    css += ('body{margin:0;padding:0;font-family:urdu;direction:rtl;text-align:center;}'
            f'p{{margin:0;padding:0;line-height:{line_height};}}'
            '.latin{direction:ltr;font-size:65%;' + ('font-family:latin;' if latin_font else '') + '}')
    return css


def letter_region(page, region, archive, css, min_scale, weight):
    rect = fitz.Rect(region['box'])
    cleanup = fitz.Rect(region.get('cleanup', region['box']))
    page.draw_rect(cleanup, color=None, fill=region.get('background', [1, 1, 1]))
    size = region.get('size', 32)
    story = fitz.Story(html=make_markup(region['text'], size, region.get('foreground', [0, 0, 0])), user_css=css, archive=archive)
    target = fitz.Rect(0, 0, rect.width, rect.height)
    fit = story.fit_scale(target, scale_min=1, scale_max=1/min_scale,
                          flags=fitz.mupdf.FZ_PLACE_STORY_FLAG_NO_OVERFLOW)
    if not fit.big_enough:
        raise ValueError(f"Text cannot fit region {region['id']} at the minimum scale.")
    scale = 1/fit.parameter
    spare = max(0, (fit.rect.y1 - fit.filled[3]) * scale)
    display = fitz.DisplayList(fitz.mupdf.FzRect(0, 0, rect.width, rect.height))
    device = fitz.DeviceWrapper(display.this)
    offsets = [(0, 0)] if weight == 0 else [(-weight, 0), (weight, 0), (0, -weight*.75), (0, weight*.75), (0, 0)]
    for dx, dy in offsets:
        story.draw(device, fitz.Matrix(scale, 0, 0, scale, dx, spare/2+dy))
    device.this.fz_close_device()
    pixmap = display.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=True)
    page.insert_image(rect, stream=pixmap.tobytes('png'), keep_proportion=False)
    return {'id': region['id'], 'scale': round(scale, 4), 'effective_size': round(size*scale, 2)}


def contact_sheet(images, destination):
    thumbs = [ImageOps.contain(image.convert('RGB'), (298, 430)) for image in images]
    sheet = Image.new('RGB', (1200, max(1, math.ceil(len(thumbs)/4))*460), '#cccccc')
    draw = ImageDraw.Draw(sheet)
    for index, thumb in enumerate(thumbs):
        x, y = (index % 4)*300, (index // 4)*460
        sheet.paste(thumb, (x, y+25))
        draw.text((x+8, y+5), str(index+1), fill='black')
    sheet.save(destination)


def inspect_archive(source, output, overwrite=False):
    pages = read_archive(source)
    out = prepare_output(output, overwrite)
    images = []
    manifest = {'version': 1, 'title': Path(source).stem, 'source_language': 'English', 'pages': []}
    for number, page in enumerate(pages, 1):
        image = Image.open(io.BytesIO(page['bytes'])).convert('RGB')
        image.save(out/f'source-{number:04d}.png')
        images.append(image)
        manifest['pages'].append({'file': page['file'], 'regions': []})
    contact_sheet(images, out/'contact-sheet.png')
    (out/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'pages': len(pages), 'output': str(out)}


def render(source, manifest_path, font_path, output, *, latin_font=None, raster_scale=1.5,
           line_height=1.65, min_scale=.45, weight=.24, overwrite=False):
    source, font = Path(source).resolve(), Path(font_path).resolve()
    pages = read_archive(source)
    manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    regions = validate_manifest(manifest, pages)
    font_name = check_font(font, regions)
    if not (math.isfinite(raster_scale) and .5 <= raster_scale <= 4 and math.isfinite(line_height) and 1 <= line_height <= 3
            and math.isfinite(min_scale) and .1 <= min_scale <= 1 and math.isfinite(weight) and 0 <= weight <= 1):
        raise ValueError('Invalid rendering settings: scale .5..4, line-height 1..3, min-scale .1..1, weight 0..1.')
    out = prepare_output(output, overwrite)
    if source.is_relative_to(out.resolve()) or font.is_relative_to(out.resolve()) or Path(manifest_path).resolve().is_relative_to(out.resolve()):
        raise ValueError('Keep source archive, manifest, and font outside the output directory.')
    archive = fitz.Archive()
    css = font_css(archive, font, Path(latin_font).resolve() if latin_font else None, line_height)
    final = fitz.open()
    report = {'font': font_name, 'source_language': manifest.get('source_language', 'unspecified'), 'pages': [], 'warnings': []}
    thumbnails = []
    with zipfile.ZipFile(out/'edition.cbz', 'w', zipfile.ZIP_DEFLATED) as cbz:
        for number, source_page in enumerate(pages, 1):
            working = fitz.open()
            page = working.new_page(width=source_page['width'], height=source_page['height'])
            page.insert_image(page.rect, stream=source_page['bytes'])
            fits = []
            for region in regions.get(source_page['file'], []):
                result = letter_region(page, region, archive, css, min_scale, weight)
                fits.append(result)
                if result['effective_size'] < 18 or result['scale'] < .6:
                    report['warnings'].append(f"Review small lettering: {source_page['file']}:{region['id']}")
            pixmap = page.get_pixmap(matrix=fitz.Matrix(raster_scale, raster_scale), alpha=False)
            filename = f'page-{number:04d}.png'
            pixmap.save(out/filename)
            cbz.write(out/filename, filename)
            dest = final.new_page(width=page.rect.width, height=page.rect.height)
            dest.insert_image(dest.rect, filename=str(out/filename))
            with Image.open(out/filename) as preview:
                thumbnails.append(ImageOps.contain(preview.convert('RGB'), (298, 430)))
            report['pages'].append({'source': source_page['file'], 'output': filename, 'regions': fits})
            working.close()
    final.set_metadata({'title': manifest.get('title', 'Urdu manga dialogue'), 'subject': 'Urdu dialogue edition; original names and action lettering retained'})
    final.save(out/'edition.pdf', deflate=True, garbage=4)
    final.close()
    contact_sheet(thumbnails, out/'contact-sheet.png')
    (out/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    (out/'fit-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    with fitz.open(out/'edition.pdf') as check:
        if len(check) != len(pages):
            raise ValueError('PDF page count does not match the source archive.')
    with zipfile.ZipFile(out/'edition.cbz') as check:
        if len(check.namelist()) != len(pages) or check.testzip() is not None:
            raise ValueError('CBZ integrity or page count check failed.')
    return {'pages': len(pages), 'regions': sum(len(rows) for rows in regions.values()),
            'warnings': report['warnings'], 'output': str(out)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    inspect = sub.add_parser('inspect', help='Extract numbered review PNGs and a manifest skeleton.')
    inspect.add_argument('--source', required=True, type=Path)
    inspect.add_argument('--output', required=True, type=Path)
    inspect.add_argument('--overwrite', action='store_true')
    for command in ('validate', 'render'):
        child = sub.add_parser(command)
        child.add_argument('--source', required=True, type=Path)
        child.add_argument('--manifest', required=True, type=Path)
        child.add_argument('--font', required=True, type=Path)
        if command == 'render':
            child.add_argument('--output', required=True, type=Path)
            child.add_argument('--latin-font', type=Path)
            child.add_argument('--raster-scale', type=float, default=1.5)
            child.add_argument('--line-height', type=float, default=1.65)
            child.add_argument('--min-scale', type=float, default=.45)
            child.add_argument('--weight', type=float, default=.24)
            child.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'inspect':
            result = inspect_archive(args.source, args.output, args.overwrite)
        elif args.command == 'validate':
            pages = read_archive(args.source)
            rows = validate_manifest(json.loads(args.manifest.read_text(encoding='utf-8')), pages)
            result = {'font': check_font(args.font, rows), 'pages': len(pages), 'regions': sum(map(len, rows.values()))}
        else:
            kwargs = vars(args).copy()
            kwargs.pop('command')
            kwargs['manifest_path'] = kwargs.pop('manifest')
            kwargs['font_path'] = kwargs.pop('font')
            result = render(**kwargs)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, zipfile.BadZipFile, fitz.mupdf.FzErrorBase) as exc:
        parser.exit(2, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
