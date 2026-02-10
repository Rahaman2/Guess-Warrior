"""Family Feud Game - Flask Application Entry Point."""

from flask import Flask, render_template
from flask_socketio import SocketIO
from config import Config
from services import QuestionService, MatchingService, GameService
from services.multiplayer_service import MultiplayerService
from routes import game_bp
from routes.game_routes import init_routes
from routes.multiplayer_events import init_multiplayer


def create_app(config_class=Config):
    """
    Application factory pattern.

    Args:
        config_class: Configuration class to use

    Returns:
        Tuple of (Flask app, SocketIO instance)
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

    # Initialize services
    question_service = QuestionService(app.config['QUESTIONS_CSV_PATH'])
    matching_service = MatchingService(
        app.config['MATCHING_THRESHOLD'],
        app.config['SEMANTIC_THRESHOLD']
    )
    game_service = GameService(question_service, matching_service)

    # Initialize single-player routes
    init_routes(game_service)
    app.register_blueprint(game_bp)

    # Initialize multiplayer
    mp_service = MultiplayerService(question_service, matching_service)
    init_multiplayer(socketio, mp_service)

    @app.route('/multiplayer')
    def multiplayer_page():
        return render_template('multiplayer.html')

    return app, socketio


if __name__ == '__main__':
    print("=" * 50)
    print("Family Feud Game Starting...")
    print("=" * 50)

    app, socketio = create_app()

    print(f"\n[OK] Server ready at http://localhost:{app.config['PORT']}")
    print(f"[OK] Single player: http://localhost:{app.config['PORT']}/")
    print(f"[OK] Multiplayer:   http://localhost:{app.config['PORT']}/multiplayer")
    print("[OK] Press Ctrl+C to stop\n")

    socketio.run(
        app,
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
