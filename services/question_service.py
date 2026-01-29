"""Service for loading and managing questions from CSV."""

import csv
import random
from typing import List, Optional
from models.question import Question, Answer


class QuestionService:
    """Service to load and provide questions from CSV file."""

    def __init__(self, csv_path: str = "questions.csv"):
        """
        Initialize the QuestionService.

        Args:
            csv_path: Path to the questions CSV file
        """
        self.csv_path = csv_path
        self.questions: List[Question] = []
        self.load_questions()

    def load_questions(self) -> None:
        """Load questions from CSV file into Question objects."""
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    question = self._parse_row(row)
                    if question:
                        self.questions.append(question)

            print(f"[OK] Loaded {len(self.questions)} questions from {self.csv_path}")

        except FileNotFoundError:
            print(f"Error: CSV file not found at {self.csv_path}")
            raise
        except Exception as e:
            print(f"Error loading questions: {e}")
            raise

    def _parse_row(self, row: dict) -> Optional[Question]:
        """
        Parse a CSV row into a Question object.

        Args:
            row: Dictionary representing a CSV row

        Returns:
            Question object or None if invalid
        """
        try:
            question_text = row.get('Question', '').strip()
            if not question_text:
                return None

            answers = []
            # CSV has Answer 1, #1, Answer 2, #2, etc.
            for i in range(1, 7):  # Up to 6 answers
                answer_key = f'Answer {i}'
                points_key = f'#{i}'

                answer_text = row.get(answer_key, '').strip()
                points_str = row.get(points_key, '').strip()

                if answer_text and points_str:
                    try:
                        points = int(points_str)
                        answers.append(Answer(text=answer_text, points=points))
                    except ValueError:
                        continue

            if answers:
                return Question(question_text=question_text, answers=answers)

        except Exception as e:
            print(f"Error parsing row: {e}")

        return None

    def get_random_question(self) -> Optional[Question]:
        """
        Get a random question from the loaded questions.

        Returns:
            Random Question object or None if no questions available
        """
        if not self.questions:
            return None
        return random.choice(self.questions)

    def get_question_count(self) -> int:
        """Get the total number of loaded questions."""
        return len(self.questions)
