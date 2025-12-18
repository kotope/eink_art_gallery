#!/usr/bin/env python3
"""
E-Ink Gallery Management Service
REST API with web interface for managing images on e-ink displays
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from functools import partial

# Ensure /app is in the path for module imports
sys.path.insert(0, "/app")

from aiohttp import web
from aiohttp.web_runner import TCPSite
import aiofiles
import mimetypes

# Import local modules
from display_config_manager import DisplayConfigManager
from metadata_db import MetadataDatabase
from eink_endpoints import (
    api_get_eink_image,
    api_get_random_eink_image,
    api_get_next_eink_image,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Gallery configuration
DATA_DIR = Path("/data/eink_art")
IMAGES_DIR = DATA_DIR / "images"
CONFIG_FILE = DATA_DIR / "config.json"
METADATA_DB_FILE = DATA_DIR / "metadata.db"

# Display config manager
display_config_manager = None


class GalleryManager:
    """Manages the eink art gallery"""

    def __init__(self, images_dir: Path, port: int = 8112):
        self.images_dir = images_dir
        self.port = port
        self.images_dir.mkdir(parents=True, exist_ok=True)
        # Initialize metadata database
        self.metadata_db = MetadataDatabase(METADATA_DB_FILE)

    def find_image_by_basename(self, basename: str) -> Optional[str]:
        """Find image file by basename (without extension).

        Args:
            basename: Image basename without extension (e.g., 'photo')

        Returns:
            Full filename if found (e.g., 'photo.jpg'), None otherwise
        """
        for file_path in self.images_dir.glob("*"):
            if file_path.is_file() and self._is_image(file_path):
                if file_path.stem == basename:  # Compare without extension
                    return file_path.name
        return None

    def get_images(self) -> list:
        """Get list of all images with metadata"""
        images = []
        for file_path in sorted(self.images_dir.glob("*")):
            if file_path.name.startswith("."):
                continue
            if file_path.is_file() and self._is_image(file_path):
                meta = self.metadata_db.get_image_metadata(file_path.name)
                if meta:
                    images.append(
                        {
                            "filename": file_path.name,
                            "size": file_path.stat().st_size,
                            "uploaded": meta.get(
                                "uploaded_at",
                                datetime.fromtimestamp(
                                    file_path.stat().st_ctime
                                ).isoformat(),
                            ),
                            "title": meta.get("title", ""),
                            "description": meta.get("description", ""),
                            "tags": meta.get("tags", []),
                            "url": f"/api/images/{file_path.name}",
                        }
                    )
                else:
                    # Image exists but not in database, add it
                    self.metadata_db.add_image(
                        file_path.name,
                        datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                    )
                    images.append(
                        {
                            "filename": file_path.name,
                            "size": file_path.stat().st_size,
                            "uploaded": datetime.fromtimestamp(
                                file_path.stat().st_ctime
                            ).isoformat(),
                            "title": "",
                            "description": "",
                            "tags": [],
                            "url": f"/api/images/{file_path.name}",
                        }
                    )
        return images

    def _is_image(self, file_path: Path) -> bool:
        """Check if file is a valid image"""
        valid_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
        return file_path.suffix.lower() in valid_extensions

    async def upload_image(self, filename: str, data: bytes, title: str = "") -> bool:
        """Upload an image file"""
        if not self._is_image(Path(filename)):
            raise ValueError("Invalid image format")

        file_path = self.images_dir / filename
        try:
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(data)

            # Add to metadata database
            self.metadata_db.add_image(
                filename, datetime.now().isoformat(), title=title
            )

            # Remove 'latest' tag from all other images
            self.metadata_db.remove_tag_from_all_images("latest")

            # Add 'latest' tag to the newly uploaded image
            self.metadata_db.add_tag(filename, "latest")

            logger.info(f"Image uploaded: {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload image: {e}")
            raise

    async def delete_image(self, filename: str) -> bool:
        """Delete an image"""
        file_path = self.images_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Image not found: {filename}")

        try:
            file_path.unlink()
            # Remove from metadata database
            self.metadata_db.remove_image(filename)
            logger.info(f"Image deleted: {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete image: {e}")
            raise

    async def get_image(self, filename: str) -> bytes:
        """Get image data"""
        file_path = self.images_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Image not found: {filename}")

        try:
            async with aiofiles.open(file_path, "rb") as f:
                return await f.read()
        except Exception as e:
            logger.error(f"Failed to read image: {e}")
            raise


# Global gallery manager
gallery = None


async def handle_index(request: web.Request) -> web.Response:
    """Serve the web interface"""
    html_file = Path(__file__).parent / "templates" / "index.html"
    try:
        with open(html_file, "r") as f:
            html = f.read()
        return web.Response(text=html, content_type="text/html")
    except Exception as e:
        logger.error(f"Failed to load index.html: {e}")
        return web.Response(text="Error loading interface", status=500)


async def api_get_images(request: web.Request) -> web.Response:
    """GET /api/images - Get list of all images"""
    try:
        images = gallery.get_images()
        return web.json_response({"status": "success", "images": images})
    except Exception as e:
        logger.error(f"Error getting images: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def api_upload_image(request: web.Request) -> web.Response:
    """POST /api/images/upload - Upload an image"""
    try:
        reader = await request.multipart()
        field = await reader.next()

        if field.name != "file":
            return web.json_response(
                {"status": "error", "message": "Missing 'file' field"}, status=400
            )

        filename = field.filename
        title = request.rel_url.query.get("title", "")

        data = await field.read()
        await gallery.upload_image(filename, data, title)

        return web.json_response(
            {
                "status": "success",
                "message": f"Image '{filename}' uploaded successfully",
                "filename": filename,
            }
        )
    except ValueError as e:
        return web.json_response({"status": "error", "message": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def api_delete_image(request: web.Request) -> web.Response:
    """DELETE /api/images/{filename} - Delete an image (filename can be basename without extension)"""
    try:
        basename = request.match_info.get("filename")
        # Try to find the actual filename by basename
        filename = gallery.find_image_by_basename(basename)
        if not filename:
            # If not found by basename, try as full filename
            filename = basename

        await gallery.delete_image(filename)
        return web.json_response(
            {"status": "success", "message": f"Image '{filename}' deleted successfully"}
        )
    except FileNotFoundError as e:
        return web.json_response({"status": "error", "message": str(e)}, status=404)
    except Exception as e:
        logger.error(f"Error deleting image: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def api_get_image(request: web.Request) -> web.Response:
    """GET /api/images/{filename} - Get a specific image (filename can be basename without extension)"""
    try:
        basename = request.match_info.get("filename")
        # Try to find the actual filename by basename
        filename = gallery.find_image_by_basename(basename)
        if not filename:
            # If not found by basename, try as full filename
            filename = basename

        data = await gallery.get_image(filename)

        # Determine content type
        file_path = gallery.images_dir / filename
        content_type, _ = mimetypes.guess_type(str(file_path))
        if not content_type:
            content_type = "application/octet-stream"

        return web.Response(body=data, content_type=content_type)
    except FileNotFoundError:
        return web.json_response(
            {"status": "error", "message": f"Image not found: {basename}"}, status=404
        )
    except Exception as e:
        logger.error(f"Error getting image: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def api_get_status(request: web.Request) -> web.Response:
    """GET /api/status - Get gallery status"""
    try:
        images = gallery.get_images()
        return web.json_response(
            {
                "status": "success",
                "running": True,
                "port": gallery.port,
                "total_images": len(images),
                "data_dir": str(gallery.images_dir),
            }
        )
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def api_get_image_metadata(request: web.Request) -> web.Response:
    """GET /api/metadata/{filename} - Get metadata for a specific image"""
    try:
        basename = request.match_info.get("filename")
        # Try to find the actual filename by basename
        filename = gallery.find_image_by_basename(basename)
        if not filename:
            filename = basename

        meta = gallery.metadata_db.get_image_metadata(filename)
        if not meta:
            return web.json_response(
                {"status": "error", "message": f"Image not found: {filename}"},
                status=404,
            )

        return web.json_response({"status": "success", "metadata": meta})
    except Exception as e:
        logger.error(f"Error getting image metadata: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def api_update_image_metadata(request: web.Request) -> web.Response:
    """PUT /api/metadata/{filename} - Update image title and description"""
    try:
        basename = request.match_info.get("filename")
        # Try to find the actual filename by basename
        filename = gallery.find_image_by_basename(basename)
        if not filename:
            filename = basename

        data = await request.json()
        title = data.get("title")
        description = data.get("description")

        if not gallery.metadata_db.update_image_metadata(filename, title, description):
            return web.json_response(
                {
                    "status": "error",
                    "message": f"Failed to update metadata for {filename}",
                },
                status=500,
            )

        meta = gallery.metadata_db.get_image_metadata(filename)
        return web.json_response(
            {
                "status": "success",
                "message": "Metadata updated successfully",
                "metadata": meta,
            }
        )
    except Exception as e:
        logger.error(f"Error updating image metadata: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def api_add_tag(request: web.Request) -> web.Response:
    """POST /api/metadata/{filename}/tags - Add a tag to an image"""
    try:
        basename = request.match_info.get("filename")
        # Try to find the actual filename by basename
        filename = gallery.find_image_by_basename(basename)
        if not filename:
            filename = basename

        data = await request.json()
        tag_name = data.get("tag")

        if not tag_name:
            return web.json_response(
                {"status": "error", "message": "Missing 'tag' field"}, status=400
            )

        if not gallery.metadata_db.add_tag(filename, tag_name):
            return web.json_response(
                {"status": "error", "message": f"Failed to add tag to {filename}"},
                status=500,
            )

        meta = gallery.metadata_db.get_image_metadata(filename)
        return web.json_response(
            {
                "status": "success",
                "message": f"Tag '{tag_name}' added successfully",
                "metadata": meta,
            }
        )
    except Exception as e:
        logger.error(f"Error adding tag: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def api_remove_tag(request: web.Request) -> web.Response:
    """DELETE /api/metadata/{filename}/tags/{tag_name} - Remove a tag from an image"""
    try:
        basename = request.match_info.get("filename")
        tag_name = request.match_info.get("tag_name")

        # Try to find the actual filename by basename
        filename = gallery.find_image_by_basename(basename)
        if not filename:
            filename = basename

        if not gallery.metadata_db.remove_tag(filename, tag_name):
            return web.json_response(
                {"status": "error", "message": f"Failed to remove tag from {filename}"},
                status=500,
            )

        meta = gallery.metadata_db.get_image_metadata(filename)
        return web.json_response(
            {
                "status": "success",
                "message": f"Tag '{tag_name}' removed successfully",
                "metadata": meta,
            }
        )
    except Exception as e:
        logger.error(f"Error removing tag: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def api_get_all_tags(request: web.Request) -> web.Response:
    """GET /api/tags - Get all available tags"""
    try:
        tags = gallery.metadata_db.get_all_tags()
        return web.json_response({"status": "success", "tags": tags})
    except Exception as e:
        logger.error(f"Error getting all tags: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


# Display Configuration Management Endpoints


async def api_list_displays(request: web.Request) -> web.Response:
    """GET /api/displays - List all available displays"""
    try:
        displays = display_config_manager.list_displays()
        return web.json_response({"status": "success", "displays": displays})
    except Exception as e:
        logger.error(f"Error listing displays: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def api_get_display_config(request: web.Request) -> web.Response:
    """GET /api/displays/{display_name}/config - Get display configuration as YAML"""
    try:
        display_name = request.match_info.get("display_name")
        content = display_config_manager.load_display_config(display_name)

        return web.json_response(
            {"status": "success", "display_name": display_name, "content": content}
        )
    except FileNotFoundError as e:
        return web.json_response({"status": "error", "message": str(e)}, status=404)
    except Exception as e:
        logger.error(f"Error getting display config: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def api_save_display_config(request: web.Request) -> web.Response:
    """PUT /api/displays/{display_name}/config - Save display configuration"""
    try:
        display_name = request.match_info.get("display_name")
        data = await request.json()
        yaml_content = data.get("content", "")

        if not yaml_content:
            return web.json_response(
                {"status": "error", "message": "Missing 'content' field"}, status=400
            )

        result = display_config_manager.save_display_config(display_name, yaml_content)
        return web.json_response(result)
    except ValueError as e:
        return web.json_response({"status": "error", "message": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error saving display config: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def api_reset_display_config(request: web.Request) -> web.Response:
    """POST /api/displays/{display_name}/reset - Reset display config to default"""
    try:
        display_name = request.match_info.get("display_name")
        result = display_config_manager.reset_display_config(display_name)
        return web.json_response(result)
    except FileNotFoundError as e:
        return web.json_response({"status": "error", "message": str(e)}, status=404)
    except Exception as e:
        logger.error(f"Error resetting display config: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def api_duplicate_display_config(request: web.Request) -> web.Response:
    """POST /api/displays/{display_name}/duplicate - Duplicate a display config"""
    try:
        source_name = request.match_info.get("display_name")
        data = await request.json()
        new_name = data.get("new_name", "")

        if not new_name:
            return web.json_response(
                {"status": "error", "message": "Missing 'new_name' field"}, status=400
            )

        result = display_config_manager.duplicate_display_config(source_name, new_name)
        return web.json_response(result)
    except (FileNotFoundError, ValueError) as e:
        return web.json_response({"status": "error", "message": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error duplicating display config: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def api_delete_display_config(request: web.Request) -> web.Response:
    """DELETE /api/displays/{display_name} - Delete a custom display config"""
    try:
        display_name = request.match_info.get("display_name")
        result = display_config_manager.delete_display_config(display_name)
        return web.json_response(result)
    except FileNotFoundError as e:
        return web.json_response({"status": "error", "message": str(e)}, status=404)
    except Exception as e:
        logger.error(f"Error deleting display config: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def api_export_display_config(request: web.Request) -> web.Response:
    """GET /api/displays/{display_name}/export - Export display config as YAML file"""
    try:
        display_name = request.match_info.get("display_name")
        filename, content = display_config_manager.export_display_config(display_name)

        return web.Response(
            body=content.encode("utf-8"),
            content_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except FileNotFoundError as e:
        return web.json_response({"status": "error", "message": str(e)}, status=404)
    except Exception as e:
        logger.error(f"Error exporting display config: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def api_import_display_config(request: web.Request) -> web.Response:
    """POST /api/displays/import - Import a display config from YAML"""
    try:
        reader = await request.multipart()

        filename = None
        content = None

        async for field in reader:
            if field.name == "file":
                filename = field.filename
                content = (await field.read()).decode("utf-8")

        if not filename or not content:
            return web.json_response(
                {"status": "error", "message": "Missing 'file' field"}, status=400
            )

        overwrite = request.rel_url.query.get("overwrite", "false").lower() in (
            "true",
            "1",
            "yes",
        )
        result = display_config_manager.import_display_config(
            filename, content, overwrite=overwrite
        )
        return web.json_response(result)
    except FileExistsError as e:
        return web.json_response({"status": "error", "message": str(e)}, status=409)
    except ValueError as e:
        return web.json_response({"status": "error", "message": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error importing display config: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def create_app(port: int = 8112) -> web.Application:
    """Create and configure the aiohttp application"""
    app = web.Application()

    # Routes
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/status", api_get_status)
    app.router.add_get("/api/images", api_get_images)
    app.router.add_post("/api/images/upload", api_upload_image)

    # Create eink resource to handle sub-routes in correct order
    # Note: In aiohttp, literal paths and parameterized paths at same level have conflicts
    # We need to register them with explicit resource handling
    eink_res = app.router.add_resource("/api/images/eink/random")
    eink_res.add_route("GET", partial(api_get_random_eink_image, gallery))

    eink_next_res = app.router.add_resource("/api/images/eink/next")
    eink_next_res.add_route("GET", partial(api_get_next_eink_image, gallery))

    eink_file_res = app.router.add_resource("/api/images/eink/{filename}")
    eink_file_res.add_route("GET", partial(api_get_eink_image, gallery))

    # Generic image routes
    img_res = app.router.add_resource("/api/images/{filename}")
    img_res.add_route("GET", api_get_image)
    img_res.add_route("DELETE", api_delete_image)

    # Metadata routes
    app.router.add_get("/api/metadata/{filename}", api_get_image_metadata)
    app.router.add_put("/api/metadata/{filename}", api_update_image_metadata)
    app.router.add_post("/api/metadata/{filename}/tags", api_add_tag)
    app.router.add_delete("/api/metadata/{filename}/tags/{tag_name}", api_remove_tag)
    app.router.add_get("/api/tags", api_get_all_tags)

    # Display configuration routes
    app.router.add_get("/api/displays", api_list_displays)
    app.router.add_get("/api/displays/{display_name}/config", api_get_display_config)
    app.router.add_put("/api/displays/{display_name}/config", api_save_display_config)
    app.router.add_post("/api/displays/{display_name}/reset", api_reset_display_config)
    app.router.add_post(
        "/api/displays/{display_name}/duplicate", api_duplicate_display_config
    )
    app.router.add_delete("/api/displays/{display_name}", api_delete_display_config)
    app.router.add_get("/api/displays/{display_name}/export", api_export_display_config)
    app.router.add_post("/api/displays/import", api_import_display_config)

    # Serve static files (CSS, JS, etc.)
    static_path = Path(__file__).parent / "static"
    app.router.add_static("/static/", path=str(static_path), name="static")

    # Serve templates files
    templates_path = Path(__file__).parent / "templates"
    app.router.add_static("/templates/", path=str(templates_path), name="templates")

    return app


async def main():
    """Main entry point"""
    global gallery, display_config_manager

    # Read configuration from environment or config file
    port_str = os.getenv("PORT", "8112")

    # Handle 'null' string or empty values
    if not port_str or port_str == "null":
        port_str = "8112"

    port = int(port_str)

    logger.info(f"Starting E-Ink Gallery Service on port {port}")

    # Initialize gallery manager and display config manager FIRST
    gallery = GalleryManager(IMAGES_DIR, port)
    display_config_manager = DisplayConfigManager()

    # Create and start the application
    app = await create_app(port)
    runner = web.AppRunner(app)
    await runner.setup()

    # Start both IPv4 and IPv6 sites
    site_v4 = TCPSite(runner, "0.0.0.0", port)
    await site_v4.start()

    site_v6 = TCPSite(runner, "::", port)
    await site_v6.start()

    logger.info(f"E-Ink Gallery Service is running on port {port}")
    logger.info(f"  IPv4: http://0.0.0.0:{port}")
    logger.info(f"  IPv6: http://[::1]:{port}")
    logger.info(f"Images directory: {IMAGES_DIR}")

    # Keep the server running
    try:
        await asyncio.sleep(3600 * 24)  # Sleep for a day
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
