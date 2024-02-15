#!/usr/bin/env python3
"""This module provides an interface for labelling all images in a folder"""
import click
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

BANNER_PERCENT_OF_HEIGHT = 5  # Adjust the percentage as needed
FONT_PERCENT_OF_BANNER = 50  # Adjust the font size percentage as needed
EXTS = (".jpg", ".png", ".jpeg", ".bmp")  # file extensions to look for
MARKS = ("CUI", "S", "U")
FONT = Path(__file__).parents[1] / "font" / "ARIALBD.TTF"


class Markings:
    """Class to define marking options. Options: Unclass, CUI, & Secret"""
    def __init__(self, classifications: str=MARKS) -> str:
        self.classifications = classifications

    def get_symbol(self, classification: str) -> str:
        """Return short-hand symbol for classification"""
        return classification

    def get_long_name(self, classification: str) -> str:
        """Return full name of classification level"""
        out = None
        if classification == "CUI":
            out = "CUI"
        elif classification == "S":
            out = "SECRET"
        elif classification == "U":
            out = "UNCLASSIFIED"
        return out

    def get_color(self, classification: str) -> str:
        """Return color for banner matching classification level"""
        out = None
        if classification == "CUI":
            out = (80, 43, 133)
        elif classification == "S":
            out = (200, 16, 46)
        elif classification == "U":
            out = (0, 122, 51)
        return out


markings = Markings()


def draw_overlay(
        draw: ImageDraw.ImageDraw, width: int, height: int,
        classification: str='CUI'
) -> None:
    """Add overlay banner with classification markings."""
    banner_height = int(height * (BANNER_PERCENT_OF_HEIGHT / 100))
    font = ImageFont.truetype(
        str(FONT), int(banner_height * (FONT_PERCENT_OF_BANNER / 100))
    )
    color = markings.get_color(classification)
    bottom_offset = height - banner_height
    draw.rectangle([0, 0, width, banner_height],fill=color)
    draw.rectangle([0, bottom_offset, width, height], fill=color)
    text = markings.get_long_name(classification)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_horizontal = (width - (text_bbox[2] - text_bbox[0])) // 2
    text_vertical = (banner_height - (text_bbox[3] + text_bbox[1])) // 2
    text_position_top = (text_horizontal, text_vertical)
    text_position_bottom = (text_horizontal, bottom_offset + text_vertical)
    draw.text(text_position_top, text, font=font, fill=(255, 255, 255))
    draw.text(text_position_bottom, text, font=font, fill=(255, 255, 255))    


def add_border(img: Image.Image, border_thickness: int=5) -> Image.Image:
    """Add black border around image"""
    width, height = img.size
    bordered_img = Image.new(
        "RGB",
        (width + 2 * border_thickness, height + 2 * border_thickness),
        (0, 0, 0)
    )
    bordered_img.paste(img, (border_thickness, border_thickness))
    return bordered_img
    

def save_image_with_overlay(
        image_path: Path, new_path: Path,
        classification: str, border_thickness: int=5
) -> None:
    """Take input image, add overlay with classification, and black border.
    Save image with classification level in file name"""
    try:
        img = Image.open(image_path)
        width, height = img.size
        banner_height = int(height * (BANNER_PERCENT_OF_HEIGHT / 100))    
        new_height = height + 2 * banner_height
        new_img = Image.new("RGB", (width, new_height), (0, 0, 0))
        draw = ImageDraw.Draw(new_img)
        draw_overlay(draw, width, new_height, classification)
        new_img.paste(img, (0, banner_height))
        bordered_img = add_border(new_img, border_thickness)
        bordered_img.save(new_path)
        logging.info(f"Saved {image_path.name} to: {new_path}")
    except FileNotFoundError:
        logging.error(f"Error: File not found at {image_path}")
    except Exception as e:
        logging.error(f"Error opening image: {e}")
    

def add_overlay_to_dir(
        directory_path: Path, output_path: Path,
        classification: str='CUI') -> None:
    """Iterate through all supported image files in a director"""
    if not Path(output_path).exists():
        output_path.mkdir(parents=True, exist_ok=True)
    image_files = [
        x for x in Path(directory_path).iterdir() if x.suffix.lower() in EXTS
    ]
    for image_file in image_files:
        overlayed_image = Path(
            output_path,
            f"({markings.get_symbol(classification)}) {image_file.name}"
        )
        save_image_with_overlay(
            image_file, overlayed_image, classification
        )


@click.command()
@click.argument(
    'images', required=True,
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True
    )
)
@click.argument(
    'classification', required=True,
    type=click.Choice(MARKS, case_sensitive=False)
)
@click.option(
    '--output', required=False, type=click.Path()
)
def main(images, classification, output):
    images = Path(images).resolve()
    output = images if output is None else Path(output).resolve()
    #label_folder(images, output, classification)
    add_overlay_to_dir(images, output, classification)


if __name__ == "__main__":
    main()
