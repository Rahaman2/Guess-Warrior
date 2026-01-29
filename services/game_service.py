"""Service for managing game logic and state."""

from typing import Optional, Dict, Any
from models.game import Game, GameState
from models.question import Question, Answer
from .question_service import QuestionService
from .matching_service import MatchingService


class GameService:
    """Service to manage Family Feud game logic and state."""

    def __init__(self, question_service: QuestionService, matching_service: MatchingService):
        """
        Initialize the GameService.

        Args:
            question_service: Service for loading questions
            matching_service: Service for matching user input
        """
        self.question_service = question_service
        self.matching_service = matching_service
        self.current_game: Optional[Game] = None

    def start_new_game(self) -> Optional[Game]:
        """
        Start a new game with a random question.

        Returns:
            New Game object or None if no questions available
        """
        question = self.question_service.get_random_question()
        if not question:
            return None

        self.current_game = Game(question=question)
        return self.current_game

    def process_guess(self, guess: str) -> Dict[str, Any]:
        """
        Process a user's guess and update game state.

        Args:
            guess: The user's answer guess

        Returns:
            Dictionary with result information:
            {
                "matched": bool,
                "answer": Answer object or None,
                "message": str,
                "game_over": bool,
                "state": GameState value
            }
        """
        if not self.current_game or self.current_game.is_game_over():
            return {
                "matched": False,
                "answer": None,
                "message": "No active game",
                "game_over": True,
                "state": None
            }

        # Check if guess is empty
        if not guess or not guess.strip():
            return {
                "matched": False,
                "answer": None,
                "message": "Please enter an answer",
                "game_over": False,
                "state": self.current_game.state.value
            }

        # Check if already guessed
        if self.current_game.has_guessed(guess):
            return {
                "matched": False,
                "answer": None,
                "message": "You already guessed that!",
                "game_over": False,
                "state": self.current_game.state.value
            }

        # Track this guess
        self.current_game.add_guessed_answer(guess)

        # Try to match the guess
        matched_answer = self.matching_service.match_answer(
            guess,
            self.current_game.question.answers
        )

        if matched_answer:
            # Check if this answer was already revealed
            answer_index = self.current_game.question.answers.index(matched_answer)
            if self.current_game.revealed_answers[answer_index]:
                return {
                    "matched": False,
                    "answer": None,
                    "message": "That answer is already revealed!",
                    "game_over": False,
                    "state": self.current_game.state.value
                }

            # Correct answer - reveal it
            self.current_game.reveal_answer(matched_answer)
            self.current_game.check_win()

            return {
                "matched": True,
                "answer": {
                    "text": matched_answer.text,
                    "points": matched_answer.points,
                    "index": answer_index
                },
                "message": f"Correct! {matched_answer.text} - {matched_answer.points} points!",
                "game_over": self.current_game.is_game_over(),
                "state": self.current_game.state.value
            }
        else:
            # Wrong answer - add strike
            self.current_game.add_strike()

            return {
                "matched": False,
                "answer": None,
                "message": "Wrong answer! Strike!",
                "game_over": self.current_game.is_game_over(),
                "state": self.current_game.state.value
            }

    def get_game_state(self) -> Optional[Dict[str, Any]]:
        """
        Get the current game state.

        Returns:
            Dictionary representation of game state or None
        """
        if not self.current_game:
            return None
        return self.current_game.to_dict()

    def reset_game(self) -> None:
        """Reset the current game."""
        self.current_game = None
