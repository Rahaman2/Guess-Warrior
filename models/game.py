"""Game state model."""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from .question import Question, Answer


class GameState(Enum):
    """Enum representing the current state of the game."""
    PLAYING = "playing"
    WON = "won"
    LOST = "lost"


@dataclass
class Game:
    """Represents the current state of a Family Feud game session."""
    question: Question
    revealed_answers: List[bool] = field(default_factory=list)
    score: int = 0
    strikes: int = 0
    state: GameState = GameState.PLAYING
    guessed_answers: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize revealed_answers list based on number of answers."""
        if not self.revealed_answers:
            self.revealed_answers = [False] * len(self.question.answers)

    def reveal_answer(self, answer: Answer) -> None:
        """
        Reveal an answer and add its points to the score.

        Args:
            answer: The Answer object to reveal
        """
        for i, ans in enumerate(self.question.answers):
            if ans.text == answer.text and not self.revealed_answers[i]:
                self.revealed_answers[i] = True
                self.score += answer.points
                break

    def add_strike(self) -> None:
        """Add a strike and check if game is lost."""
        self.strikes += 1
        if self.strikes >= 3:
            self.state = GameState.LOST

    def check_win(self) -> bool:
        """Check if all answers have been revealed."""
        if all(self.revealed_answers):
            self.state = GameState.WON
            return True
        return False

    def is_game_over(self) -> bool:
        """Check if the game is over (won or lost)."""
        return self.state in [GameState.WON, GameState.LOST]

    def add_guessed_answer(self, guess: str) -> None:
        """Track guessed answers to prevent duplicates."""
        self.guessed_answers.append(guess.lower().strip())

    def has_guessed(self, guess: str) -> bool:
        """Check if an answer has already been guessed."""
        return guess.lower().strip() in self.guessed_answers

    def to_dict(self) -> dict:
        """Convert game state to dictionary for JSON serialization."""
        return {
            "question": self.question.question_text,
            "answers": [
                {
                    "text": answer.text,
                    "points": answer.points,
                    "revealed": self.revealed_answers[i]
                }
                for i, answer in enumerate(self.question.answers)
            ],
            "score": self.score,
            "strikes": self.strikes,
            "state": self.state.value,
            "guessed_answers": self.guessed_answers
        }
