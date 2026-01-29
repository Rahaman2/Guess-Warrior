"""Service for fuzzy and semantic matching user input to answers."""

import re
from typing import Optional, List
from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer, util
from models.question import Answer


class MatchingService:
    """Service to match user input to correct answers using fuzzy and semantic matching."""

    def __init__(self, threshold: int = 80, semantic_threshold: float = 0.55):
        """
        Initialize the MatchingService.

        Args:
            threshold: Minimum similarity percentage (0-100) for fuzzy match
            semantic_threshold: Minimum cosine similarity (0.0-1.0) for semantic match
        """
        self.threshold = threshold
        self.semantic_threshold = semantic_threshold
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    @staticmethod
    def normalize(text: str) -> str:
        """
        Normalize text for matching by removing punctuation and extra spaces.

        Args:
            text: Input text to normalize

        Returns:
            Normalized text (lowercase, no punctuation, trimmed)
        """
        # Convert to lowercase
        text = text.lower()
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text

    def _fuzzy_match(self, user_input: str, correct_answers: List[Answer]) -> tuple[Optional[Answer], int]:
        """
        Try to match using fuzzy string matching.

        Returns:
            Tuple of (matched Answer or None, best score)
        """
        normalized_input = self.normalize(user_input)
        best_match = None
        best_score = 0

        for answer in correct_answers:
            normalized_answer = self.normalize(answer.text)
            similarity = fuzz.ratio(normalized_input, normalized_answer)
            partial_similarity = fuzz.partial_ratio(normalized_input, normalized_answer)
            score = max(similarity, partial_similarity)

            if score > best_score:
                best_score = score
                best_match = answer

        if best_score >= self.threshold:
            return best_match, best_score
        return None, best_score

    def _semantic_match(self, user_input: str, correct_answers: List[Answer]) -> Optional[Answer]:
        """
        Try to match using semantic similarity via sentence-transformers.

        Returns:
            Matched Answer or None
        """
        input_embedding = self.model.encode(user_input, convert_to_tensor=True)
        answer_texts = [a.text for a in correct_answers]
        answer_embeddings = self.model.encode(answer_texts, convert_to_tensor=True)

        cosine_scores = util.cos_sim(input_embedding, answer_embeddings)[0]

        best_idx = cosine_scores.argmax().item()
        best_score = cosine_scores[best_idx].item()

        if best_score >= self.semantic_threshold:
            return correct_answers[best_idx]
        return None

    def match_answer(self, user_input: str, correct_answers: List[Answer]) -> Optional[Answer]:
        """
        Match user input against correct answers using fuzzy matching first,
        then falling back to semantic similarity.

        Args:
            user_input: The user's guess
            correct_answers: List of correct Answer objects

        Returns:
            Matched Answer object or None if no match found
        """
        if not user_input or not correct_answers:
            return None

        # First try fuzzy matching (fast, handles typos and close strings)
        fuzzy_result, _ = self._fuzzy_match(user_input, correct_answers)
        if fuzzy_result:
            return fuzzy_result

        # Fall back to semantic matching (handles synonyms like "educator" -> "teacher")
        return self._semantic_match(user_input, correct_answers)

    def get_match_quality(self, user_input: str, answer_text: str) -> int:
        """
        Get the match quality percentage between user input and an answer.

        Args:
            user_input: The user's guess
            answer_text: The correct answer text

        Returns:
            Match quality percentage (0-100)
        """
        normalized_input = self.normalize(user_input)
        normalized_answer = self.normalize(answer_text)

        similarity = fuzz.ratio(normalized_input, normalized_answer)
        partial_similarity = fuzz.partial_ratio(normalized_input, normalized_answer)

        return max(similarity, partial_similarity)
