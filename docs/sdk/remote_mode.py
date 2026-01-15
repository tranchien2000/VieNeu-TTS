"""
Demo VieNeuSDK v1.1.3 - Full Features Guide
"""

import time
import soundfile as sf
from vieneu import Vieneu
from pathlib import Path

def main():
    print("🚀 Initializing VieNeu SDK (v1.1.3)...")
    
    # Initialize SDK
    # Default: "pnnbao-ump/VieNeu-TTS-0.3B-q4-gguf" (Speed & CPU Optimized)
    #
    # You can change 'backbone_repo' to balance Quality vs Speed:
    # 1. Better Quality (slower than q4): "pnnbao-ump/VieNeu-TTS-0.3B-q8-gguf"
    # 2. PyTorch 0.3B (Fast, uncompressed): "pnnbao-ump/VieNeu-TTS-0.3B"
    # 3. PyTorch 0.5B (Best Quality, heavy): "pnnbao-ump/VieNeu-TTS"
    # You can also use a GGUF version merged with your own LoRA adapter.
    # See finetuning guide: https://github.com/pnnbao97/VieNeu-TTS/tree/main/finetune
    
    # Mode selection:
    # - mode="standard" (Default): Runs locally using GGUF (CPU) or PyTorch
    # - mode="remote": Connects to the LMDeploy server setup above for max speed
    
    # API Configuration for Remote Mode
    # Replace with your own server URL (e.g. http://localhost:23333/v1)
    LMDEPLOY_API_URL = 'http://bore.pub:31631/v1' 
    
    # Initialize: Choose 'standard' (local) or 'remote' (API)
    # tts = Vieneu(mode='standard') 
    # Note: 'model_name' must match the model ID serving on LMDeploy
    tts = Vieneu(mode='remote', api_base=LMDEPLOY_API_URL, model_name="pnnbao-ump/VieNeu-TTS")

    # ---------------------------------------------------------
    # PART 1: PRESET VOICES
    # ---------------------------------------------------------
    available_voices = tts.list_preset_voices()
    
    # Display available voices
    if available_voices:
        print(f"📋 Found {len(available_voices)} available voices. First 3:")
        for desc, name in available_voices[:3]:
            print(f"   - {desc} (ID: {name})")
    
    # 1. Use the default voice
    print("\n--- 2. Default Voice ---")
    default_voice_data = tts.get_preset_voice() # No arg = Default
    print(f"✅ Default voice text: {default_voice_data['text'][:50]}...")

    # ---------------------------------------------------------
    # PART 2: CUSTOM VOICES GUIDE
    # ---------------------------------------------------------
    print("\n--- 3. Custom Voice Guide ---")
    print("ℹ️ To use a custom voice:")
    print("1. Create voice preset: `uv run python finetune/create_voices_json.py ...`")
    print("2. Or use ad-hoc reference in code.")

    # ---------------------------------------------------------
    # PART 3: SYNTHESIS
    # ---------------------------------------------------------
    print("\n--- 3. Speech Synthesis ---")
    
    text_input = "Xin chào, tôi là VieNeu. Tôi có thể giúp bạn đọc sách, làm chatbot thời gian thực, hoặc thậm chí clone giọng nói của bạn."
    
    # Example: Select the first voice ID
    _, selected_voice_id = available_voices[0] if available_voices else (None, None)
    # voice_data = tts.get_preset_voice(selected_voice_id)
    
    print("🎧 Generating...")
    print(f"   Using default voice mechanism...")
    audio = tts.infer(
        text=text_input,
        voice=None, # SDK will use default automatically. 
        # To use specific voice: voice=tts.get_preset_voice("VoiceName")
        temperature=1.0, 
        top_k=50
    )
    tts.save(audio, "output.wav")
    print("💾 Saved: output.wav")

    # ---------------------------------------------------------
    # CLEANUP
    # ---------------------------------------------------------
    tts.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    main()