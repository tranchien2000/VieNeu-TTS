"""
Audiobook processor for handling large text files.
Simple version without pause/resume (MVP).
"""

import soundfile as sf
import numpy as np
import time
from pathlib import Path
from typing import List, Dict, Callable, Optional
from vieneu_utils.core_utils import split_text_into_chunks, join_audio_chunks


class AudiobookProcessor:
    """
    Process large text files into audiobooks.
    MVP version: Simple batch processing without pause/resume.
    """

    def __init__(self, tts_model, output_dir: str):
        """
        Initialize processor.

        Args:
            tts_model: TTS model instance
            output_dir: Directory for output files
        """
        self.tts = tts_model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.sr = 24000
        self.checkpoint_file = self.output_dir / "checkpoint.json"

    def save_checkpoint(self, state: Dict):
        """Save checkpoint to disk."""
        import json
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def load_checkpoint(self) -> Optional[Dict]:
        """Load checkpoint if exists."""
        import json
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def clear_checkpoint(self):
        """Delete checkpoint file."""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()

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
        max_batch_size: int = 16
    ) -> List[str]:
        """
        Process audiobook chapters into audio files.

        Args:
            chapters: List of chapter dicts with 'title' and 'text'
            voice_id: Voice ID to use
            temperature: Generation temperature
            max_chars_chunk: Max chars per chunk
            output_mode: "Single file" or "Split by chapters"
            progress_callback: Callback(current, total, chapter_name, preview_audio)
            pause_event: Threading event for pause requests
            stop_event: Threading event for stop requests
            resume_from_checkpoint: Whether to resume from saved checkpoint
            use_batch: Whether to use batch processing
            max_batch_size: Maximum batch size for batch processing

        Returns:
            List of output file paths
        """
        import soundfile as sf

        # Load checkpoint if resuming
        start_chapter_idx = 0
        chapter_audios = []
        completed_chapter_files = []

        if resume_from_checkpoint:
            checkpoint = self.load_checkpoint()
            if checkpoint:
                start_chapter_idx = checkpoint.get('current_chapter_idx', 0)
                # Load completed chapter audio files from checkpoint
                completed_chapter_files = checkpoint.get('completed_chapter_files', [])
                for idx, ch_file in enumerate(completed_chapter_files):
                    if Path(ch_file).exists():
                        audio_data, _ = sf.read(ch_file)
                        # Extract actual title from filename: chapter_XX_Title.wav -> Title
                        stem = Path(ch_file).stem
                        if stem.startswith(f"chapter_{idx+1:02d}_"):
                            title = stem[len(f"chapter_{idx+1:02d}_"):]
                        else:
                            title = stem
                        chapter_audios.append({
                            'title': title,
                            'audio': audio_data,
                            'index': idx
                        })

        # Get voice data
        voice_data = self.tts.get_preset_voice(voice_id)
        ref_codes = voice_data['codes']
        ref_text = voice_data['text']

        # Convert to numpy if needed
        if 'torch' in str(type(ref_codes)):
            import torch
            if isinstance(ref_codes, torch.Tensor):
                ref_codes = ref_codes.cpu().numpy()

        # Check if batch processing is available
        using_batch = use_batch and hasattr(self.tts, 'infer_batch')

        # Process each chapter starting from checkpoint
        total_chunks = sum(len(split_text_into_chunks(ch['text'], max_chars=max_chars_chunk)) for ch in chapters)
        current_chunk = sum(len(split_text_into_chunks(chapters[i]['text'], max_chars=max_chars_chunk))
                           for i in range(start_chapter_idx))

        for ch_idx in range(start_chapter_idx, len(chapters)):
            chapter = chapters[ch_idx]
            chapter_name = chapter['title']
            chapter_text = chapter['text']

            # Check stop event
            if stop_event and stop_event.is_set():
                self.save_checkpoint({
                    'current_chapter_idx': ch_idx,
                    'completed_chapter_files': completed_chapter_files,
                    'voice_id': voice_id,
                    'temperature': temperature,
                    'max_chars_chunk': max_chars_chunk,
                    'output_mode': output_mode,
                    'timestamp': time.time()
                })
                return []

            # Check pause event
            if pause_event and pause_event.is_set():
                self.save_checkpoint({
                    'current_chapter_idx': ch_idx,
                    'completed_chapter_files': completed_chapter_files,
                    'voice_id': voice_id,
                    'temperature': temperature,
                    'max_chars_chunk': max_chars_chunk,
                    'output_mode': output_mode,
                    'timestamp': time.time()
                })
                return []

            # Split chapter into chunks
            chunks = split_text_into_chunks(chapter_text, max_chars=max_chars_chunk)
            chapter_chunk_audios = []

            # Process chunks with batch or sequential
            if using_batch and len(chunks) > 1:
                # Batch processing
                for batch_start in range(0, len(chunks), max_batch_size):
                    # Check stop/pause before each batch
                    if stop_event and stop_event.is_set():
                        self.save_checkpoint({
                            'current_chapter_idx': ch_idx,
                            'completed_chapter_files': completed_chapter_files,
                            'voice_id': voice_id,
                            'temperature': temperature,
                            'max_chars_chunk': max_chars_chunk,
                            'output_mode': output_mode,
                            'timestamp': time.time()
                        })
                        return []

                    if pause_event and pause_event.is_set():
                        self.save_checkpoint({
                            'current_chapter_idx': ch_idx,
                            'completed_chapter_files': completed_chapter_files,
                            'voice_id': voice_id,
                            'temperature': temperature,
                            'max_chars_chunk': max_chars_chunk,
                            'output_mode': output_mode,
                            'timestamp': time.time()
                        })
                        return []

                    # Process batch
                    batch_end = min(batch_start + max_batch_size, len(chunks))
                    current_batch = chunks[batch_start:batch_end]

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

                        # Progress callback with preview (last chunk in batch)
                        if progress_callback and i == len(batch_audios) - 1:
                            preview_audio = (self.sr, chunk_audio) if chunk_audio is not None else None
                            progress_callback(current_chunk, total_chunks, chapter_name, preview_audio)
            else:
                # Sequential processing
                for i, chunk in enumerate(chunks):
                    # Check stop/pause inside chunk loop
                    if stop_event and stop_event.is_set():
                        self.save_checkpoint({
                            'current_chapter_idx': ch_idx,
                            'completed_chapter_files': completed_chapter_files,
                            'voice_id': voice_id,
                            'temperature': temperature,
                            'max_chars_chunk': max_chars_chunk,
                            'output_mode': output_mode,
                            'timestamp': time.time()
                        })
                        return []

                    if pause_event and pause_event.is_set():
                        self.save_checkpoint({
                            'current_chapter_idx': ch_idx,
                            'completed_chapter_files': completed_chapter_files,
                            'voice_id': voice_id,
                            'temperature': temperature,
                            'max_chars_chunk': max_chars_chunk,
                            'output_mode': output_mode,
                            'timestamp': time.time()
                        })
                        return []

                    # Synthesize chunk
                    chunk_audio = self.tts.infer(
                        chunk,
                        ref_codes=ref_codes,
                        ref_text=ref_text,
                        temperature=temperature,
                        max_chars=max_chars_chunk,
                        skip_normalize=True
                    )

                    if chunk_audio is not None and len(chunk_audio) > 0:
                        chapter_chunk_audios.append(chunk_audio)

                    current_chunk += 1

                    # Progress callback with preview
                    if progress_callback:
                        preview_audio = (self.sr, chunk_audio) if chunk_audio is not None else None
                        progress_callback(current_chunk, total_chunks, chapter_name, preview_audio)

            # Join chapter chunks
            if chapter_chunk_audios:
                chapter_audio = join_audio_chunks(chapter_chunk_audios, sr=self.sr, silence_p=0.05, crossfade_p=0.01)

                # Sanitize chapter name for filename
                safe_title = "".join(c for c in chapter_name if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_title = safe_title[:50]  # Limit length

                chapter_audios.append({
                    'title': chapter_name,
                    'audio': chapter_audio,
                    'index': ch_idx
                })

                # Save chapter immediately with proper name
                if output_mode == "Single file":
                    # For single file mode, just collect audio, don't save yet
                    pass
                else:
                    # For separate chapters, save with proper name immediately
                    filename = f"chapter_{ch_idx+1:02d}_{safe_title}.wav"
                    chapter_file = self.output_dir / filename
                    sf.write(chapter_file, chapter_audio, self.sr)
                    # Track saved file for checkpoint
                    completed_chapter_files.append(str(chapter_file))

        # All chapters completed - clear checkpoint
        self.clear_checkpoint()

        # Save output
        if output_mode == "Single file":
            return self._save_single_file(chapter_audios)
        else:
            # Already saved during processing, just return file list
            return self._get_saved_chapter_files(chapter_audios)

    def _save_single_file(self, chapter_audios: List[Dict]) -> List[str]:
        """Join all chapters and save as single file."""
        # Add crossfade between chapters (Turbo adds its own silence at sentence ends)
        all_audio = []
        silence = np.zeros(int(self.sr * 0.5), dtype=np.float32)  # Reduced from 1.0s

        for i, ch in enumerate(chapter_audios):
            all_audio.append(ch['audio'])
            if i < len(chapter_audios) - 1:
                all_audio.append(silence)

        final_audio = join_audio_chunks(all_audio, sr=self.sr, silence_p=0.0, crossfade_p=0.02)

        # Save
        output_file = self.output_dir / "audiobook.wav"
        sf.write(output_file, final_audio, self.sr)

        return [str(output_file)]

    def _get_saved_chapter_files(self, chapter_audios: List[Dict]) -> List[str]:
        """Get list of already saved chapter files."""
        output_files = []

        for ch in chapter_audios:
            # Sanitize filename
            safe_title = "".join(c for c in ch['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title[:50]  # Limit length

            filename = f"chapter_{ch['index']+1:02d}_{safe_title}.wav"
            output_file = self.output_dir / filename
            output_files.append(str(output_file))

        return output_files

