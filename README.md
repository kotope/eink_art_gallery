# E-Ink Art Gallery

A standalone Docker-based application for managing and displaying images for e-ink displays. This is a web-based gallery manager with a REST API for providing images for e-ink displays.

**Disclaimer** This application is in beta stage and was developed rapidly with a focus on personal use. A lot of of vibe coding was used :-)
This beta version does not have any authentication in place, so please don't expose your eink art gallery interface to outside your local network.

## Features

- **Web-based Gallery Management UI** - Intuitive interface for managing your image collection
- **REST API** - Full-featured API for programmatic control
- **Display Configuration** - YAML-based configuration system for different e-ink display models
- **Metadata Management** - SQLite-based metadata tracking for images
- **Image Optimization** - Automatic image processing for e-ink displays
- **Docker Ready** - Easy deployment with Docker and Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Port 8112 available (or modify in docker-compose.yml)

### Running with Docker Compose

```bash
docker-compose up -d
```

The application will be available at `http://localhost:8112`

### Building and Running Manually

```bash
docker build -t eink-art-gallery .
docker run -p 8112:8112 -v eink_data:/data/eink_art eink-art-gallery
```

### Running Locally (Development)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create data directory
mkdir -p /data/eink_art/images

# Run application
export PORT=8112
python3 app.py
```

## Configuration

### Port Configuration

The application runs on port `8112` by default. To change this:

**With Docker Compose:**
Edit `docker-compose.yml` and modify:

```yaml
ports:
  - "YOUR_PORT:8112"
environment:
  - PORT=YOUR_PORT
```

**With Environment Variable:**

```bash
docker run -p 8080:8112 -e PORT=8112 eink-art-gallery
```

### Data Directory

Images and metadata are stored in `/data/eink_art/`:

- `images/` - Directory for image files
- `metadata.db` - SQLite database for image metadata
- `config.json` - Application configuration

When using Docker Compose, data is persisted in the `eink_data` volume.

### Display Configuration

Display configurations are located in the `displays/` directory. Each YAML file defines:

- Display resolution
- Color mode (monochrome, grayscale, color)
- Supported image formats
- Specific hardware parameters

Example: `displays/7.3inch_eink_spectra_6.yaml`

## Web Interface

Access the web interface at `http://localhost:8112`

### Main Features:

1. **Gallery View** - Browse and manage your image collection
2. **Image Upload** - Add new images to the gallery
3. **Display Settings** - Configure display parameters
4. **Image Preview** - See how images will appear on your display

## API Endpoints

### Image Management

- `GET /api/images` - List all images
- `GET /api/images/<image_id>` - Get image details
- `POST /api/images/upload` - Upload new image
- `DELETE /api/images/<image_id>` - Delete image

### Display Control

- `GET /api/eink/image` - Get current display image
- `GET /api/eink/random` - Get random image
- `GET /api/eink/next` - Get next image in sequence
- `POST /api/eink/display` - Display specific image

### Configuration

- `GET /api/config` - Get configuration
- `POST /api/config` - Update configuration
- `GET /api/displays` - List available display configurations


## Dependencies

- **aiohttp** - Async web framework
- **aiofiles** - Async file operations
- **Pillow** - Image processing
- **PyYAML** - YAML configuration parsing
- **NumPy** - Numerical operations for image processing

See `requirements.txt` for specific versions.

## Development

### Setup Development Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running Tests

```bash
python3 -m pytest tests/
```

### Code Style

The project follows PEP 8 conventions. Use `black` and `flake8` for code formatting and linting.

## Docker Image Details

- **Base Image**: `python:3.11-slim`
- **Working Directory**: `/app`
- **Data Directory**: `/data/eink_art` (should be mounted as volume)
- **Exposed Port**: 8112

### Volume Mounts

Mount `/data/eink_art` to persist images and metadata:

```bash
docker run -v /path/to/local/data:/data/eink_art eink-art-gallery
```

## Troubleshooting

### Port Already in Use

If port 8112 is already in use:

```bash
docker run -p 8080:8112 eink-art-gallery
# Access at http://localhost:8080
```

### Permission Issues

If you encounter permission issues with the data directory:

```bash
chmod -R 755 /path/to/data
```

### Container Won't Start

Check logs:

```bash
docker logs eink-art-gallery
```

### Database Locked

If you get "database is locked" errors, ensure only one instance is running:

```bash
docker ps | grep eink-art-gallery
docker stop eink-art-gallery
```

## Performance Optimization

- Use SSD storage for better performance
- For multiple displays, consider running multiple container instances
- Images are automatically optimized for e-ink displays on upload

## License

MIT License (see LICENSE file)

## Support
[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/tokorhon)

For issues and feature requests, please open an issue on the project repository.
