"""
VieNeu-TTS SDK Example: Remote Mode
Version: 1.1.3
"""

from vieneu import Vieneu
import os

def main():
    print("🚀 Initializing VieNeu Remote Client...")
    
    # ---------------------------------------------------------
    # PART 0: PRE-REQUISITES & CONFIG
    # ---------------------------------------------------------
    # Ensure output directory exists
    os.makedirs("outputs", exist_ok=True)
    
    # Replace with your actual LMDeploy server URL
    # Example: 'http://localhost:23333/v1' or a public tunnel URL
    REMOTE_API_BASE = 'http://bore.pub:31631/v1' # Replace with your actual LMDeploy server URL
    REMOTE_MODEL_ID = "pnnbao-ump/VieNeu-TTS"

    # ---------------------------------------------------------
    # PART 1: INITIALIZATION
    # ---------------------------------------------------------
    # Remote mode is LIGHTWEIGHT: It doesn't load the heavy 0.3B/0.5B model locally.
    # It only loads a small Codec (distill-neucodec) to encode/decode audio instantly.
    print(f"📡 Connecting to server: {REMOTE_API_BASE}...")
    try:
        tts = Vieneu(
            mode='remote', 
            api_base=REMOTE_API_BASE, 
            model_name=REMOTE_MODEL_ID
        )
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return

    # ---------------------------------------------------------
    # PART 2: LIST REMOTE VOICES
    # ---------------------------------------------------------
    # Fetch available voice presets from the remote server
    available_voices = tts.list_preset_voices()
    print(f"📋 Found {len(available_voices)} remote voices.")
    
    if available_voices:
        print("   Showing all voices:")
        for desc, name in available_voices:
            print(f"   - {desc} (ID: {name})")

    # ---------------------------------------------------------
    # PART 3: USE SPECIFIC VOICE ID
    # ---------------------------------------------------------
    if available_voices:
        print("\n--- PART 3: Using Specific Voice ID ---")
        # Select a voice by its ID (the second element in the tuple)
        _, my_voice_id = available_voices[1] if len(available_voices) > 1 else available_voices[0]
        print(f"👤 Selecting voice: {my_voice_id}")
        
        # Get reference data for this specific voice
        voice_data = tts.get_preset_voice(my_voice_id)
        
        test_text = f"Chào bạn, tôi đang nói bằng giọng của bác sĩ Tuyên."
        audio_spec = tts.infer(text=test_text, voice=voice_data)
        
        tts.save(audio_spec, f"outputs/remote_{my_voice_id}.wav")
        print(f"💾 Saved {my_voice_id} synthesis to: outputs/remote_{my_voice_id}.wav")

    # ---------------------------------------------------------
    # PART 4: REMOTE SPEECH SYNTHESIS (DEFAULT)
    # ---------------------------------------------------------
    print("\n--- PART 4: Standard Synthesis (Default) ---")
    text_input = "Chế độ remote giúp tích hợp VieNeu vào ứng dụng Web hoặc App cực nhanh mà không cần GPU tại máy khách."
    
    print("🎧 Sending synthesis request to server...")
    # The SDK handles splitting long text and joining results automatically
    audio = tts.infer(text=text_input)
    
    tts.save(audio, "outputs/remote_output.wav")
    print("💾 Saved remote synthesis to: outputs/remote_output.wav")

    # ---------------------------------------------------------
    # PART 5: ZERO-SHOT VOICE CLONING (REMOTE)
    # ---------------------------------------------------------
    # Even in remote mode, you can still clone voices!
    # STEP: The SDK encodes the audio LOCALLY first, then sends 'codes' to the server.
    ref_audio = "examples/audio_ref/example_ngoc_huyen.wav"
    ref_text = "Tác phẩm dự thi bảo đảm tính khoa học, tính đảng, tính chiến đấu, tính định hướng."
    
    if os.path.exists(ref_audio):
        print("\n--- PART 5: Remote Voice Cloning ---")
        print(f"🦜 Encoding {ref_audio} locally and sending codes to server...")
        cloned_audio = tts.infer(
            text="Đây là giọng nói được clone và xử lý thông qua VieNeu Server.",
            ref_audio=ref_audio,
            ref_text=ref_text
        )
        tts.save(cloned_audio, "outputs/remote_cloned_output.wav")
        print("💾 Saved remote cloned voice to: outputs/remote_cloned_output.wav")

    # ---------------------------------------------------------
    # PART 6: DONE
    # ---------------------------------------------------------
    print("\n✅ Remote tasks completed!")

if __name__ == "__main__":
    main()
