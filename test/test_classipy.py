"""Automated test cases for classiPY functions"""
import math
import re
import tempfile
from pathlib import Path
import pytest
from PIL import Image
from classipy import classiPY



def test_markings() -> None:
    """Verify correct marking options exist"""
    markings = classiPY.Markings()
    levels = ["CUI", "S", "U"]
    for level in levels:
        assert level == markings.get_symbol(level)


@pytest.mark.parametrize("level,full_name,color", [
    ("CUI", "CUI", (80, 43, 133)),
    ("S", "SECRET", (200, 16, 46)),
    ("U", "UNCLASSIFIED", (0, 122, 51)),
    ])
def test_marking_output(level: str, full_name: str, color: tuple) -> None:
    """Verify correct mappings between short-hand labels and marks that
    will appear on immages and banner colors"""
    markings = classiPY.Markings()
    assert markings.get_long_name(level) == full_name
    assert markings.get_color(level) == color


def count_pixel_colors(filename: Path, banner_percent: int=5) -> tuple:
    pixels = []
    width, height = 0, 0
    with Image.open(filename).convert('RGB') as img:
        width, height = img.width, img.height
        banner_rows = int(height * (banner_percent / 100))
        for row in range(6, banner_rows - 2):
            for column in range(6, width - 6):
                pixels.append(img.getpixel((column, row)))
    most_freq = max(set(pixels), key=pixels.count)
    return most_freq


@pytest.mark.parametrize("level, color", [
    ("CUI", (80, 43, 133)),
    ("S", (200, 16, 46)),
    ("U", (0, 122, 51)),
    ])
def test_banners(level: str, color: tuple) -> None:
    """Verify correct file renaming, banner colors"""
    with tempfile.TemporaryDirectory(dir=Path('/tmp').resolve()) as tempdir:
        classiPY.add_overlay_to_dir(
            Path('./test/figs').resolve(), Path(tempdir),
            classification=level
        )
        filenames = list(Path(tempdir).glob('*.*'))
        num_test_files = len(list(Path("./test/figs").resolve().glob('[!.]*.*')))
        assert len(filenames) == num_test_files
        for filename in filenames:
            assert re.search(f"^({level})*", filename.name)
            banner_color = count_pixel_colors(filename)
            for i, j in zip(banner_color, color):
                assert math.isclose(i, j, abs_tol=22)
