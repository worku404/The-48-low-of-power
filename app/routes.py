from flask import Blueprint, render_template, current_app, request, jsonify, g, send_file
from app.services.tts import EmptyContentError, MissingAPIKeyError, GeminiAPIError

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # Load all sections
    sections = current_app.content_service.get_all_sections()
    
    # Identify requested law, default to Law 1
    law_id_str = request.args.get('law', '1')
    try:
        law_id = int(law_id_str)
    except ValueError:
        law_id = 1

    # Fetch active section
    active_section = current_app.content_service.get_section(law_id)
    if not active_section:
        active_section = current_app.content_service.get_section(1)
        law_id = 1

    # Fetch likes metadata for active section
    likes_count = current_app.likes_service.get_likes(law_id)
    has_liked = current_app.likes_service.has_liked(getattr(g, 'visitor_id', None), law_id)

    return render_template(
        'index.html',
        sections=sections,
        active_section=active_section,
        likes_count=likes_count,
        has_liked=has_liked
    )

@bp.route('/api/sections/<int:section_id>')
def get_section_api(section_id):
    section = current_app.content_service.get_section(section_id)
    if not section:
        return jsonify({'error': 'Section not found'}), 404

    # Fetch likes metrics
    likes_count = current_app.likes_service.get_likes(section_id)
    has_liked = current_app.likes_service.has_liked(getattr(g, 'visitor_id', None), section_id)

    # Return section info along with likes data
    return jsonify({
        'id': section['id'],
        'label': section['label'],
        'title': section['title'],
        'body': section['body'],
        'language': section['language'],
        'likes': likes_count,
        'liked': has_liked
    })

@bp.route('/api/sections/<int:section_id>/like', methods=['POST'])
def like_section_api(section_id):
    section = current_app.content_service.get_section(section_id)
    if not section:
        return jsonify({'error': 'Section not found'}), 404

    visitor_id = getattr(g, 'visitor_id', None)
    if not visitor_id:
        return jsonify({'error': 'Visitor cookie not available'}), 400

    likes_count, success = current_app.likes_service.add_like(visitor_id, section_id)
    
    return jsonify({
        'likes': likes_count,
        'liked': True
    })

@bp.route('/api/sections/<int:section_id>/audio')
def get_section_audio_api(section_id):
    section = current_app.content_service.get_section(section_id)
    if not section:
        return jsonify({'error': 'Section not found'}), 404

    body_text = section.get('body', '').strip()
    if not body_text:
        return jsonify({'error': 'Cannot generate audio for empty content (Coming soon)'}), 400

    try:
        # Call TTS service (resolves cache check and Gemini call)
        audio_path = current_app.tts_service.get_audio_path(body_text)
        return send_file(audio_path, mimetype='audio/wav', as_attachment=False)
        
    except EmptyContentError as e:
        return jsonify({'error': str(e)}), 400
    except MissingAPIKeyError as e:
        # 503 Service Unavailable, custom header indicating missing API setup
        return jsonify({'error': str(e), 'details': 'TTS_KEY_MISSING'}), 503
    except GeminiAPIError as e:
        # 502 Bad Gateway
        return jsonify({'error': str(e)}), 502
    except Exception as e:
        return jsonify({'error': f"An unexpected audio retrieval error occurred: {str(e)}"}), 500
