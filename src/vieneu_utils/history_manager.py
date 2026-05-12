"""
History manager for VieNeu-TTS generation history.
Manages persistent storage of audio generations with metadata.
"""

import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


class HistoryManager:
    """Manages generation history with JSON persistence and audio file management."""

    def __init__(self, history_dir: str = "history_data", max_items: int = 50):
        """
        Initialize history manager.

        Args:
            history_dir: Root directory for history storage
            max_items: Maximum number of history items to keep
        """
        self.history_dir = Path(history_dir)
        self.audio_dir = self.history_dir / "audio"
        self.json_path = self.history_dir / "history.json"
        self.max_items = max_items
        self.items = []

        # Create directories if not exist
        self.audio_dir.mkdir(parents=True, exist_ok=True)

        # Load existing history
        self.load_from_disk()

    def add_item(self,
                 text: str,
                 voice_name: str,
                 voice_id: str,
                 mode: str,
                 temp_audio_path: str,
                 duration_seconds: float,
                 generation_time: float,
                 backend: str,
                 model: str) -> dict:
        """
        Add new generation to history.

        Args:
            text: Input text (will be truncated to 200 chars)
            voice_name: Display name of voice
            voice_id: Internal voice ID
            mode: "preset_mode" or "custom_mode"
            temp_audio_path: Path to temporary audio file
            duration_seconds: Audio duration
            generation_time: Time taken to generate
            backend: "LMDeploy" or "Standard"
            model: Model name used

        Returns:
            dict: The created history item with permanent audio path
        """
        # Generate unique ID and timestamp
        item_id = self._generate_id()
        timestamp = self._format_timestamp()

        # Truncate text if too long (100 chars instead of 200)
        display_text = text[:100]
        if len(text) > 100:
            display_text += "..."

        # Copy audio to permanent location
        audio_path = self._copy_audio_to_permanent(temp_audio_path, item_id, timestamp)

        # Create history item
        item = {
            "id": item_id,
            "timestamp": timestamp,
            "text": display_text,
            "voice_name": voice_name,
            "voice_id": voice_id,
            "mode": mode,
            "audio_path": str(audio_path.resolve()),  # Use absolute path
            "duration_seconds": duration_seconds,
            "generation_time": generation_time,
            "backend": backend,
            "model": model
        }

        # Add to beginning of list (newest first)
        self.items.insert(0, item)

        # Enforce limit
        self._enforce_limit()

        # Save to disk
        self.save_to_disk()

        return item

    def get_all_items(self) -> list:
        """Get all history items, newest first."""
        return self.items.copy()

    def load_from_disk(self) -> list:
        """Load history from JSON file."""
        if not self.json_path.exists():
            self.items = []
            return []

        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.items = data.get("items", [])
                return self.items
        except Exception as e:
            print(f"⚠️ Failed to load history: {e}")
            self.items = []
            return []

    def save_to_disk(self) -> None:
        """Save current history to JSON file."""
        try:
            data = {
                "version": "1.0",
                "max_items": self.max_items,
                "items": self.items
            }

            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save history: {e}")

    def delete_item(self, item_id: str) -> bool:
        """
        Delete a history item and its audio file.

        Args:
            item_id: ID of item to delete

        Returns:
            bool: True if deleted, False if not found
        """
        for i, item in enumerate(self.items):
            if item["id"] == item_id:
                # Delete audio file
                audio_path = Path(item["audio_path"])
                if audio_path.exists():
                    try:
                        audio_path.unlink()
                    except Exception as e:
                        print(f"⚠️ Failed to delete audio file: {e}")

                # Remove from list
                self.items.pop(i)

                # Save to disk
                self.save_to_disk()

                return True

        return False

    def clear_all(self) -> None:
        """Clear all history items and audio files."""
        # Delete all audio files
        for item in self.items:
            audio_path = Path(item["audio_path"])
            if audio_path.exists():
                try:
                    audio_path.unlink()
                except Exception as e:
                    print(f"⚠️ Failed to delete audio file: {e}")

        # Clear items
        self.items = []

        # Save to disk
        self.save_to_disk()

    def _copy_audio_to_permanent(self, temp_path: str, item_id: str, timestamp: str) -> Path:
        """
        Copy temp audio to permanent storage with organized naming.

        Args:
            temp_path: Path to temporary audio file
            item_id: Unique item ID
            timestamp: Timestamp string

        Returns:
            Path: Path to permanent audio file
        """
        # Create filename: YYYYMMDD_HHMMSS_uuid.wav
        timestamp_clean = timestamp.replace(":", "").replace("-", "").replace(" ", "_")
        filename = f"{timestamp_clean}_{item_id[:8]}.wav"
        dest_path = self.audio_dir / filename

        # Copy file
        try:
            shutil.copy2(temp_path, dest_path)
        except Exception as e:
            print(f"⚠️ Failed to copy audio file: {e}")
            # Return temp path as fallback
            return Path(temp_path)

        return dest_path

    def _enforce_limit(self) -> None:
        """Remove oldest items if exceeding max_items limit."""
        while len(self.items) > self.max_items:
            # Remove oldest item (last in list)
            old_item = self.items.pop()

            # Delete its audio file
            audio_path = Path(old_item["audio_path"])
            if audio_path.exists():
                try:
                    audio_path.unlink()
                except Exception as e:
                    print(f"⚠️ Failed to delete old audio file: {e}")

    def _generate_id(self) -> str:
        """Generate unique ID for history item."""
        return str(uuid.uuid4())

    def _format_timestamp(self) -> str:
        """Generate formatted timestamp string."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
