"""Multiplayer room and player models."""

from dataclasses import dataclass, field
from typing import Dict, Optional
from enum import Enum
import string
import random
from .question import Question
from .game import Game


class RoomState(Enum):
    """State of a multiplayer room."""
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"


@dataclass
class Player:
    """A player in a multiplayer room."""
    sid: str
    name: str
    game: Optional[Game] = None
    is_host: bool = False


@dataclass
class Room:
    """A multiplayer game room."""
    code: str
    question: Optional[Question] = None
    state: RoomState = RoomState.WAITING
    players: Dict[str, 'Player'] = field(default_factory=dict)
    timer_seconds: int = 60
    time_remaining: int = 60
    started_at: Optional[float] = None

    @staticmethod
    def generate_code(length: int = 4) -> str:
        """Generate a short uppercase room code."""
        return ''.join(random.choices(string.ascii_uppercase, k=length))

    def add_player(self, sid: str, name: str, is_host: bool = False) -> 'Player':
        player = Player(sid=sid, name=name, is_host=is_host)
        self.players[sid] = player
        return player

    def remove_player(self, sid: str) -> Optional['Player']:
        return self.players.pop(sid, None)

    def is_full(self) -> bool:
        return len(self.players) >= 2

    def get_opponent(self, sid: str) -> Optional['Player']:
        for player_sid, player in self.players.items():
            if player_sid != sid:
                return player
        return None

    def init_player_games(self, question: Question) -> None:
        """Give each player their own Game instance with the same Question."""
        self.question = question
        for player in self.players.values():
            player.game = Game(question=question)

    def to_lobby_dict(self) -> dict:
        return {
            "code": self.code,
            "state": self.state.value,
            "players": [
                {"name": p.name, "is_host": p.is_host}
                for p in self.players.values()
            ],
        }

    def to_game_dict(self, for_sid: str) -> dict:
        """Game state from a specific player's perspective."""
        player = self.players.get(for_sid)
        opponent = self.get_opponent(for_sid)

        answers = []
        if self.question and player and player.game:
            for i, ans in enumerate(self.question.answers):
                my_revealed = player.game.revealed_answers[i]
                opp_revealed = opponent.game.revealed_answers[i] if opponent and opponent.game else False
                answers.append({
                    "text": ans.text if my_revealed else None,
                    "points": ans.points if my_revealed else None,
                    "revealed_by_me": my_revealed,
                    "revealed_by_opponent": opp_revealed,
                })

        return {
            "code": self.code,
            "state": self.state.value,
            "question": self.question.question_text if self.question else None,
            "time_remaining": self.time_remaining,
            "answers": answers,
            "answer_count": len(self.question.answers) if self.question else 0,
            "my_score": player.game.score if player and player.game else 0,
            "my_strikes": player.game.strikes if player and player.game else 0,
            "opponent_score": opponent.game.score if opponent and opponent.game else 0,
            "opponent_name": opponent.name if opponent else None,
            "my_name": player.name if player else None,
        }
