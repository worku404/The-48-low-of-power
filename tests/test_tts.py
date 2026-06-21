import os
import pytest
from unittest.mock import MagicMock, patch
from app.services.tts import TTSService, EmptyContentError, MissingAPIKeyError, GeminiAPIError

# --- Mock structures mimicking google-genai Response ---
class MockInlineData:
    def __init__(self, data):
        self.data = data

class MockPart:
    def __init__(self, data):
        self.inline_data = MockInlineData(data)

class MockContent:
    def __init__(self, data):
        self.parts = [MockPart(data)]

class MockCandidate:
    def __init__(self, data):
        self.content = MockContent(data)

class MockResponse:
    def __init__(self, data):
        self.candidates = [MockCandidate(data)]

def test_tts_rejects_empty_content(app):
    with app.app_context():
        service = app.tts_service
        
        with pytest.raises(EmptyContentError):
            service.get_audio_path("")
            
        with pytest.raises(EmptyContentError):
            service.get_audio_path("   ")

def test_tts_raises_missing_api_key(app):
    with app.app_context():
        # Instantiate a custom service with no keys
        service = TTSService(cache_dir=app.config['AUDIO_CACHE_DIR'], api_key=None)
        
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(MissingAPIKeyError):
                service.get_audio_path("እዚህ Amharic content")

@patch('app.services.tts.genai.Client')
def test_tts_cache_miss_and_hit(mock_client_class, app):
    # Setup mock behavior
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    expected_bytes = b"mocked-binary-audio-wav-data"
    mock_client.models.generate_content.return_value = MockResponse(expected_bytes)

    with app.app_context():
        service = app.tts_service
        # Pass a mock API key to bypass key check
        service._api_key = "mock-key"
        
        text = "ይህ የሙከራ የአማርኛ ጽሑፍ ነው።"
        
        # 1. First Call: Cache Miss (API is called)
        path1 = service.get_audio_path(text)
        assert os.path.exists(path1)
        import wave
        with wave.open(path1, 'rb') as f:
            assert f.getnchannels() == 1
            assert f.getsampwidth() == 2
            assert f.getframerate() == 24000
            assert f.readframes(f.getnframes()) == expected_bytes
        
        assert mock_client.models.generate_content.call_count == 1
        
        # 2. Second Call: Cache Hit (API is NOT called, file retrieved from local folder)
        path2 = service.get_audio_path(text)
        assert path1 == path2
        assert mock_client.models.generate_content.call_count == 1

@patch('app.services.tts.genai.Client')
def test_audio_endpoints(mock_client_class, client):
    # Setup mock behavior for endpoints integration
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    expected_bytes = b"endpoint-mocked-wav-data"
    mock_client.models.generate_content.return_value = MockResponse(expected_bytes)
    
    # Inject fake API key to routes context
    client.application.tts_service._api_key = "mock-key"

    # Test GET audio endpoint for seeded Law 1
    response = client.get('/api/sections/1/audio')
    assert response.status_code == 200
    assert response.content_type == 'audio/wav'
    import wave
    import io
    with wave.open(io.BytesIO(response.data), 'rb') as f:
        assert f.getnchannels() == 1
        assert f.getsampwidth() == 2
        assert f.getframerate() == 24000
        assert f.readframes(f.getnframes()) == expected_bytes
    response.close()

    # Test GET audio endpoint for untranslated Law 3 (empty body)
    response_empty = client.get('/api/sections/3/audio')
    assert response_empty.status_code == 400
    assert b"Cannot generate audio for empty content" in response_empty.data
    response_empty.close()
