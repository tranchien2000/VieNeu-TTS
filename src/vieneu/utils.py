import numpy as np
import torch
import re

def _linear_overlap_add(frames: list[np.ndarray], stride: int) -> np.ndarray:
    """
    Perform linear overlap-add on a list of audio frames.

    Original implementation inspired by:
    https://github.com/facebookresearch/encodec/blob/main/encodec/utils.py

    Args:
        frames: List of audio frames to join.
        stride: Stride between frames in samples.

    Returns:
        Joined audio waveform.
    """
    assert len(frames) > 0
    dtype = frames[0].dtype
    shape = frames[0].shape[:-1]

    total_size = 0
    for i, frame in enumerate(frames):
        frame_end = stride * i + frame.shape[-1]
        total_size = max(total_size, frame_end)

    sum_weight = np.zeros(total_size, dtype=dtype)
    out = np.zeros((*shape, total_size), dtype=dtype)

    # Cache for weights to avoid recomputing if frame_length is constant
    _weight_cache = {}

    offset: int = 0
    for frame in frames:
        frame_length = frame.shape[-1]

        if frame_length not in _weight_cache:
            t = np.linspace(0, 1, frame_length + 2, dtype=dtype)[1:-1]
            weight = np.abs(0.5 - (t - 0.5))
            _weight_cache[frame_length] = weight
        else:
            weight = _weight_cache[frame_length]

        out[..., offset : offset + frame_length] += weight * frame
        sum_weight[offset : offset + frame_length] += weight
        offset += stride

    assert sum_weight.min() > 0
    return out / sum_weight

def _compile_codec_with_triton(codec) -> bool:
    """
    Compile codec with Triton for faster decoding (Windows/Linux compatible).

    Args:
        codec: The codec model to compile.

    Returns:
        True if compilation was successful, False otherwise.
    """
    try:
        import triton

        if hasattr(codec, 'dec') and hasattr(codec.dec, 'resblocks'):
            if len(codec.dec.resblocks) > 2:
                codec.dec.resblocks[2].forward = torch.compile(
                    codec.dec.resblocks[2].forward,
                    mode="reduce-overhead",
                    dynamic=True
                )
                print("   ✅ Triton compilation enabled for codec")
        return True

    except ImportError:
        # Silently fail for optional triton optimization
        return False
    except Exception:
        return False

def extract_speech_ids(codes_str: str) -> list[int]:
    """Extract speech token IDs from a string using regex."""
    return [int(num) for num in re.findall(r"<\|speech_(\d+)\|>", codes_str)]
