"""
Audiobook processor for handling large text files.
Enhanced with checkpoint/resume, auto-save, and cross-session recovery.
"""

import soundfile as sf
import numpy as np
import time
import json
import os
from pathlib import Path
from typing import List, Dict, Callable, Optional, Any
from vieneu_utils.core_utils import split_text_into_chunks, join_audio_chunks
from vieneu_utils.phonemize_text import normalize_to_chunks


class AudiobookProcessor:
    """
    Process large text files into audiobooks.
    Supports pause/resume, auto-checkpoint, and cross-session recovery.
    """

    def __init__(self, tts_model, output_dir: str, checkpoint_interval: int = 5, book_name: str = "audiobook"):
        """
        Initialize processor.

        Args:
            tts_model: TTS model instance
            output_dir: Directory for output files
            checkpoint_interval: Save checkpoint every N chunks (default 5)
            book_name: Base name for output files (default "audiobook")
        """
        self.tts = tts_model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.sr = 24000
        self.checkpoint_file = self.output_dir / "checkpoint.json"
        self._last_checkpoint_time = 0
        self.checkpoint_interval = checkpoint_interval
        self.book_name = "".join(c for c in book_name if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
    def save_checkpoint(self, state: Dict):
        """Save checkpoint atomically (Windows/OneDrive compatible)."""
        temp_file = self.checkpoint_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            # Use copy + unlink instead of os.replace for Windows/OneDrive compatibility
            import shutil
            shutil.copy2(temp_file, self.checkpoint_file)
            temp_file.unlink()
            self._last_checkpoint_time = time.time()
        except Exception:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            raise

    def load_checkpoint(self) -> Optional[Dict]:
        """Load checkpoint if exists and is valid."""
        if not self.checkpoint_file.exists():
            return None
        try:
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Validate required fields
            if not all(k in data for k in ('version', 'current_chapter_idx', 'current_chunk_idx', 'voice_id')):
                return None
            return data
        except Exception:
            # Corrupt file – rename for debugging and return None
            backup = self.checkpoint_file.with_suffix('.corrupted')
            try:
                self.checkpoint_file.rename(backup)
            except Exception:
                pass
            return None

    def clear_checkpoint(self):
        """Delete checkpoint file if present."""
        if self.checkpoint_file.exists():
            try:
                self.checkpoint_file.unlink()
            except Exception:
                pass

    def _load_progress(self) -> Dict:
        """Load progress from checkpoint file if exists, else return default values."""
        checkpoint = self.load_checkpoint()
        if checkpoint:
            return {
                'last_completed_chapter': checkpoint.get('current_chapter_idx', -1),
                'completed_files': checkpoint.get('completed_chapter_files', [])
            }
        return {'last_completed_chapter': -1, 'completed_files': []}

    def _save_progress(self, chapter_idx: int, chapter_file: str) -> None:
        """Update checkpoint file with completed chapter info atomically (Windows/OneDrive compatible)."""
        checkpoint = self.load_checkpoint() or self._build_checkpoint_state(
            chapter_idx, 0, [], "unknown", 0.7, 256, "Single file"
        )
        checkpoint['current_chapter_idx'] = chapter_idx
        checkpoint.setdefault('completed_chapter_files', []).append(chapter_file)
        checkpoint['status'] = "completed_chapter"
        checkpoint['timestamp'] = time.time()

        temp = self.checkpoint_file.with_suffix('.tmp')
        with open(temp, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)
        import shutil
        shutil.copy2(temp, self.checkpoint_file)
        temp.unlink()

    def clear_progress(self) -> None:
        """Delete checkpoint file if present."""
        self.clear_checkpoint()

    def process_audiobook(
        self,
        chapters: List[Dict],
        voice_id: str,
        temperature: float = 0.7,
        max_chars_chunk: int = 256,
        output_mode: str = "Single file",
        progress_callback: Optional[Callable] = None,
        pause_event: Optional[object] = None,
        stop_event: Optional[object] = None,
        resume_from_checkpoint: bool = False,
        use_batch: bool = False,
        max_batch_size: int = 16,
        save_intermediate: bool = True,
        spell_check_engine: str = "off",
        spell_check_device: str = "auto",
        spell_check_batch_size: int = 16,
    ) -> List[str]:
        """
        Process audiobook chapters into audio files with enhanced checkpoint/resume.

        Args:
            chapters: List of chapter dicts with 'title' and 'text'
            voice_id: Voice ID to use
            temperature: Generation temperature
            max_chars_chunk: Max chars per chunk
            output_mode: "Single file" or "Split by chapters"
            progress_callback: Callback(current, total, chapter_name, preview_audio, state_info)
            pause_event: Threading event for pause requests
            stop_event: Threading event for stop requests
            resume_from_checkpoint: Whether to resume from saved checkpoint
            use_batch: Whether to use batch processing
            max_batch_size: Maximum batch size for batch processing
            save_intermediate: Save completed chapter audio files immediately
            spell_check_engine: Spell check engine ("off", "symspell", "vspell", "hybrid")
            spell_check_device: Device for VSpell ("auto", "cpu", "cuda")
            spell_check_batch_size: Batch size for spell checking

        Returns:
            List of output file paths
        """
        import soundfile as sf
        from vieneu_utils.spell_checker import get_spell_checker

        # Apply spell check to all chapters BEFORE processing (if not resuming)
        if not resume_from_checkpoint and spell_check_engine != "off":
            checker = get_spell_checker(
                engine=spell_check_engine,
                device=spell_check_device,
                batch_size=spell_check_batch_size
            )
            for chapter in chapters:
                chapter['text'] = checker.correct(chapter['text'])

        # Load progress if resuming
        progress = self._load_progress()
        start_chapter_idx = progress.get('last_completed_chapter', -1) + 1
        completed_chapter_files = progress.get('completed_files', [])
        chapter_audios = []  # will hold audio data for already completed chapters (optional)
        # Note: we do not reload audio data here; we simply continue from next chapter

        # Load checkpoint for mid-chapter resume
        start_chunk_idx = 0
        if resume_from_checkpoint:
            checkpoint = self.load_checkpoint()
            if checkpoint:
                # Validate checkpoint matches current run
                if checkpoint.get('voice_id') == voice_id and \
                   checkpoint.get('output_mode') == output_mode and \
                   checkpoint.get('temperature') == temperature and \
                   checkpoint.get('max_chars_chunk') == max_chars_chunk:
                    start_chapter_idx = checkpoint.get('current_chapter_idx', start_chapter_idx)
                    start_chunk_idx = checkpoint.get('current_chunk_idx', 0)
                    completed_chapter_files = checkpoint.get('completed_chapter_files', completed_chapter_files)
                    # Ensure we don't go backwards
                    if start_chapter_idx < progress.get('last_completed_chapter', -1) + 1:
                        start_chapter_idx = progress.get('last_completed_chapter', -1) + 1
                        start_chunk_idx = 0



        # --- Get voice data ---
        voice_data = self.tts.get_preset_voice(voice_id)
        ref_codes = voice_data['codes']
        ref_text = voice_data['text']

        if 'torch' in str(type(ref_codes)):
            import torch
            if isinstance(ref_codes, torch.Tensor):
                ref_codes = ref_codes.cpu().numpy()

        using_batch = use_batch and hasattr(self.tts, 'infer_batch')

        # Pre-calculate total chunks for progress - normalize first like single file mode
        all_chapter_chunks = []
        for ch in chapters:
            chunks = normalize_to_chunks(
                ch['text'],
                max_chars=max_chars_chunk,
                skip_normalize=False,
                spell_check_engine=spell_check_engine,
                spell_check_device=spell_check_device,
                spell_check_batch_size=spell_check_batch_size
            )
            all_chapter_chunks.append(chunks)
        total_chunks = sum(len(c) for c in all_chapter_chunks)

        # Calculate starting chunk offset
        current_chunk = 0
        for i in range(start_chapter_idx):
            current_chunk += len(all_chapter_chunks[i])
        current_chunk += start_chunk_idx

        # --- Process chapters ---
        for ch_idx in range(start_chapter_idx, len(chapters)):
            chapter = chapters[ch_idx]
            chapter_name = chapter['title']
            chunks = all_chapter_chunks[ch_idx]

            # Determine starting chunk for this chapter
            chunk_start = start_chunk_idx if ch_idx == start_chapter_idx else 0

            # Check stop/pause before chapter
            if self._check_stop_pause(stop_event, pause_event, ch_idx, chunk_start, completed_chapter_files,
                                       voice_id, temperature, max_chars_chunk, output_mode):
                return []

            chapter_chunk_audios = []

            # Load existing chapter audio if resuming mid-chapter
            # (No per‑chunk resume – start from next chapter only)
            pass

            # Process chunks
            if using_batch and len(chunks) > 1:
                current_chunk, chapter_chunk_audios = self._process_batched(
                    chunks, chunk_start, ch_idx, chapter_name,
                    ref_codes, ref_text, temperature, max_batch_size,
                    current_chunk, total_chunks, progress_callback,
                    stop_event, pause_event, completed_chapter_files,
                    voice_id, max_chars_chunk, output_mode
                )
            else:
                current_chunk, chapter_chunk_audios = self._process_sequential(
                    chunks, chunk_start, ch_idx, chapter_name,
                    ref_codes, ref_text, temperature, max_chars_chunk,
                    current_chunk, total_chunks, progress_callback,
                    stop_event, pause_event, completed_chapter_files,
                    voice_id, max_chars_chunk, output_mode
                )

            # Join chapter chunks - increase crossfade to 50ms to mask cold-start artifacts
            if chapter_chunk_audios:
                chapter_audio = join_audio_chunks(chapter_chunk_audios, sr=self.sr, silence_p=0.05, crossfade_p=0.05)

                safe_title = "".join(c for c in chapter_name if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_title = safe_title[:50]

                chapter_audios.append({
                    'title': chapter_name,
                    'audio': chapter_audio,
                    'index': ch_idx
                })

                # Save chapter immediately if separate files mode
                if output_mode != "Single file" and save_intermediate:
                    filename = f"{self.book_name}_chapter_{ch_idx+1:03d}.wav"
                    chapter_file = self.output_dir / filename
                    sf.write(chapter_file, chapter_audio, self.sr)
                    completed_chapter_files.append(str(chapter_file))
                    # Save progress after each chapter completion
                    self._save_progress(ch_idx, str(chapter_file))

            # Reset chunk index for next chapter
            start_chunk_idx = 0

        # All chapters completed
        self.clear_checkpoint()

        # Save output
        if output_mode == "Single file":
            return self._save_single_file(chapter_audios)
        else:
            return self._get_saved_chapter_files(chapter_audios)

    def _check_stop_pause(self, stop_event, pause_event, ch_idx, chunk_in_chapter, completed_files,
                          voice_id, temp, max_chars, output_mode) -> bool:
        """Check stop/pause events and save checkpoint if needed. Returns True if should stop."""
        if stop_event and stop_event.is_set():
            self.save_checkpoint(self._build_checkpoint_state(
                ch_idx, chunk_in_chapter, completed_files, voice_id, temp, max_chars, output_mode,
                status="stopped"
            ))
            return True
        if pause_event and pause_event.is_set():
            self.save_checkpoint(self._build_checkpoint_state(
                ch_idx, chunk_in_chapter, completed_files, voice_id, temp, max_chars, output_mode,
                status="paused"
            ))
            return True
        return False

    def _process_batched(
        self, chunks, chunk_start, ch_idx, chapter_name,
        ref_codes, ref_text, temperature, max_batch_size,
        current_chunk, total_chunks, progress_callback,
        stop_event, pause_event, completed_files,
        voice_id, max_chars_chunk, output_mode
    ):
        """Process chunks in batches with checkpoint support."""
        chapter_chunk_audios = []

        # Skip already-processed chunks
        remaining_chunks = chunks[chunk_start:]

        for batch_start in range(0, len(remaining_chunks), max_batch_size):
            chunk_in_chapter = batch_start + 1
            if self._check_stop_pause(stop_event, pause_event, ch_idx, chunk_in_chapter, completed_files,
                                       voice_id, temperature, max_chars_chunk, output_mode):
                return current_chunk, chapter_chunk_audios

            batch_end = min(batch_start + max_batch_size, len(remaining_chunks))
            current_batch = remaining_chunks[batch_start:batch_end]

            batch_audios = self.tts.infer_batch(
                current_batch,
                ref_codes=ref_codes,
                ref_text=ref_text,
                max_batch_size=max_batch_size,
                temperature=temperature,
                skip_normalize=True
            )

            for i, chunk_audio in enumerate(batch_audios):
                if chunk_audio is not None and len(chunk_audio) > 0:
                    chapter_chunk_audios.append(chunk_audio)

                current_chunk += 1

                # Checkpoint every N chunks
                chunk_in_chapter = batch_start + i + 1
                if chunk_in_chapter % self.checkpoint_interval == 0:
                    self.save_checkpoint(self._build_checkpoint_state(
                        ch_idx, chunk_in_chapter, completed_files,
                        voice_id, temperature, max_chars_chunk, output_mode,
                        status="processing"
                    ))

                # Progress callback
                if progress_callback and i == len(batch_audios) - 1:
                    preview_audio = (self.sr, chunk_audio) if chunk_audio is not None else None
                    state_info = {
                        'chapter_idx': ch_idx,
                        'chunk_in_chapter': batch_start + i + 1,
                        'total_chunks_in_chapter': len(chunks),
                        'status': 'processing'
                    }
                    progress_callback(current_chunk, total_chunks, chapter_name, preview_audio, state_info)

        return current_chunk, chapter_chunk_audios

    def _process_sequential(
        self, chunks, chunk_start, ch_idx, chapter_name,
        ref_codes, ref_text, temperature, max_chars_chunk,
        current_chunk, total_chunks, progress_callback,
        stop_event, pause_event, completed_files,
        voice_id, max_chars_chunk_param, output_mode
    ):
        """Process chunks sequentially with checkpoint support."""
        chapter_chunk_audios = []

        # Process in small batches to maintain checkpoint granularity but reduce cold-start artifacts
        batch_size = 4  # Small batch for sequential mode

        for i in range(chunk_start, len(chunks), batch_size):
            chunk_in_chapter = i + 1
            if self._check_stop_pause(stop_event, pause_event, ch_idx, chunk_in_chapter, completed_files,
                                       voice_id, temperature, max_chars_chunk_param, output_mode):
                return current_chunk, chapter_chunk_audios

            batch_end = min(i + batch_size, len(chunks))
            current_batch = chunks[i:batch_end]

            # Use infer_batch for better continuity between chunks in the same batch
            batch_audios = self.tts.infer_batch(
                current_batch,
                ref_codes=ref_codes,
                ref_text=ref_text,
                max_batch_size=batch_size,
                temperature=temperature,
                skip_normalize=True
            )

            for j, chunk_audio in enumerate(batch_audios):
                if chunk_audio is not None and len(chunk_audio) > 0:
                    chapter_chunk_audios.append(chunk_audio)

                current_chunk += 1

                # Checkpoint every N chunks
                if (i + j + 1 - chunk_start) % self.checkpoint_interval == 0:
                    self.save_checkpoint(self._build_checkpoint_state(
                        ch_idx, i + j + 1, completed_files,
                        voice_id, temperature, max_chars_chunk_param, output_mode,
                        status="processing"
                    ))

                # Progress callback
                if progress_callback:
                    preview_audio = (self.sr, chunk_audio) if chunk_audio is not None else None
                    state_info = {
                        'chapter_idx': ch_idx,
                        'chunk_in_chapter': i + j + 1,
                        'total_chunks_in_chapter': len(chunks),
                        'status': 'processing'
                    }
                    progress_callback(current_chunk, total_chunks, chapter_name, preview_audio, state_info)

        return current_chunk, chapter_chunk_audios

    def _build_checkpoint_state(self, ch_idx, chunk_idx, completed_files,
                                voice_id, temp, max_chars, output_mode, status="processing") -> Dict:
        """Build comprehensive checkpoint state dictionary."""
        return {
            'version': 2,  # Checkpoint format version
            'current_chapter_idx': ch_idx,
            'current_chunk_idx': chunk_idx,
            'completed_chapter_files': completed_files,
            'voice_id': voice_id,
            'temperature': temp,
            'max_chars_chunk': max_chars,
            'output_mode': output_mode,
            'status': status,
            'timestamp': time.time(),
            'sample_rate': self.sr,
            'checkpoint_interval': self.checkpoint_interval,
        }

    def _save_single_file(self, chapter_audios: List[Dict]) -> List[str]:
        """Join all chapters and save as single file."""
        all_audio = []
        silence = np.zeros(int(self.sr * 0.5), dtype=np.float32)

        for i, ch in enumerate(chapter_audios):
            all_audio.append(ch['audio'])
            if i < len(chapter_audios) - 1:
                all_audio.append(silence)

        final_audio = join_audio_chunks(all_audio, sr=self.sr, silence_p=0.0, crossfade_p=0.05)

        output_file = self.output_dir / f"{self.book_name}.wav"
        sf.write(output_file, final_audio, self.sr)

        return [str(output_file)]

    def _get_saved_chapter_files(self, chapter_audios: List[Dict]) -> List[str]:
        """Get list of already saved chapter files."""
        output_files = []
        for ch in chapter_audios:
            filename = f"{self.book_name}_chapter_{ch['index']+1:03d}.wav"
            output_file = self.output_dir / filename
            output_files.append(str(output_file))
        return output_files

    def get_checkpoint_info(self) -> Optional[Dict]:
        """Get human-readable checkpoint info for UI display."""
        checkpoint = self.load_checkpoint()
        if not checkpoint:
            return None
        return {
            'chapter_index': checkpoint.get('current_chapter_idx', 0),
            'chunk_index': checkpoint.get('current_chunk_idx', 0),
            'completed_chapters': len(checkpoint.get('completed_chapter_files', [])),
            'voice_id': checkpoint.get('voice_id', 'unknown'),
            'status': checkpoint.get('status', 'unknown'),
            'timestamp': checkpoint.get('timestamp', 0),
            'version': checkpoint.get('version', 1),
        }

    def can_resume(self) -> bool:
        """Check if a valid checkpoint exists for resume."""
        return self.checkpoint_file.exists() and self.load_checkpoint() is not None

    def force_checkpoint(self, ch_idx: int, chunk_idx: int, completed_files: List[str],
                         voice_id: str, temp: float, max_chars: int, output_mode: str):
        """Force save checkpoint (e.g., on app shutdown)."""
        self.save_checkpoint(self._build_checkpoint_state(
            ch_idx, chunk_idx, completed_files, voice_id, temp, max_chars, output_mode,
            status="forced"
        ))