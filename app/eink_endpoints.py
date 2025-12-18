"""
E-Ink image processing endpoints
Handles image processing and delivery for e-ink displays
"""

import logging
import random
from pathlib import Path
import tempfile

from aiohttp import web
import aiofiles

from display_config import load_display_config, list_available_displays
from image_utils import process_image

# Configure logging
logger = logging.getLogger(__name__)


async def api_get_eink_image(gallery, request: web.Request) -> web.Response:
    """GET /api/images/eink/{filename} - Get processed image for e-ink display (filename can be basename without extension)"""
    try:
        basename = request.match_info.get('filename')
        display_type = request.rel_url.query.get('display')
        crop = request.rel_url.query.get('crop', 'true').lower() in ('true', '1', 'yes')

        if not display_type:
            return web.json_response(
                {"status": "error", "message": "Missing required query parameter: display"},
                status=400
            )

        # Try to find the actual filename by basename
        filename = gallery.find_image_by_basename(basename)
        if not filename:
            # If not found by basename, try as full filename
            filename = basename

        # Load display configuration
        try:
            config = load_display_config(display_type)
        except FileNotFoundError:
            available = list_available_displays()
            return web.json_response(
                {
                    "status": "error",
                    "message": f"Display type '{display_type}' not found",
                    "available_displays": available
                },
                status=404
            )

        # Get original image data
        data = await gallery.get_image(filename)

        # Process image using display configuration
        params = config.to_process_image_params()

        # Create temporary files for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_file = temp_path / filename
            # Always save as PNG to avoid issues with palette mode images
            output_file = temp_path / f"processed_{Path(filename).stem}.png"

            # Write original image
            async with aiofiles.open(input_file, 'wb') as f:
                await f.write(data)

            # Process image (synchronous operation)
            process_image(
                input_path=str(input_file),
                output_path=str(output_file),
                dither=True,
                resize=True,
                crop=crop,
                **params
            )

            # Read processed image
            async with aiofiles.open(output_file, 'rb') as f:
                processed_data = await f.read()

        # Always return PNG for eink endpoint
        return web.Response(body=processed_data, content_type='image/png')

    except FileNotFoundError:
        return web.json_response(
            {"status": "error", "message": f"Image not found: {basename}"},
            status=404
        )
    except Exception as e:
        logger.error(f"Error processing eink image: {e}")
        return web.json_response(
            {"status": "error", "message": str(e)},
            status=500
        )


async def api_get_random_eink_image(gallery, request: web.Request) -> web.Response:
    """GET /api/images/eink/random - Get a random processed image for e-ink display"""
    try:
        display_type = request.rel_url.query.get('display')
        tags_param = request.rel_url.query.get('tags')

        if not display_type:
            return web.json_response(
                {"status": "error", "message": "Missing required query parameter: display"},
                status=400
            )

        # Get all images with metadata
        all_images = gallery.get_images()

        if not all_images:
            return web.json_response(
                {"status": "error", "message": "No images available in gallery"},
                status=404
            )

        # Filter by tags if provided
        if tags_param:
            # Parse comma-separated tags
            requested_tags = [tag.strip().lower() for tag in tags_param.split(',') if tag.strip()]

            # Filter images that have at least one of the requested tags
            filtered_images = []
            for img in all_images:
                # Handle both string tags and dict tags (in case they're stored as dicts)
                raw_tags = img.get('tags', [])
                img_tags = []
                for tag in raw_tags:
                    if isinstance(tag, str):
                        img_tags.append(tag.lower())
                    elif isinstance(tag, dict) and 'name' in tag:
                        img_tags.append(tag['name'].lower())
                    elif isinstance(tag, dict) and 'tag' in tag:
                        img_tags.append(tag['tag'].lower())

                if any(tag in img_tags for tag in requested_tags):
                    filtered_images.append(img)

            if not filtered_images:
                return web.json_response(
                    {
                        "status": "error",
                        "message": f"No images found with tags: {tags_param}"
                    },
                    status=404
                )

            images_to_choose_from = filtered_images
        else:
            images_to_choose_from = all_images

        # Select a random image
        selected_image = random.choice(images_to_choose_from)
        filename = selected_image['filename']

        # Load display configuration
        try:
            config = load_display_config(display_type)
        except FileNotFoundError:
            available = list_available_displays()
            return web.json_response(
                {
                    "status": "error",
                    "message": f"Display type '{display_type}' not found",
                    "available_displays": available
                },
                status=404
            )

        # Get original image data
        data = await gallery.get_image(filename)

        # Process image using display configuration
        params = config.to_process_image_params()

        # Create temporary files for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_file = temp_path / filename
            # Always save as PNG to avoid issues with palette mode images
            output_file = temp_path / f"processed_{Path(filename).stem}.png"

            # Write original image
            async with aiofiles.open(input_file, 'wb') as f:
                await f.write(data)

            # Process image (synchronous operation)
            process_image(
                input_path=str(input_file),
                output_path=str(output_file),
                dither=True,
                resize=True,
                crop=True,
                **params
            )

            # Read processed image
            async with aiofiles.open(output_file, 'rb') as f:
                processed_data = await f.read()

        # Always return PNG for eink endpoint
        # Add custom header to indicate which image was selected
        response = web.Response(body=processed_data, content_type='image/png')
        response.headers['X-Selected-Image'] = filename
        return response

    except Exception as e:
        logger.error(f"Error processing random eink image: {e}")
        return web.json_response(
            {"status": "error", "message": str(e)},
            status=500
        )


