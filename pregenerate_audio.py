import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to python path to import the app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.tts import TTSError

def pregenerate_all_audio():
    print("Initializing Flask App context...")
    app = create_app()
    
    with app.app_context():
        content_service = app.content_service
        tts_service = app.tts_service
        
        sections = content_service.get_all_sections()
        translated_sections = [s for s in sections if s.get('body', '').strip()]
        
        if not translated_sections:
            print("No translated laws found to generate audio for.")
            return
            
        print(f"Found {len(translated_sections)} translated law(s). Pregenerating audio...")
        
        # Verify API key is present
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            print("Error: GEMINI_API_KEY is not set in the environment or .env file.")
            print("Please add 'GEMINI_API_KEY=your_key' to your .env file and try again.")
            return

        for section in translated_sections:
            law_id = section['id']
            label = section['label']
            text = section['body']
            
            print(f"Processing {label}...", end="", flush=True)
            try:
                # This will generate and save the audio if it is a cache miss
                audio_path = tts_service.get_audio_path(text)
                print(f" Done! Saved to: {os.path.basename(audio_path)}")
            except TTSError as e:
                print(f" Failed: {str(e)}")
            except Exception as e:
                print(f" Error: {str(e)}")

if __name__ == '__main__':
    pregenerate_all_audio()
