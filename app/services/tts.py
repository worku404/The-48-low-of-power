import os
import hashlib
from google import genai
from google.genai import types

class TTSError(Exception):
    """Base exception class for TTS Service errors."""
    pass

class EmptyContentError(TTSError):
    """Raised when text content is empty or only whitespace."""
    pass

class MissingAPIKeyError(TTSError):
    """Raised when Gemini API key is missing."""
    pass

class GeminiAPIError(TTSError):
    """Raised when the Gemini API returns an error or invalid response."""
    pass

class TTSService:
    def __init__(self, cache_dir=None, model_name="gemini-2.5-flash-preview-tts", voice_name="Aoede", api_key=None):
        self._cache_dir = cache_dir
        self.model_name = model_name
        self.voice_name = voice_name
        self._api_key = api_key
        self._client = None

    @property
    def cache_dir(self):
        if self._cache_dir is None:
            from flask import current_app
            self._cache_dir = os.path.join(current_app.instance_path, 'audio_cache')
        return self._cache_dir

    def _get_client(self):
        """Lazy initializer for google-genai client."""
        if self._client is None:
            api_key = self._api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise MissingAPIKeyError("Gemini API key is not configured. Please set GEMINI_API_KEY.")
            self._client = genai.Client(api_key=api_key)
        return self._client

    def get_audio_path(self, text):
        """
        Computes SHA256 of the text, checks if audio is cached,
        generates and caches it if missing, and returns the absolute file path.
        """
        if not text or not text.strip():
            raise EmptyContentError("Cannot generate TTS audio for empty content.")

        # Compute content hash
        text_utf8 = text.strip().encode('utf-8')
        text_hash = hashlib.sha256(text_utf8).hexdigest()
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        cache_file_path = os.path.join(self.cache_dir, f"{text_hash}.mp3")

        # Cache Hit
        if os.path.exists(cache_file_path):
            return cache_file_path

        # Cache Miss - Generate using Gemini API
        client = self._get_client()
        try:
            # Configure request for audio output modality
            config = types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=self.voice_name
                        )
                    )
                ),
            )

            # Invoke model for text recitation
            prompt = f"Please read the following Amharic text aloud exactly as written, with clear, natural pronunciation:\n\n{text}"
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )

            # Defensive parsing of API response content structure
            if not response.candidates:
                raise GeminiAPIError("Gemini API returned no candidates.")
            candidate = response.candidates[0]
            if candidate.content is None:
                reason = getattr(candidate, 'finish_reason', 'unknown')
                raise GeminiAPIError(f"Gemini API returned a candidate with no content (finish_reason={reason}).")
            if not candidate.content.parts:
                raise GeminiAPIError("Gemini API returned an empty response candidate.")

            part = response.candidates[0].content.parts[0]
            if not part.inline_data or not part.inline_data.data:
                raise GeminiAPIError("Gemini API response did not contain inline audio bytes.")

            audio_bytes = part.inline_data.data

            import wave
            import io
            # Write a proper WAV container around the raw PCM bytes in memory
            # Pad to even length if needed (16-bit samples must be 2-byte aligned)
            pcm_data = audio_bytes
            if len(pcm_data) % 2 != 0:
                pcm_data = pcm_data + b'\x00'

            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)       # Mono
                wav_file.setsampwidth(2)       # 16-bit (2 bytes per sample)
                wav_file.setframerate(24000)   # 24 kHz sample rate
                wav_file.writeframes(pcm_data)

            # Atomically write the completed WAV buffer to disk
            wav_bytes = wav_buffer.getvalue()
            os.makedirs(self.cache_dir, exist_ok=True)
            with open(cache_file_path, 'wb') as f:
                f.write(wav_bytes)

            return cache_file_path

        except Exception as e:
            if isinstance(e, (EmptyContentError, MissingAPIKeyError, GeminiAPIError)):
                raise e
            raise GeminiAPIError(f"Failed to generate audio via Gemini API: {str(e)}") from e
