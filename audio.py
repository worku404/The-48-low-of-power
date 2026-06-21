import os
import sys
import json
import time
import wave
import hashlib
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Reconfigure stdout to use UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# Set up API keys for rotation
API_KEYS = [
    os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"),
    "AIzaSyAPz05mZQM8pSMbkqh6sBF2ykkU4T--BYU",
    "AIzaSyA3HrseCAZuzDyACqPGD0rZYUg8zDFw3Cg",
    "AIzaSyC7qvyqoRd53AhHj5Y9L8Pt3utl44wm6WM"
]
API_KEYS = [k for k in API_KEYS if k]

print(f"Configured {len(API_KEYS)} API keys for key-rotation.")

sections_path = r"c:\Users\hi\Downloads\webdev\The_48_low_of_power\data\sections.json"
audio_cache_dir = r"c:\Users\hi\Downloads\webdev\The_48_low_of_power\instance\audio_cache"
os.makedirs(audio_cache_dir, exist_ok=True)

# Helper function to split text into chunks of max_chars
def split_text(text, max_chars=1500):
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []
    current_len = 0
    
    for p in paragraphs:
        p_len = len(p)
        if current_len + p_len + 2 > max_chars:
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_len = 0
            if p_len > max_chars:
                lines = p.split('\n')
                for line in lines:
                    line_len = len(line)
                    if current_len + line_len + 1 > max_chars:
                        if current_chunk:
                            chunks.append("\n".join(current_chunk))
                            current_chunk = []
                            current_len = 0
                        if line_len > max_chars:
                            # Absolute fallback: hard character split
                            for i in range(0, line_len, max_chars):
                                chunks.append(line[i:i+max_chars])
                        else:
                            current_chunk.append(line)
                            current_len = line_len
                    else:
                        current_chunk.append(line)
                        current_len += line_len + 1
            else:
                current_chunk.append(p)
                current_len = p_len
        else:
            current_chunk.append(p)
            current_len += p_len + 2
            
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
        
    return [c.strip() for c in chunks if c.strip()]

# Load sections.json
with open(sections_path, "r", encoding="utf-8") as f:
    sections = json.load(f)

key_index = 0
def get_client():
    global key_index
    api_key = API_KEYS[key_index % len(API_KEYS)]
    print(f"Using API key index {key_index % len(API_KEYS)} (ending in ...{api_key[-6:]})")
    return genai.Client(api_key=api_key)

def rotate_key():
    global key_index
    key_index += 1
    print(f"Rotating key... New index: {key_index % len(API_KEYS)}")

def generate_chunk_audio(text_chunk):
    config = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Aoede"
                )
            )
        )
    )
    prompt = f"Please read the following Amharic text aloud exactly as written, with clear,smooth,  natural pronunciation:\n\n{text_chunk}"
    
    max_retries = 6
    for attempt in range(max_retries):
        client = get_client()
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=prompt,
                config=config
            )
            
            if not response.candidates:
                raise ValueError("No candidates returned.")
            candidate = response.candidates[0]
            if candidate.content is None:
                reason = getattr(candidate, 'finish_reason', 'unknown')
                raise ValueError(f"No content in response (finish_reason={reason})")
            part = candidate.content.parts[0]
            if not part.inline_data or not part.inline_data.data:
                raise ValueError("No inline data in response part")
                
            return part.inline_data.data
        except Exception as e:
            err_str = str(e)
            print(f"Error on attempt {attempt+1}/{max_retries}: {err_str}")
            rotate_key()
            if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                sleep_time = 25
            else:
                sleep_time = 10
            print(f"Sleeping {sleep_time}s before retry...")
            time.sleep(sleep_time)
            
    raise RuntimeError("All retries exhausted for chunk.")

def merge_pcm_chunks_to_wav(pcm_chunks, out_wav_path):
    print(f"Merging chunks into: {out_wav_path}")
    combined_pcm = b""
    for data in pcm_chunks:
        if len(data) % 2 != 0:
            data += b'\x00'
        combined_pcm += data
        
    with wave.open(out_wav_path, 'wb') as wav:
        wav.setnchannels(1)       # Mono
        wav.setsampwidth(2)       # 16-bit
        wav.setframerate(24000)   # 24 kHz
        wav.writeframes(combined_pcm)
        
    print(f"Saved merged WAV to {out_wav_path} (size: {os.path.getsize(out_wav_path):,} bytes)")

# Main execution loop for Laws 7 to 10
for law_id in range(10, 26):
    section = next((s for s in sections if s["id"] == law_id), None)
    if not section:
        print(f"Error: Law {law_id} not found in sections.json.")
        continue
        
    body = section.get("body", "").strip()
    if not body:
        print(f"Error: Law {law_id} body is empty. Skipping.")
        continue
        
    # Calculate hash
    text_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()
    output_wav = os.path.join(audio_cache_dir, f"{text_hash}.wav")
    
    print(f"\n=========================================")
    print(f"Processing Law {law_id}...")
    print(f"Expected file hash: {text_hash}")
    print(f"Output path: {output_wav}")
    print(f"=========================================")
    
    if os.path.exists(output_wav):
        print(f"Audio already exists in cache. Skipping generation.")
        continue
        
    # Split text into chunks
    chunks = split_text(body, max_chars=1500)
    print(f"Split Law {law_id} text ({len(body)} chars) into {len(chunks)} chunk(s).")
    
    pcm_chunks = []
    failed = False
    for i, chunk in enumerate(chunks):
        print(f"\n--- Generating chunk {i+1}/{len(chunks)} ({len(chunk)} chars) ---")
        try:
            pcm_data = generate_chunk_audio(chunk)
            pcm_chunks.append(pcm_data)
            print(f"Successfully generated chunk {i+1} ({len(pcm_data)} audio bytes).")
            # Be polite to the rate limits
            time.sleep(5)
        except Exception as e:
            print(f"Fatal error generating chunk {i+1} for Law {law_id}: {e}")
            failed = True
            break
            
    if not failed and pcm_chunks:
        try:
            merge_pcm_chunks_to_wav(pcm_chunks, output_wav)
            print(f"✅ Law {law_id} audio is completed successfully!")
        except Exception as e:
            print(f"Failed to merge chunks for Law {law_id}: {e}")
    else:
        print(f"❌ Failed to generate audio for Law {law_id}.")
        
print("\nAll tasks completed.")
