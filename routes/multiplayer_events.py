"""SocketIO event handlers for multiplayer."""

import time as _time
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
from models.multiplayer import RoomState
from models.round_config import BETWEEN_ROUND_DELAY
from services.multiplayer_service import MultiplayerService

socketio: SocketIO = None
mp_service: MultiplayerService = None


def init_multiplayer(sio: SocketIO, service: MultiplayerService):
    """Wire up SocketIO instance and multiplayer service."""
    global socketio, mp_service
    socketio = sio
    mp_service = service
    _register_events(sio)


def _register_events(sio: SocketIO):

    @sio.on('connect')
    def handle_connect():
        print(f"[MP] Client connected: {request.sid}")

    @sio.on('disconnect')
    def handle_disconnect():
        sid = request.sid
        room = mp_service.get_room_for_player(sid)
        room_code = room.code if room else None

        result = mp_service.disconnect_player(sid)
        if result:
            _room, removed_player = result
            if room_code:
                sio.emit('player_left', {
                    'player_name': removed_player.name,
                }, room=room_code)
        print(f"[MP] Client disconnected: {sid}")

    @sio.on('create_room')
    def handle_create_room(data):
        player_name = data.get('player_name', 'Player 1').strip()[:20] or 'Player 1'
        room = mp_service.create_room(request.sid, player_name)
        join_room(room.code)
        emit('room_created', room.to_lobby_dict())
        print(f"[MP] Room {room.code} created by {player_name}")

    @sio.on('join_room')
    def handle_join_room(data):
        code = data.get('room_code', '')
        player_name = data.get('player_name', 'Player 2').strip()[:20] or 'Player 2'
        room, error = mp_service.join_room(code, request.sid, player_name)
        if not room:
            emit('join_error', {'message': error})
            return
        join_room(room.code)
        sio.emit('player_joined', room.to_lobby_dict(), room=room.code)
        print(f"[MP] {player_name} joined room {room.code}")

    @sio.on('start_game')
    def handle_start_game(data=None):
        room = mp_service.get_room_for_player(request.sid)
        if not room:
            emit('error', {'message': 'Not in a room'})
            return
        player = room.players.get(request.sid)
        if not player or not player.is_host:
            emit('error', {'message': 'Only host can start'})
            return
        if not room.is_full():
            emit('error', {'message': 'Need 2 players to start'})
            return

        started_room = mp_service.start_game(room.code)
        if not started_room:
            emit('error', {'message': 'Failed to start game'})
            return

        # Send personalized game state to each player
        for sid in started_room.players:
            sio.emit('game_started', started_room.to_game_dict(sid), room=sid)

        # Start server-side timer
        _start_timer(started_room.code)
        print(f"[MP] Match started in room {started_room.code} - Round 1")

    @sio.on('submit_guess')
    def handle_submit_guess(data):
        guess = data.get('guess', '')
        result = mp_service.process_guess(request.sid, guess)
        if result is None:
            emit('error', {'message': 'Invalid state'})
            return

        room = mp_service.get_room_for_player(request.sid)

        # Send result to the guessing player
        emit('guess_result', result)

        # If matched, notify opponent
        if result.get('matched') and room:
            opponent = room.get_opponent(request.sid)
            if opponent:
                player = room.players.get(request.sid)
                sio.emit('opponent_revealed', {
                    'answer_index': result['answer']['index'],
                    'opponent_score': player.game.score if player and player.game else 0,
                }, room=opponent.sid)

            # Board cleared -> end round
            if result.get('board_cleared'):
                _end_round(room.code)

    @sio.on('next_round')
    def handle_next_round(data=None):
        room = mp_service.get_room_for_player(request.sid)
        if not room:
            return
        player = room.players.get(request.sid)
        if not player or not player.is_host:
            emit('error', {'message': 'Only host can advance'})
            return
        if room.state != RoomState.ROUND_ENDED:
            return
        started_room = mp_service.advance_round(room.code)
        if not started_room:
            return
        for sid in started_room.players:
            sio.emit('game_started', started_room.to_game_dict(sid), room=sid)
        _start_timer(started_room.code)
        print(f"[MP] Round {started_room.current_round} started in room {room.code} (host advanced)")

    @sio.on('play_again')
    def handle_play_again(data=None):
        room = mp_service.get_room_for_player(request.sid)
        if not room:
            return
        room.state = RoomState.WAITING
        room.time_remaining = room.timer_seconds
        room.started_at = None
        room.current_round = 0
        room.used_questions = []
        for p in room.players.values():
            p.game = None
            p.total_score = 0
            p.round_scores = []
        sio.emit('room_reset', room.to_lobby_dict(), room=room.code)


def _start_timer(room_code: str):
    """Run server-side 1-second timer ticks."""
    def timer_loop():
        while True:
            _time.sleep(1)
            remaining = mp_service.tick_timer(room_code)
            if remaining is None:
                break
            socketio.emit('timer_tick', {'time_remaining': remaining}, room=room_code)
            if remaining <= 0:
                _end_round(room_code)
                break

    socketio.start_background_task(timer_loop)


def _end_round(room_code: str):
    """Finalize the current round and emit appropriate events."""
    round_summary = mp_service.end_round(room_code)
    if not round_summary:
        return

    if round_summary["is_final_round"]:
        # Match is over -- emit final results
        results = mp_service.get_results(room_code)
        if results:
            # Include the last round summary so the client can show it
            results["last_round_summary"] = round_summary
            socketio.emit('match_over', results, room=room_code)
            print(f"[MP] Match over in room {room_code} - Winner: {results.get('winner', 'Tie')}")
    else:
        # Emit round summary, then auto-advance after delay
        socketio.emit('round_ended', round_summary, room=room_code)
        print(f"[MP] Round {round_summary['current_round']} ended in room {room_code}")
        _schedule_next_round(room_code)


def _schedule_next_round(room_code: str):
    """Auto-advance to next round after a delay."""
    def advance():
        _time.sleep(BETWEEN_ROUND_DELAY)
        room = mp_service.rooms.get(room_code)
        if not room or room.state != RoomState.ROUND_ENDED:
            return  # host already advanced, or room gone
        started_room = mp_service.advance_round(room_code)
        if not started_room:
            return
        for sid in started_room.players:
            socketio.emit('game_started', started_room.to_game_dict(sid), room=sid)
        _start_timer(started_room.code)
        print(f"[MP] Round {started_room.current_round} auto-started in room {room_code}")

    socketio.start_background_task(advance)
