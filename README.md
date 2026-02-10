# Family Feud Game MVP

A classic Family Feud game with semantic answer matching, spelling understanding, and real-time multiplayer.

## Features

- Classic Family Feud TV show UI (blue/red theme, flip cards, strike X's)
- Fuzzy + semantic answer matching (handles typos, spelling variations, and synonyms)
- 1,063 questions loaded from CSV
- Sound effects (ding, buzzer, strike)
- Real-time multiplayer via WebSocket (room-based, 2 players)
- 60-second timed multiplayer rounds
- Modular architecture (single-player REST + multiplayer SocketIO side by side)

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the game:
```bash
python app.py
```

3. Open your browser:
   - **Single Player**: http://localhost:5000
   - **Multiplayer**: http://localhost:5000/multiplayer

## How to Play

### Single Player
1. Read the question displayed at the top
2. Type your answer in the input field
3. Press SUBMIT or hit Enter
4. If your answer matches (even with typos!), it will reveal and add points
5. Wrong answers give you a strike (3 strikes = game over)
6. Guess all answers to win!

### Multiplayer
1. Go to `/multiplayer` and enter your name
2. **Player 1**: Click CREATE ROOM and share the 4-letter room code
3. **Player 2**: Enter the room code and click JOIN
4. Host clicks START GAME -- both players get the same question
5. Race to guess answers for 60 seconds -- scores are independent
6. Highest score when the timer runs out (or someone clears the board) wins!

## Project Structure

```
Guess-Warrior/
├── app.py                           # Flask + SocketIO entry point
├── config.py                        # Configuration
├── questions.csv                    # Questions database (1,063 questions)
├── models/                          # Data models
│   ├── question.py                 # Question & Answer models
│   ├── game.py                     # Game state model
│   └── multiplayer.py              # Room, Player, RoomState models
├── services/                        # Business logic
│   ├── question_service.py         # Load questions from CSV
│   ├── matching_service.py         # Fuzzy + semantic matching
│   ├── game_service.py             # Single-player game logic
│   └── multiplayer_service.py      # Multiplayer room & game logic
├── routes/                          # Endpoints
│   ├── game_routes.py              # Single-player REST API
│   └── multiplayer_events.py       # Multiplayer WebSocket events
├── static/                          # Frontend assets
│   ├── css/
│   │   ├── style.css               # Base styling
│   │   └── multiplayer.css         # Multiplayer-specific styles
│   ├── js/
│   │   ├── game.js                 # Single-player frontend
│   │   └── multiplayer.js          # Multiplayer frontend (SocketIO)
│   └── sounds/                     # Sound effects
└── templates/
    ├── game.html                   # Single-player page
    └── multiplayer.html            # Multiplayer page
```

## API & Events

### Single Player (REST)
- `GET /` - Single-player game page
- `POST /api/game/start` - Start new game with random question
- `POST /api/game/guess` - Submit answer guess
- `GET /api/game/state` - Get current game state

### Multiplayer (WebSocket)
- `GET /multiplayer` - Multiplayer game page
- `create_room` - Create a new room (returns room code)
- `join_room` - Join an existing room by code
- `start_game` - Host starts the game
- `submit_guess` - Submit a guess during gameplay
- `play_again` - Reset room for another round

## Fuzzy Matching

Uses `rapidfuzz` library with 80% similarity threshold, with semantic matching fallback via `sentence-transformers`. Examples:
- "car" matches "cars"
- "bakon" matches "bacon"
- "christmass" matches "christmas"
- "automobil" matches "automobile"

## Future Enhancements

- [x] WebSocket multiplayer support
- [x] Timed game rounds
- [ ] Mobile app with auto-matching (no room codes)
- [ ] Multiple rounds per game session
- [ ] Team play mode
- [ ] Leaderboard

## Tech Stack

- **Backend**: Python, Flask, Flask-SocketIO
- **Frontend**: Vanilla JavaScript, HTML/CSS
- **Matching**: rapidfuzz + sentence-transformers
- **Real-time**: WebSocket via SocketIO (threading async mode)
