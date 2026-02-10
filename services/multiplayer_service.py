"""Service for managing multiplayer rooms and game logic."""

import time
from typing import Dict, Optional, Any, Tuple
from models.multiplayer import Room, RoomState, Player
from models.game import GameState
from services.question_service import QuestionService
from services.matching_service import MatchingService


class MultiplayerService:
    """Manages all active multiplayer rooms."""

    def __init__(self, question_service: QuestionService, matching_service: MatchingService):
        self.question_service = question_service
        self.matching_service = matching_service
        self.rooms: Dict[str, Room] = {}
        self.player_rooms: Dict[str, str] = {}

    def create_room(self, sid: str, player_name: str) -> Room:
        code = Room.generate_code()
        while code in self.rooms:
            code = Room.generate_code()
        room = Room(code=code)
        room.add_player(sid, player_name, is_host=True)
        self.rooms[code] = room
        self.player_rooms[sid] = code
        return room

    def join_room(self, code: str, sid: str, player_name: str) -> Tuple[Optional[Room], str]:
        """Returns (room, error_message). Room is None on failure."""
        code = code.upper().strip()
        room = self.rooms.get(code)
        if not room:
            return None, "Room not found"
        if room.is_full():
            return None, "Room is full"
        if room.state != RoomState.WAITING:
            return None, "Game already in progress"
        room.add_player(sid, player_name, is_host=False)
        self.player_rooms[sid] = code
        return room, ""

    def start_game(self, room_code: str) -> Optional[Room]:
        """Initialize question and player games."""
        room = self.rooms.get(room_code)
        if not room or not room.is_full():
            return None
        question = self.question_service.get_random_question()
        if not question:
            return None
        room.init_player_games(question)
        room.state = RoomState.PLAYING
        room.time_remaining = room.timer_seconds
        room.started_at = time.time()
        return room

    def process_guess(self, sid: str, guess: str) -> Optional[Dict[str, Any]]:
        """Process a guess for a multiplayer player."""
        room_code = self.player_rooms.get(sid)
        if not room_code:
            return None
        room = self.rooms.get(room_code)
        if not room or room.state != RoomState.PLAYING:
            return None

        player = room.players.get(sid)
        if not player or not player.game:
            return None

        game = player.game

        if not guess or not guess.strip():
            return {"matched": False, "message": "Please enter an answer", "answer": None}
        if game.has_guessed(guess):
            return {"matched": False, "message": "You already guessed that!", "answer": None}

        game.add_guessed_answer(guess)

        matched_answer = self.matching_service.match_answer(guess, room.question.answers)

        if matched_answer:
            answer_index = room.question.answers.index(matched_answer)
            if game.revealed_answers[answer_index]:
                return {"matched": False, "message": "Already revealed!", "answer": None}

            game.reveal_answer(matched_answer)
            # Override the LOST state from strikes - in multiplayer strikes are cosmetic
            if game.state == GameState.LOST:
                game.state = GameState.PLAYING
            board_cleared = game.check_win()

            return {
                "matched": True,
                "answer": {"text": matched_answer.text, "points": matched_answer.points, "index": answer_index},
                "message": f"Correct! {matched_answer.text} - {matched_answer.points} points!",
                "board_cleared": board_cleared,
                "player_sid": sid,
            }
        else:
            game.add_strike()
            # Override the LOST state - in multiplayer strikes are cosmetic
            if game.state == GameState.LOST:
                game.state = GameState.PLAYING
            return {
                "matched": False,
                "answer": None,
                "message": "Strike!",
                "strikes": game.strikes,
            }

    def tick_timer(self, room_code: str) -> Optional[int]:
        """Decrement timer. Returns remaining seconds, or None if room gone."""
        room = self.rooms.get(room_code)
        if not room or room.state != RoomState.PLAYING:
            return None
        room.time_remaining -= 1
        if room.time_remaining <= 0:
            room.time_remaining = 0
            room.state = RoomState.FINISHED
        return room.time_remaining

    def get_results(self, room_code: str) -> Optional[Dict[str, Any]]:
        """Get final results for a finished game."""
        room = self.rooms.get(room_code)
        if not room:
            return None
        players = []
        for p in room.players.values():
            players.append({
                "name": p.name,
                "score": p.game.score if p.game else 0,
                "strikes": p.game.strikes if p.game else 0,
                "answers_found": sum(p.game.revealed_answers) if p.game else 0,
            })
        players.sort(key=lambda x: x["score"], reverse=True)
        winner = None
        if len(players) >= 2 and players[0]["score"] != players[1]["score"]:
            winner = players[0]["name"]
        return {
            "winner": winner,
            "players": players,
            "question": room.question.question_text if room.question else "",
            "all_answers": [
                {"text": a.text, "points": a.points}
                for a in room.question.answers
            ] if room.question else [],
        }

    def get_room_for_player(self, sid: str) -> Optional[Room]:
        code = self.player_rooms.get(sid)
        return self.rooms.get(code) if code else None

    def disconnect_player(self, sid: str) -> Optional[Tuple[Room, Player]]:
        """Handle player disconnect. Returns (room, removed_player) or None."""
        code = self.player_rooms.pop(sid, None)
        if not code:
            return None
        room = self.rooms.get(code)
        if not room:
            return None
        removed = room.remove_player(sid)
        if not room.players:
            del self.rooms[code]
            return (room, removed) if removed else None
        return (room, removed) if removed else None

    def cleanup_room(self, code: str) -> None:
        """Remove a room entirely."""
        room = self.rooms.pop(code, None)
        if room:
            for sid in list(room.players.keys()):
                self.player_rooms.pop(sid, None)
