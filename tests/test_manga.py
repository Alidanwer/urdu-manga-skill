import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

import pymupdf as fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('manga', ROOT/'skills/urdu-manga/scripts/manga.py')
manga = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manga)


def image_bytes(color='white'):
    buffer = io.BytesIO()
    Image.new('RGB', (300, 220), color).save(buffer, format='PNG')
    return buffer.getvalue()


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root/'source.cbz'
        with zipfile.ZipFile(self.source, 'w') as archive:
            archive.writestr('page-10.png', image_bytes('gray'))
            archive.writestr('page-2.png', image_bytes())
        self.pages = manga.read_archive(self.source)
        self.manifest = {'version': 1, 'pages': [{'file': 'page-2.png', 'regions': [{
            'id': 'speech', 'kind': 'dialogue', 'text': 'Zara، کیا تم تیار ہو؟',
            'preserve': ['Zara'], 'box': [20, 20, 280, 180], 'size': 38}]}]}

    def tearDown(self):
        self.temp.cleanup()

    def test_natural_order_and_untouched_pages(self):
        self.assertEqual([p['file'] for p in self.pages], ['page-2.png', 'page-10.png'])
        self.assertEqual(list(manga.validate_manifest(self.manifest, self.pages)), ['page-2.png'])

    def test_archive_paths_are_never_extracted(self):
        with zipfile.ZipFile(self.root/'nested.cbz', 'w') as archive:
            archive.writestr('../outside.png', image_bytes())
        manga.inspect_archive(self.root/'nested.cbz', self.root/'inspection')
        self.assertFalse((self.root/'outside.png').exists())
        self.assertTrue((self.root/'inspection/source-0001.png').exists())

    def test_changed_name_is_rejected(self):
        self.manifest['pages'][0]['regions'][0]['text'] = 'کیا تم تیار ہو؟'
        with self.assertRaisesRegex(ValueError, 'preserved name'):
            manga.validate_manifest(self.manifest, self.pages)

    def test_outside_rectangle_is_rejected(self):
        self.manifest['pages'][0]['regions'][0]['box'] = [20, 20, 400, 210]
        with self.assertRaisesRegex(ValueError, 'outside'):
            manga.validate_manifest(self.manifest, self.pages)

    def test_action_regions_are_rejected(self):
        self.manifest['pages'][0]['regions'][0]['kind'] = 'sound-effect'
        with self.assertRaisesRegex(ValueError, 'dialogue/monologue'):
            manga.validate_manifest(self.manifest, self.pages)

    def test_duplicate_manifest_page_is_rejected(self):
        self.manifest['pages'].append(self.manifest['pages'][0])
        with self.assertRaisesRegex(ValueError, 'repeated'):
            manga.validate_manifest(self.manifest, self.pages)

    def test_nonfinite_coordinates_are_rejected(self):
        self.manifest['pages'][0]['regions'][0]['box'][0] = float('nan')
        with self.assertRaisesRegex(ValueError, 'finite'):
            manga.validate_manifest(self.manifest, self.pages)

    def test_existing_output_requires_explicit_overwrite(self):
        target = self.root/'output'
        target.mkdir()
        (target/'keep.txt').write_text('keep', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'not empty'):
            manga.prepare_output(target)
        self.assertEqual((target/'keep.txt').read_text(), 'keep')

    def test_missing_urdu_glyphs_are_rejected(self):
        font = self.root/'latin.ttf'
        font.write_bytes(fitz.Font('helv').buffer)
        with self.assertRaisesRegex(ValueError, 'Urdu glyphs'):
            manga.check_font(font, {})

    def test_white_lettering_is_visible_on_black(self):
        document = fitz.open()
        page = document.new_page(width=300, height=220)
        page.draw_rect(page.rect, fill=(0, 0, 0), color=None)
        region = {'id': 'reverse', 'text': 'Ready?', 'box': [20, 20, 280, 200],
                  'size': 40, 'background': [0, 0, 0], 'foreground': [1, 1, 1]}
        manga.letter_region(page, region, fitz.Archive(),
            'body{margin:0;font-family:sans-serif;}p{margin:0;text-align:center;line-height:1.65}', .45, .24)
        pix = page.get_pixmap(alpha=False)
        data = list(pix.samples)
        self.assertGreater(sum(value > 240 for value in data), 300)
        self.assertGreater(sum(value < 10 for value in data), len(data)*.8)
        document.close()

    @unittest.skipUnless(os.environ.get('URDU_MANGA_TEST_FONT'), 'Supply a local Urdu font for full rendering integration.')
    def test_full_urdu_render_preserves_untouched_page(self):
        path = self.root/'dialogue.json'
        path.write_text(json.dumps(self.manifest, ensure_ascii=False), encoding='utf-8')
        output = self.root/'edition'
        result = manga.render(self.source, path, os.environ['URDU_MANGA_TEST_FONT'], output, raster_scale=1)
        self.assertEqual((result['pages'], result['regions']), (2, 1))
        with fitz.open(output/'edition.pdf') as pdf:
            self.assertEqual(len(pdf), 2)
        with zipfile.ZipFile(output/'edition.cbz') as cbz:
            self.assertIsNone(cbz.testzip())
            self.assertEqual(len(cbz.namelist()), 2)
        with Image.open(output/'page-0002.png') as image:
            self.assertEqual(image.getpixel((150, 110)), (128, 128, 128))
        self.assertFalse(any(p.suffix == '.ttf' for p in output.iterdir()))


if __name__ == '__main__':
    unittest.main()
