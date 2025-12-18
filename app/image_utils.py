import sys
from PIL import Image, ImageOps
import numpy as np
import logging

# Configure logging
logger = logging.getLogger(__name__)


# Resize resolution as parameter
def apply_gamma_correction(image, gamma=1.0):
    """
    Apply gamma correction to an image.

    Args:
        image: PIL Image in RGB mode
        gamma: Gamma value (> 1.0 brightens, < 1.0 darkens, default: 1.0 = no correction)

    Returns:
        PIL Image with gamma correction applied
    """
    if gamma == 1.0:
        return image

    # Convert PIL image to numpy array
    img_array = np.array(image, dtype=np.float32) / 255.0

    # Apply gamma correction: output = input ^ (1/gamma)
    corrected = np.power(img_array, 1.0 / gamma)

    # Convert back to 0-255 range
    corrected = (corrected * 255.0).astype(np.uint8)

    # Convert back to PIL Image
    return Image.fromarray(corrected, mode="RGB")


def process_image(
    input_path,
    output_path,
    dither=True,
    resize=False,
    crop=False,
    width=800,
    height=480,
    palette_image=None,
    gamma=1.0,
):
    """
    Process an image for e-ink display.

    Args:
        input_path: Path to the input image
        output_path: Path to save the processed image
        dither: Whether to use dithering (default: True)
        resize: Whether to resize the image (default: False)
        crop: Whether to crop or letterbox when resizing (default: False)
        width: Target width (default: 800)
        height: Target height (default: 480)
        palette_image: Optional PIL Image with palette. If None, uses 3-bit palette.
        gamma: Gamma correction value (default: 1.0 = no correction, < 1.0 brightens, > 1.0 darkens)
    """
    try:
        source = Image.open(input_path).convert("RGB")
        logger.info(f"source before conversion = {source.size}")

        # Apply EXIF orientation if present to prevent unintended flips
        try:
            source = ImageOps.exif_transpose(source)
            logger.info("Applied EXIF orientation")
        except Exception as e:
            logger.warning(f"Could not apply EXIF orientation: {e}")

        logger.info(f"source = {source.size}")

        # --- Resizing Logic ---
        if resize:
            target_size = (width, height)

            if crop:
                # "Fill and Crop":
                # Scales the image to completely cover 800x480, then crops the center.
                # No black bars, no distortion.
                source = ImageOps.fit(
                    source, target_size, method=Image.Resampling.LANCZOS
                )
            else:
                # "Fit / Letterbox":
                # Scales to fit INSIDE 800x480. Adds black bars if aspect ratio differs.
                source.thumbnail(target_size, Image.Resampling.LANCZOS)

                # Create black background
                new_bg = Image.new("RGB", target_size, (0, 0, 0))

                # Center the image
                left = (target_size[0] - source.width) // 2
                top = (target_size[1] - source.height) // 2
                new_bg.paste(source, (left, top))
                source = new_bg
        # ----------------------

        # Apply gamma correction if specified
        if gamma != 1.0:
            source = apply_gamma_correction(source, gamma)

        # Quantize to palette
        if palette_image is None:
            print(f"❌ Error: No palette image provided.")
            sys.exit(1)

        dither_mode = Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE

        output_image = source.quantize(palette=palette_image, dither=dither_mode)
        output_image.save(output_path)

        print(
            f"✅ Success! Saved {output_image.size[0]}x{output_image.size[1]} image to: {output_path}"
        )

    except FileNotFoundError:
        print(f"❌ Error: The file '{input_path}' was not found.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
