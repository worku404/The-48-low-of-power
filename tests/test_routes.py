import pytest
import json

def test_home_page_renders_with_visitor_cookie(client):
    response = client.get('/')
    assert response.status_code == 200
    # Checks if cookie header was sent
    cookie_header = response.headers.get('Set-Cookie')
    assert cookie_header is not None
    assert 'visitor_id=' in cookie_header
    
    # Verify default Law 1 is rendered
    html = response.data.decode('utf-8')
    assert 'Law 1' in html
    assert 'የሙከራ ርዕስ 1' in html

def test_deep_linking_law_parameter(client):
    # Retrieve law=2 deep link
    response = client.get('/?law=2')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert 'Law 2' in html
    assert 'የሙከራ ርዕስ 2' in html

def test_invalid_law_parameter_fallbacks(client):
    # Invalid string parameter defaults to Law 1
    response = client.get('/?law=invalid')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert 'Law 1' in html

    # Out of bounds parameter defaults to Law 1
    response = client.get('/?law=100')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert 'Law 1' in html

def test_get_section_json_api(client):
    response = client.get('/api/sections/1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == 1
    assert data['label'] == 'Law 1'
    assert data['title'] == 'የሙከራ ርዕስ 1'
    assert 'የሙከራ ይዘት እዚህ ይገኛል' in data['body']
    assert data['likes'] == 0
    assert data['liked'] is False

def test_get_nonexistent_section_api(client):
    response = client.get('/api/sections/99')
    assert response.status_code == 404

def test_like_section_api(client):
    # Get a visitor cookie session
    client.get('/')
    
    # Call like API
    response = client.post('/api/sections/1/like')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['likes'] == 1
    assert data['liked'] is True

    # Check updated GET API values
    get_response = client.get('/api/sections/1')
    get_data = json.loads(get_response.data)
    assert get_data['likes'] == 1
    assert get_data['liked'] is True
