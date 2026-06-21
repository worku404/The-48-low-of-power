import os
import uuid
from flask import Flask, request, g
from app.services.content import ContentService
from app.services.likes import LikesService
from app.services.tts import TTSService

def create_app(test_config=None):
    # Initialize the Flask application
    app = Flask(__name__, instance_relative_config=True)
    
    # Configure default settings
    app.config.from_mapping(
        DATABASE_PATH=os.path.join(app.instance_path, 'likes.sqlite3'),
        AUDIO_CACHE_DIR=os.path.join(app.instance_path, 'audio_cache'),
        CONTENT_JSON_PATH=os.path.join(app.root_path, '..', 'data', 'sections.json'),
        SECRET_KEY='dev-key-placeholder-for-session-fallback'
    )

    if test_config:
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['AUDIO_CACHE_DIR'], exist_ok=True)

    # Initialize Services and attach to app context or app config
    content_service = ContentService(data_path=app.config['CONTENT_JSON_PATH'])
    likes_service = LikesService(db_path=app.config['DATABASE_PATH'])
    tts_service = TTSService(cache_dir=app.config['AUDIO_CACHE_DIR'])
    
    # Store services on the app object for easy retrieval in blueprints/routes
    app.content_service = content_service
    app.likes_service = likes_service
    app.tts_service = tts_service

    # Register context teardown for database connections
    app.teardown_appcontext(LikesService.close_db)

    # Before request hook to ensure every visitor has a tracking cookie
    @app.before_request
    def ensure_visitor_id():
        if 'visitor_id' not in request.cookies:
            # Generate a new unique tracking identifier
            g.visitor_id = str(uuid.uuid4())
            g.visitor_id_new = True
        else:
            g.visitor_id = request.cookies.get('visitor_id')
            g.visitor_id_new = False

    # After request hook to set the cookie in the browser
    @app.after_request
    def set_visitor_cookie(response):
        if getattr(g, 'visitor_id_new', False):
            # Set cookie for 1 year, secure/httponly for standard tracking
            response.set_cookie(
                'visitor_id',
                g.visitor_id,
                max_age=365 * 24 * 60 * 60,  # 1 year in seconds
                httponly=True,
                samesite='Lax'
            )
        return response

    # Register blueprints and routes
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
