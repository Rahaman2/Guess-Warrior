# Family Feud Game MVP

A classic Family Feud game with semantic answer matching and spelling understanding.

## Features

- Classic Family Feud TV show UI (blue/red theme, flip cards, strike X's)
- Fuzzy answer matching (handles typos and spelling variations)
- 1,063 questions loaded from CSV
- Sound effects (ding, buzzer, strike)
- Modular architecture ready for WebSocket multiplayer

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the game:
```bash
python app.py
```

3. Open your browser to: **http://localhost:5000**

## How to Play

1. Read the question displayed at the top
2. Type your answer in the input field
3. Press SUBMIT or hit Enter
4. If your answer matches (even with typos!), it will reveal and add points
5. Wrong answers give you a strike (3 strikes = game over)
6. Guess all answers to win!

## Project Structure

```
Guess-Warrior/
├── app.py                    # Flask app entry point
├── config.py                 # Configuration
├── questions.csv             # Questions database
├── models/                   # Data models
│   ├── question.py          # Question & Answer models
│   └── game.py              # Game state model
├── services/                 # Business logic
│   ├── question_service.py  # Load questions from CSV
│   ├── matching_service.py  # Fuzzy matching logic
│   └── game_service.py      # Game logic & state
├── routes/                   # API endpoints
│   └── game_routes.py       # Game API routes
├── static/                   # Frontend assets
│   ├── css/style.css        # Classic Feud styling
│   ├── js/game.js           # Frontend game logic
│   └── sounds/              # Sound effects
└── templates/                # HTML templates
    └── game.html            # Main game page
```

## API Endpoints

- `GET /` - Main game page
- `POST /api/game/start` - Start new game with random question
- `POST /api/game/guess` - Submit answer guess
- `GET /api/game/state` - Get current game state

## Fuzzy Matching

Uses `rapidfuzz` library with 80% similarity threshold. Examples:
- "car" matches "cars" ✓
- "bakon" matches "bacon" ✓
- "christmass" matches "christmas" ✓
- "automobil" matches "automobile" ✓

## Future Enhancements

- [ ] WebSocket multiplayer support
- [ ] Multiple rounds per game session
- [ ] Team play mode
- [ ] Leaderboard
- [ ] Better sound effects
- [ ] Mobile responsive improvements

## Tech Stack

- **Backend**: Python + Flask
- **Frontend**: Vanilla JavaScript + HTML/CSS
- **Matching**: rapidfuzz (free, no paid APIs)
- **No external dependencies** for core gameplay
