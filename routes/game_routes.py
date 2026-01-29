"""Game routes for Family Feud game API."""

from flask import Blueprint, render_template, jsonify, request
from services import GameService

game_bp = Blueprint('game', __name__)

# This will be injected by the app
game_service: GameService = None


def init_routes(service: GameService):
    """
    Initialize routes with the game service.

    Args:
        service: GameService instance
    """
    global game_service
    game_service = service


@game_bp.route('/')
def index():
    """Serve the main game page."""
    return render_template('game.html')


@game_bp.route('/api/game/start', methods=['POST'])
def start_game():
    """
    Start a new game with a random question.

    Returns:
        JSON response with game state
    """
    try:
        game = game_service.start_new_game()

        if not game:
            return jsonify({
                "success": False,
                "error": "No questions available"
            }), 500

        return jsonify({
            "success": True,
            "data": game_service.get_game_state()
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@game_bp.route('/api/game/guess', methods=['POST'])
def submit_guess():
    """
    Submit a guess for the current question.

    Expected JSON body:
        {
            "guess": "user's answer"
        }

    Returns:
        JSON response with match result and updated game state
    """
    try:
        data = request.get_json()

        if not data or 'guess' not in data:
            return jsonify({
                "success": False,
                "error": "No guess provided"
            }), 400

        guess = data['guess']
        result = game_service.process_guess(guess)

        return jsonify({
            "success": True,
            "data": {
                "result": result,
                "game_state": game_service.get_game_state()
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@game_bp.route('/api/game/state', methods=['GET'])
def get_state():
    """
    Get the current game state.

    Returns:
        JSON response with current game state
    """
    try:
        state = game_service.get_game_state()

        if not state:
            return jsonify({
                "success": False,
                "error": "No active game"
            }), 404

        return jsonify({
            "success": True,
            "data": state
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
