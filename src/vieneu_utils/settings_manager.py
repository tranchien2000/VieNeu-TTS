"""
Settings manager for VieNeu-TTS UI.
Persists user preferences across sessions.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class SettingsManager:
    """Manages persistent UI settings."""

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
        """Load settings from disk."""
        if self.settings_path.exists():
            try:
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Failed to load settings: {e}")
                return self._default_settings()
        return self._default_settings()

    def save(self):
        """Save settings to disk."""
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Failed to save settings: {e}")

    def _default_settings(self) -> Dict[str, Any]:
        """Return default settings."""
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

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        """Set a setting value and save."""
        self.settings[key] = value
        self.save()

    def update(self, updates: Dict[str, Any]):
        """Update multiple settings at once."""
        self.settings.update(updates)
        self.save()

    def reset(self):
        """Reset to default settings."""
        self.settings = self._default_settings()
        self.save()

    def get_all(self) -> Dict[str, Any]:
        """Get all settings."""
        return self.settings.copy()


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
