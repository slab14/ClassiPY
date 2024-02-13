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
FONT_SIZE = 25
BAR_HEIGHT = 40
EXTS = (".jpg", ".png", ".jpeg", ".bmp")  # file extensions to look for
MARKS = ("CUI", "S", "U")
FONT = Path(__file__).parent / ".." / "font" / "ARIALBD.TTF"


class Markings:
    """Class to define marking options. Options: Unclass, CUI, & Secret"""
    def __init__(self, classifications=MARKS):
        self.classifications = classifications

    def get_symbol(self, classification):
        """Return short-hand symbol for classification"""
        return classification

    def get_long_name(self, classification):
        """Return full name of classification level"""
        out = None
        if classification == "CUI":
            out = "CUI"
        elif classification == "S":
            out = "SECRET"
        elif classification == "U":
            out = "UNCLASSIFIED"
        return out

    def get_color(self, classification):
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
    #font = ImageFont.truetype(str(FONT), FONT_SIZE)
    #banner_height = int(height * (BANNER_PERCENT_OF_HEIGHT / 100))
    banner_height = BAR_HEIGHT
    draw.rectangle(
        [0, 0, width, banner_height],
        fill=markings.get_color(classification)
    )
    draw.rectangle(
        [0, height-banner_height, width, height],
        fill=markings.get_color(classification)
    )
    text_bbox = draw.textbbox(
        (0, 0), markings.get_long_name(classification)
    )
    text_horizontal = width - (text_bbox[2] - text_bbox[0]) // 2
    text_vertical = banner_height - (text_bbox[3] + text_bbox[1]) // 2
    text_position_top = (text_horizontal, text_vertical)
    text_position_bottom = (
        text_horizontal,
        height - banner_height + text_vertical
    )
    draw.text(
        text_position_top, markings.get_long_name(classification),
        fill=(255, 255, 255)
    )
    draw.text(
        text_position_bottom, markings.get_long_name(classification),
        fill=(255, 255, 255)
    )    


def add_border(img: Image.Image, border_thickness: int=5) -> Image.Image:
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


def add_banner(input_image, output_image, classification="CUI"):
    """Function to add top & bottom portion markings to image file"""
    with Image(filename=input_image) as img:

        banner = Image(width=img.width, height=banner_height)
        banner.background_color = markings.get_color(classification)
        banner.alpha_channel = "remove"

        # Calculate font size based on a percentage of the banner's height
        font_size = int(banner_height * (FONT_PERCENT_OF_BANNER / 90))

        with Drawing() as draw:
            draw.font_size = font_size
            draw.font_weight = 700  # Bold font weight
            draw.fill_color = Color("white")
            draw.text_alignment = "center"
            draw.text(
                x=banner.width // 2,
                y=banner_height // 2 + font_size // 3,
                body=markings.get_long_name(classification),
            )
            draw.text(
                x=banner.width // 2,
                y=img.height + 2 * banner_height // 2 + font_size // 3,
                body=markings.get_long_name(classification),
            )
            draw(banner)

        with Image(
            filename=input_image
        ) as img:  # Re-open the image to avoid closure issue
            with Image(
                width=img.width, height=img.height + 2 * banner_height
            ) as result:
                result.composite(banner, top=0, left=0)
                result.composite(img, top=banner_height, left=0)
                result.composite(banner, top=img.height + banner_height, left=0)
                border_style = 6  # Change border
                result.border(
                    color=Color("black"), width=border_style,
                    height=border_style
                )
                result.save(filename=output_image)


def label_folder(input_folder, output_folder, classification="CUI"):
    """Function to rename all files with classification marking \
    Calls the `add_banner` function to mark images """
    if not Path(output_folder).exists():
        output_folder.mkdir(parents=True, exist_ok=True)

    image_files = [
        x for x in Path(input_folder).iterdir() if x.suffix.lower() in EXTS
    ]

    for image_file in image_files:
        output_file = Path(
            output_folder, f"({markings.get_symbol(classification)}) {image_file.name}"
        )
        add_banner(image_file, output_file, classification)

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
