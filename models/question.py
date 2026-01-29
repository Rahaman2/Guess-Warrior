"""Question and Answer data models."""

from dataclasses import dataclass
from typing import List


@dataclass
class Answer:
    """Represents a single answer with its text and point value."""
    text: str
    points: int

    def __str__(self):
        return f"{self.text} ({self.points})"


@dataclass
class Question:
    """Represents a Family Feud question with multiple answers."""
    question_text: str
    answers: List[Answer]

    def __post_init__(self):
        """Sort answers by points in descending order."""
        self.answers.sort(key=lambda x: x.points, reverse=True)

    def get_total_points(self) -> int:
        """Calculate total possible points for this question."""
        return sum(answer.points for answer in self.answers)

    def __str__(self):
        answers_str = ", ".join([str(a) for a in self.answers])
        return f"Q: {self.question_text}\nA: [{answers_str}]"
