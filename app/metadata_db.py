#!/usr/bin/env python3
"""
Metadata database module for managing image tags and metadata using SQLite
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class MetadataDatabase:
    """SQLite database for managing image metadata and tags"""

    def __init__(self, db_path: Path):
        """Initialize the metadata database.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema if it doesn't exist"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Create images metadata table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE NOT NULL,
                    title TEXT DEFAULT '',
                    description TEXT DEFAULT '',
                    uploaded_at TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create tags table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tags (
                    tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create image_tags association table (many-to-many)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS image_tags (
                    image_filename TEXT NOT NULL,
                    tag_id INTEGER NOT NULL,
                    added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (image_filename, tag_id),
                    FOREIGN KEY (image_filename) REFERENCES images(filename) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE
                )
            ''')

            # Create indices for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_images_id ON images(id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_images_filename ON images(filename)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_images_uploaded_at ON images(uploaded_at)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_image_tags_filename ON image_tags(image_filename)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_image_tags_tag_id ON image_tags(tag_id)
            ''')

            conn.commit()
            conn.close()
            logger.info(f"Metadata database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize metadata database: {e}")
            raise

    def add_image(self, filename: str, uploaded_at: str, title: str = "", description: str = "") -> bool:
        """Add a new image to the metadata database.

        Args:
            filename: Image filename
            uploaded_at: ISO format datetime string when image was uploaded
            title: Optional image title
            description: Optional image description

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO images (filename, title, description, uploaded_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (filename, title, description, uploaded_at, datetime.now().isoformat()))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to add image {filename} to metadata: {e}")
            return False

    def remove_image(self, filename: str) -> bool:
        """Remove an image and its metadata from the database.

        Args:
            filename: Image filename

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Delete image and associated tags (cascading)
            cursor.execute('DELETE FROM images WHERE filename = ?', (filename,))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to remove image {filename} from metadata: {e}")
            return False

    def get_image_metadata(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific image.

        Args:
            filename: Image filename

        Returns:
            Dictionary with image metadata including tags, or None if not found
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Get image metadata
            cursor.execute('''
                SELECT filename, title, description, uploaded_at, created_at, updated_at
                FROM images
                WHERE filename = ?
            ''', (filename,))

            row = cursor.fetchone()
            if not row:
                return None

            # Get tags for this image
            cursor.execute('''
                SELECT t.tag_id, t.name
                FROM tags t
                JOIN image_tags it ON t.tag_id = it.tag_id
                WHERE it.image_filename = ?
                ORDER BY t.name
            ''', (filename,))

            tags = [{"tag_id": tag[0], "name": tag[1]} for tag in cursor.fetchall()]

            conn.close()
            return {
                "filename": row[0],
                "title": row[1],
                "description": row[2],
                "uploaded_at": row[3],
                "created_at": row[4],
                "updated_at": row[5],
                "tags": tags
            }
        except Exception as e:
            logger.error(f"Failed to get metadata for {filename}: {e}")
            return None

    def update_image_metadata(self, filename: str, title: str = None, description: str = None) -> bool:
        """Update image metadata (title and description).

        Args:
            filename: Image filename
            title: New title (if None, not updated)
            description: New description (if None, not updated)

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Build update query dynamically
            updates = ["updated_at = ?"]
            params = [datetime.now().isoformat()]

            if title is not None:
                updates.append("title = ?")
                params.append(title)

            if description is not None:
                updates.append("description = ?")
                params.append(description)

            params.append(filename)

            query = f"UPDATE images SET {', '.join(updates)} WHERE filename = ?"
            cursor.execute(query, params)

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to update metadata for {filename}: {e}")
            return False

    def add_tag(self, filename: str, tag_name: str) -> bool:
        """Add a tag to an image.

        Args:
            filename: Image filename
            tag_name: Tag name to add

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Insert or get tag
            cursor.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (tag_name,))

            # Get tag_id
            cursor.execute('SELECT tag_id FROM tags WHERE name = ?', (tag_name,))
            tag_id = cursor.fetchone()[0]

            # Add association
            cursor.execute(
                'INSERT OR IGNORE INTO image_tags (image_filename, tag_id) VALUES (?, ?)',
                (filename, tag_id)
            )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to add tag '{tag_name}' to {filename}: {e}")
            return False

    def remove_tag(self, filename: str, tag_name: str) -> bool:
        """Remove a tag from an image.

        Args:
            filename: Image filename
            tag_name: Tag name to remove

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Get tag_id
            cursor.execute('SELECT tag_id FROM tags WHERE name = ?', (tag_name,))
            result = cursor.fetchone()

            if not result:
                return False

            tag_id = result[0]

            # Remove association
            cursor.execute('DELETE FROM image_tags WHERE image_filename = ? AND tag_id = ?', (filename, tag_id))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to remove tag '{tag_name}' from {filename}: {e}")
            return False

    def remove_tag_from_all_images(self, tag_name: str) -> bool:
        """Remove a tag from all images.

        Args:
            tag_name: Tag name to remove from all images

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Get tag_id
            cursor.execute('SELECT tag_id FROM tags WHERE name = ?', (tag_name,))
            result = cursor.fetchone()

            if not result:
                return False

            tag_id = result[0]

            # Remove associations for this tag from all images
            cursor.execute('DELETE FROM image_tags WHERE tag_id = ?', (tag_id,))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to remove tag '{tag_name}' from all images: {e}")
            return False

    def get_all_tags(self) -> List[Dict[str, Any]]:
        """Get all available tags in the system.

        Returns:
            List of tag dictionaries with id and name
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute('''
                SELECT t.tag_id, t.name, COUNT(it.image_filename) as usage_count
                FROM tags t
                LEFT JOIN image_tags it ON t.tag_id = it.tag_id
                GROUP BY t.tag_id, t.name
                ORDER BY t.name
            ''')

            result = [{"tag_id": row[0], "name": row[1], "usage_count": row[2]} for row in cursor.fetchall()]
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Failed to get all tags: {e}")
            return []

    def get_images_by_tag(self, tag_name: str) -> List[str]:
        """Get all images with a specific tag.

        Args:
            tag_name: Tag name to search for

        Returns:
            List of filenames that have this tag
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute('''
                SELECT DISTINCT it.image_filename
                FROM image_tags it
                JOIN tags t ON it.tag_id = t.tag_id
                WHERE t.name = ?
                ORDER BY it.image_filename
            ''', (tag_name,))

            result = [row[0] for row in cursor.fetchall()]
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Failed to get images by tag '{tag_name}': {e}")
            return []

    def search_images(self, query: str) -> List[str]:
        """Search images by title, description, or tags.

        Args:
            query: Search query string

        Returns:
            List of matching filenames
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            search_pattern = f"%{query}%"

            cursor.execute('''
                SELECT DISTINCT i.filename
                FROM images i
                LEFT JOIN image_tags it ON i.filename = it.image_filename
                LEFT JOIN tags t ON it.tag_id = t.tag_id
                WHERE i.title LIKE ? OR i.description LIKE ? OR t.name LIKE ?
                ORDER BY i.filename
            ''', (search_pattern, search_pattern, search_pattern))

            result = [row[0] for row in cursor.fetchall()]
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Failed to search images with query '{query}': {e}")
            return []

    def get_all_images_metadata(self) -> List[Dict[str, Any]]:
        """Get metadata for all images.

        Returns:
            List of image metadata dictionaries
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute('''
                SELECT filename, title, description, uploaded_at, created_at, updated_at
                FROM images
                ORDER BY filename
            ''')

            images = []
            for row in cursor.fetchall():
                # Get tags for each image
                cursor.execute('''
                    SELECT t.tag_id, t.name
                    FROM tags t
                    JOIN image_tags it ON t.tag_id = it.tag_id
                    WHERE it.image_filename = ?
                    ORDER BY t.name
                ''', (row[0],))

                tags = [{"tag_id": tag[0], "name": tag[1]} for tag in cursor.fetchall()]

                images.append({
                    "filename": row[0],
                    "title": row[1],
                    "description": row[2],
                    "uploaded_at": row[3],
                    "created_at": row[4],
                    "updated_at": row[5],
                    "tags": tags
                })

            conn.close()
            return images
        except Exception as e:
            logger.error(f"Failed to get all images metadata: {e}")
            return []
