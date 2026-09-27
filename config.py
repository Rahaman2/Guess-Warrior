"""Configuration settings for Family Feud game."""

import os


class Config:
    """Base configuration."""

    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'family-feud-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', '1') == '1'

    # Game settings
    QUESTIONS_CSV_PATH = 'questions.csv'
    MATCHING_THRESHOLD = 80  # Fuzzy match threshold percentage (0-100)
    SEMANTIC_THRESHOLD = 0.55  # Semantic cosine similarity threshold (0.0-1.0)

    # Server settings
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5000))
