"""Family Feud Game - Flask Application Entry Point."""

from flask import Flask
from config import Config
from services import QuestionService, MatchingService, GameService
from routes import game_bp
from routes.game_routes import init_routes


def create_app(config_class=Config):
    """
    Application factory pattern.

    Args:
        config_class: Configuration class to use

    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize services
    question_service = QuestionService(app.config['QUESTIONS_CSV_PATH'])
    matching_service = MatchingService(
        app.config['MATCHING_THRESHOLD'],
        app.config['SEMANTIC_THRESHOLD']
    )
    game_service = GameService(question_service, matching_service)

    # Initialize routes with game service
    init_routes(game_service)

    # Register blueprints
    app.register_blueprint(game_bp)

    return app


if __name__ == '__main__':
    print("=" * 50)
    print("Family Feud Game Starting...")
    print("=" * 50)

    app = create_app()

    print(f"\n[OK] Server ready at http://localhost:{app.config['PORT']}")
    print("[OK] Press Ctrl+C to stop\n")

    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
