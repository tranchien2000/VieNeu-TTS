"""
Optimized model loading with caching and offline mode support.
"""
import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger("Vieneu.Cache")

def set_offline_mode():
    """Enable offline mode to skip HuggingFace update checks."""
    os.environ["HF_HUB_OFFLINE"] = "1"
    logger.info("🔒 Offline mode enabled - using cached models only")

def get_cache_dir() -> Path:
    """Get HuggingFace cache directory."""
    cache_home = os.environ.get("HF_HOME") or os.environ.get("HUGGINGFACE_HUB_CACHE")
    if cache_home:
        return Path(cache_home)

    # Default cache locations
    if os.name == "nt":  # Windows
        return Path.home() / ".cache" / "huggingface" / "hub"
    else:  # Linux/Mac
        return Path.home() / ".cache" / "huggingface" / "hub"

def is_model_cached(repo_id: str) -> bool:
    """Check if a model is already cached locally."""
    cache_dir = get_cache_dir()
    model_dir = cache_dir / f"models--{repo_id.replace('/', '--')}"
    return model_dir.exists()

def list_cached_models():
    """List all cached models."""
    cache_dir = get_cache_dir()
    if not cache_dir.exists():
        logger.warning(f"Cache directory not found: {cache_dir}")
        return []

    cached = []
    for item in cache_dir.iterdir():
        if item.is_dir() and item.name.startswith("models--"):
            repo_id = item.name.replace("models--", "").replace("--", "/")
            cached.append(repo_id)

    return cached

def get_cache_size() -> int:
    """Get total size of cached models in bytes."""
    cache_dir = get_cache_dir()
    if not cache_dir.exists():
        return 0

    total_size = 0
    for item in cache_dir.rglob("*"):
        if item.is_file():
            total_size += item.stat().st_size

    return total_size

def format_size(bytes_size: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"

def print_cache_info():
    """Print cache information."""
    cache_dir = get_cache_dir()
    cached_models = list_cached_models()
    cache_size = get_cache_size()

    print("=" * 60)
    print("📦 HuggingFace Cache Info")
    print("=" * 60)
    print(f"Cache directory: {cache_dir}")
    print(f"Total size: {format_size(cache_size)}")
    print(f"Cached models: {len(cached_models)}")
    print()

    if cached_models:
        print("Models:")
        for model in cached_models:
            print(f"  - {model}")
    else:
        print("No models cached yet.")

    print("=" * 60)

if __name__ == "__main__":
    print_cache_info()
