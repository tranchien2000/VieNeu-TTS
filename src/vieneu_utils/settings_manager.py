"""
Settings manager for VieNeu-TTS UI.
Persists user preferences across sessions.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger("VieNeu.Settings")


class SettingsManager:
    """Manages persistent UI settings with smart merging."""

    VERSION = "1.0.0"  # Settings schema version

    def __init__(self, settings_file: str = "vieneu_settings.json"):
        """
        Initialize settings manager.

        Args:
            settings_file: Path to settings file (relative to user home or absolute)
        """
        # Store in user's home directory
        if Path(settings_file).is_absolute():
            self.settings_path = Path(settings_file)
        else:
            self.settings_path = Path.home() / ".vieneu" / settings_file

        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings = self.load()

    def load(self) -> Dict[str, Any]:
        """
        Load settings from disk with smart merging.

        - If file exists: merge with defaults (user values take precedence)
        - If file doesn't exist: use defaults
        - If file is corrupted: backup and use defaults
        """
        defaults = self._default_settings()

        if not self.settings_path.exists():
            logger.info(f"Settings file not found. Creating with defaults: {self.settings_path}")
            # Save defaults on first run
            self.settings = defaults.copy()
            self.save()
            return self.settings

        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                user_settings = json.load(f)

            # Validate version (for future migrations)
            file_version = user_settings.get("_version", "1.0.0")

            # Smart merge: defaults + user overrides
            merged = defaults.copy()

            # Only override with user values that exist
            for key, value in user_settings.items():
                if key.startswith("_"):  # Skip metadata keys
                    continue
                merged[key] = value

            # Add version metadata
            merged["_version"] = self.VERSION
            merged["_last_loaded"] = self._get_timestamp()

            logger.info(f"✅ Loaded settings from: {self.settings_path}")
            logger.debug(f"Merged settings: {merged}")

            return merged

        except json.JSONDecodeError as e:
            logger.error(f"⚠️ Settings file corrupted: {e}")
            # Backup corrupted file
            backup_path = self.settings_path.with_suffix('.json.backup')
            try:
                self.settings_path.rename(backup_path)
                logger.info(f"Backed up corrupted file to: {backup_path}")
            except Exception:
                pass
            return defaults

        except Exception as e:
            logger.error(f"⚠️ Failed to load settings: {e}")
            return defaults

    def save(self):
        """Save settings to disk with metadata."""
        try:
            # Add metadata
            save_data = self.settings.copy()
            save_data["_version"] = self.VERSION
            save_data["_last_saved"] = self._get_timestamp()

            # Atomic write: write to temp file then rename
            temp_path = self.settings_path.with_suffix('.json.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_path.replace(self.settings_path)

            logger.debug(f"💾 Saved settings to: {self.settings_path}")

        except Exception as e:
            logger.error(f"⚠️ Failed to save settings: {e}")

    def _default_settings(self) -> Dict[str, Any]:
        """Return default settings (without metadata)."""
        return {
            # Generation parameters
            "temperature": 0.7,
            "max_chars_chunk": 256,
            "top_p": 1.0,
            "repetition_penalty": 1.0,

            # Processing settings
            "spell_check_level": "Tắt",
            "generation_mode": "Sequential (Từng đoạn)",
            "use_batch": False,
            "max_batch_size": 16,

            # Voice settings
            "last_voice_id": None,
            "last_voice_name": None,

            # Audiobook settings
            "audiobook_split_mode": "Tự động phát hiện chương",
            "audiobook_output_mode": "Single file",
            "audiobook_spell_check_level": "Tắt",
            "audiobook_words_per_chunk": 100,

            # Model settings (read-only, for display)
            "last_backbone": None,
            "last_codec": None,
            "last_device": None,
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.

        Args:
            key: Setting key
            default: Default value if key doesn't exist

        Returns:
            Setting value or default
        """
        # Skip metadata keys
        if key.startswith("_"):
            return None
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        """
        Set a setting value and save immediately.

        Args:
            key: Setting key
            value: Setting value
        """
        # Don't allow setting metadata keys
        if key.startswith("_"):
            logger.warning(f"Cannot set metadata key: {key}")
            return

        old_value = self.settings.get(key)
        if old_value != value:
            self.settings[key] = value
            self.save()
            logger.debug(f"Setting changed: {key} = {value} (was: {old_value})")

    def update(self, updates: Dict[str, Any]):
        """
        Update multiple settings at once.

        Args:
            updates: Dictionary of key-value pairs to update
        """
        changed = False
        for key, value in updates.items():
            if key.startswith("_"):
                continue
            if self.settings.get(key) != value:
                self.settings[key] = value
                changed = True

        if changed:
            self.save()

    def reset(self):
        """Reset to default settings."""
        logger.info("Resetting settings to defaults")
        self.settings = self._default_settings()
        self.save()

    def get_all(self) -> Dict[str, Any]:
        """Get all settings (excluding metadata)."""
        return {k: v for k, v in self.settings.items() if not k.startswith("_")}

    def export_settings(self, export_path: str):
        """Export settings to a file."""
        try:
            export_data = self.get_all()
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Exported settings to: {export_path}")
        except Exception as e:
            logger.error(f"Failed to export settings: {e}")

    def import_settings(self, import_path: str):
        """Import settings from a file."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported = json.load(f)

            # Validate and merge
            defaults = self._default_settings()
            for key, value in imported.items():
                if key in defaults:  # Only import known keys
                    self.settings[key] = value

            self.save()
            logger.info(f"Imported settings from: {import_path}")
        except Exception as e:
            logger.error(f"Failed to import settings: {e}")


# Global instance
_settings_manager = None


def get_settings_manager() -> SettingsManager:
    """Get or create global settings manager instance."""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager


def save_setting(key: str, value: Any):
    """Convenience function to save a single setting."""
    manager = get_settings_manager()
    manager.set(key, value)


def load_setting(key: str, default: Any = None) -> Any:
    """Convenience function to load a single setting."""
    manager = get_settings_manager()
    return manager.get(key, default)


def load_all_settings() -> Dict[str, Any]:
    """Convenience function to load all settings."""
    manager = get_settings_manager()
    return manager.get_all()


def reset_settings():
    """Convenience function to reset all settings."""
    manager = get_settings_manager()
    manager.reset()


def export_settings(path: str):
    """Convenience function to export settings."""
    manager = get_settings_manager()
    manager.export_settings(path)


def import_settings(path: str):
    """Convenience function to import settings."""
    manager = get_settings_manager()
    manager.import_settings(path)