def _filter_images_by_tags(images: list, tags_param: str) -> list:
    """Helper function to filter images by tags.

    Args:
        images: List of image dictionaries
        tags_param: Comma-separated tag string

    Returns:
        List of filtered images that have at least one of the requested tags
    """
    if not tags_param:
        return images

    # Parse comma-separated tags
    requested_tags = [tag.strip().lower() for tag in tags_param.split(',') if tag.strip()]

    # Filter images that have at least one of the requested tags
    filtered_images = []
    for img in images:
        # Handle both string tags and dict tags
        raw_tags = img.get('tags', [])
        img_tags = []
        for tag in raw_tags:
            if isinstance(tag, str):
                img_tags.append(tag.lower())
            elif isinstance(tag, dict) and 'name' in tag:
                img_tags.append(tag['name'].lower())
            elif isinstance(tag, dict) and 'tag' in tag:
                img_tags.append(tag['tag'].lower())

        if any(tag in img_tags for tag in requested_tags):
            filtered_images.append(img)

    return filtered_images


async def api_get_next_eink_image(gallery, request: web.Request) -> web.Response:
    """GET /api/images/eink/next - Get next processed image for e-ink display by index

    Query parameters:
        - current_index (required): Current image index in the images table
        - display (required): Display type for processing
        - tags (optional): Comma-separated tags to filter images

    Returns:
        Processed image as PNG with X-Selected-Image and X-Image-Index headers
    """
    try:
        display_type = request.rel_url.query.get('display')
        current_index_str = request.rel_url.query.get('current_index')
        tags_param = request.rel_url.query.get('tags')

        if not display_type:
            return web.json_response(
                {"status": "error", "message": "Missing required query parameter: display"},
                status=400
            )

        if current_index_str is None:
            return web.json_response(
                {"status": "error", "message": "Missing required query parameter: current_index"},
                status=400
            )

        # Parse current index
        try:
            current_index = int(current_index_str)
        except (ValueError, TypeError):
            return web.json_response(
                {"status": "error", "message": f"Invalid current_index value: {current_index_str}"},
                status=400
            )

        # Get all images with metadata
        all_images = gallery.get_images()

        if not all_images:
            return web.json_response(
                {"status": "error", "message": "No images available in gallery"},
                status=404
            )

        # Filter by tags if provided
        if tags_param:
            images_to_choose_from = _filter_images_by_tags(all_images, tags_param)

            if not images_to_choose_from:
                return web.json_response(
                    {
                        "status": "error",
                        "message": f"No images found with tags: {tags_param}"
                    },
                    status=404
                )
        else:
            images_to_choose_from = all_images

        # Calculate next index (wrap around to 0 if at end)
        next_index = (current_index + 1) % len(images_to_choose_from)
        selected_image = images_to_choose_from[next_index]
        filename = selected_image['filename']

        # Load display configuration
        try:
            config = load_display_config(display_type)
        except FileNotFoundError:
            available = list_available_displays()
            return web.json_response(
                {
                    "status": "error",
                    "message": f"Display type '{display_type}' not found",
                    "available_displays": available
                },
                status=404
            )

        # Get original image data
        data = await gallery.get_image(filename)

        # Process image using display configuration
        params = config.to_process_image_params()

        # Create temporary files for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_file = temp_path / filename
            # Always save as PNG to avoid issues with palette mode images
            output_file = temp_path / f"processed_{Path(filename).stem}.png"

            # Write original image
            async with aiofiles.open(input_file, 'wb') as f:
                await f.write(data)

            # Process image (synchronous operation)
            process_image(
                input_path=str(input_file),
                output_path=str(output_file),
                dither=True,
                resize=True,
                crop=True,
                **params
            )

            # Read processed image
            async with aiofiles.open(output_file, 'rb') as f:
                processed_data = await f.read()

        # Always return PNG for eink endpoint
        # Add custom headers to indicate which image was selected and its index
        response = web.Response(body=processed_data, content_type='image/png')
        response.headers['X-Selected-Image'] = filename
        response.headers['X-Image-Index'] = str(next_index)
        return response

    except Exception as e:
        logger.error(f"Error processing next eink image: {e}")
        return web.json_response(
            {"status": "error", "message": str(e)},
            status=500
        )
