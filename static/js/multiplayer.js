/**
 * Multiplayer Family Feud - Frontend Controller
 * Uses SocketIO for real-time communication.
 */

class MultiplayerGame {
    constructor() {
        this.socket = io();
        this.roomCode = null;
        this.isHost = false;
        this.gameData = null;

        this.sounds = {
            ding: document.getElementById('dingSound'),
            buzzer: document.getElementById('buzzerSound'),
            strike: document.getElementById('strikeSound')
        };

        this.elements = {
            // Lobby
            lobbyView: document.getElementById('lobbyView'),
            gameView: document.getElementById('gameView'),
            playerNameInput: document.getElementById('playerNameInput'),
            createRoomBtn: document.getElementById('createRoomBtn'),
            joinRoomBtn: document.getElementById('joinRoomBtn'),
            roomCodeInput: document.getElementById('roomCodeInput'),
            waitingRoom: document.getElementById('waitingRoom'),
            roomCodeDisplay: document.getElementById('roomCodeDisplay'),
            playerList: document.getElementById('playerList'),
            waitingMessage: document.getElementById('waitingMessage'),
            startGameBtn: document.getElementById('startGameBtn'),
            lobbyMessage: document.getElementById('lobbyMessage'),

            // Game
            questionText: document.getElementById('questionText'),
            answersGrid: document.getElementById('answersGrid'),
            answerInput: document.getElementById('answerInput'),
            submitBtn: document.getElementById('submitBtn'),
            myScore: document.getElementById('myScore'),
            myName: document.getElementById('myName'),
            opponentScore: document.getElementById('opponentScore'),
            opponentName: document.getElementById('opponentName'),
            timer: document.getElementById('timer'),
            strikes: document.getElementById('strikes'),
            message: document.getElementById('message'),

            // Modal
            modal: document.getElementById('gameOverModal'),
            modalTitle: document.getElementById('modalTitle'),
            modalMessage: document.getElementById('modalMessage'),
            resultsTable: document.getElementById('resultsTable'),
            allAnswers: document.getElementById('allAnswers'),
            playAgainBtn: document.getElementById('playAgainBtn')
        };

        this.initSocketEvents();
        this.initUIEvents();
    }

    initUIEvents() {
        this.elements.createRoomBtn.addEventListener('click', () => this.createRoom());
        this.elements.joinRoomBtn.addEventListener('click', () => this.joinRoom());
        this.elements.startGameBtn.addEventListener('click', () => this.startGame());
        this.elements.submitBtn.addEventListener('click', () => this.submitGuess());
        this.elements.answerInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.submitGuess();
        });
        this.elements.playAgainBtn.addEventListener('click', () => this.playAgain());
        this.elements.playerNameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.elements.createRoomBtn.click();
        });
        this.elements.roomCodeInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.joinRoom();
        });
        // Auto-uppercase room code input
        this.elements.roomCodeInput.addEventListener('input', (e) => {
            e.target.value = e.target.value.toUpperCase();
        });
    }

    initSocketEvents() {
        this.socket.on('room_created', (data) => this.onRoomCreated(data));
        this.socket.on('player_joined', (data) => this.onPlayerJoined(data));
        this.socket.on('join_error', (data) => this.showLobbyMessage(data.message, 'error'));
        this.socket.on('game_started', (data) => this.onGameStarted(data));
        this.socket.on('guess_result', (data) => this.onGuessResult(data));
        this.socket.on('opponent_revealed', (data) => this.onOpponentRevealed(data));
        this.socket.on('timer_tick', (data) => this.onTimerTick(data));
        this.socket.on('game_over', (data) => this.onGameOver(data));
        this.socket.on('player_left', (data) => this.onPlayerLeft(data));
        this.socket.on('room_reset', (data) => this.onRoomReset(data));
        this.socket.on('error', (data) => this.showMessage(data.message, 'error'));
        this.socket.on('disconnect', () => this.showLobbyMessage('Disconnected from server', 'error'));
    }

    // --- Actions ---

    createRoom() {
        const name = this.elements.playerNameInput.value.trim() || 'Player 1';
        this.isHost = true;
        this.socket.emit('create_room', { player_name: name });
        this.elements.createRoomBtn.disabled = true;
        this.elements.joinRoomBtn.disabled = true;
    }

    joinRoom() {
        const name = this.elements.playerNameInput.value.trim() || 'Player 2';
        const code = this.elements.roomCodeInput.value.trim().toUpperCase();
        if (!code) {
            this.showLobbyMessage('Enter a room code', 'error');
            return;
        }
        this.socket.emit('join_room', { room_code: code, player_name: name });
    }

    startGame() {
        this.elements.startGameBtn.disabled = true;
        this.socket.emit('start_game');
    }

    submitGuess() {
        const guess = this.elements.answerInput.value.trim();
        if (!guess) return;
        this.socket.emit('submit_guess', { guess });
        this.elements.answerInput.value = '';
        this.elements.answerInput.focus();
    }

    playAgain() {
        this.elements.modal.classList.remove('active');
        this.socket.emit('play_again');
    }

    // --- Socket Event Handlers ---

    onRoomCreated(data) {
        this.roomCode = data.code;
        this.elements.roomCodeDisplay.textContent = data.code;
        this.elements.waitingRoom.style.display = 'block';
        this.renderPlayerList(data.players);

        if (this.isHost) {
            this.elements.waitingMessage.textContent = 'Waiting for opponent...';
            this.elements.startGameBtn.style.display = 'none';
        }
    }

    onPlayerJoined(data) {
        this.roomCode = data.code;
        this.elements.roomCodeDisplay.textContent = data.code;
        this.elements.waitingRoom.style.display = 'block';
        this.renderPlayerList(data.players);

        // Disable lobby actions for the joiner
        this.elements.createRoomBtn.disabled = true;
        this.elements.joinRoomBtn.disabled = true;

        if (this.isHost && data.players.length >= 2) {
            this.elements.waitingMessage.textContent = 'Ready to start!';
            this.elements.startGameBtn.style.display = 'block';
            this.elements.startGameBtn.disabled = false;
        } else if (!this.isHost) {
            this.elements.waitingMessage.textContent = 'Waiting for host to start...';
        }
    }

    onGameStarted(data) {
        this.gameData = data;

        // Switch to game view
        this.elements.lobbyView.style.display = 'none';
        this.elements.gameView.style.display = 'flex';

        // Set names
        this.elements.myName.textContent = (data.my_name || 'YOU').toUpperCase();
        this.elements.opponentName.textContent = (data.opponent_name || 'OPPONENT').toUpperCase();

        // Render board
        this.renderBoard(data);
        this.elements.myScore.textContent = data.my_score;
        this.elements.opponentScore.textContent = data.opponent_score;
        this.elements.timer.textContent = data.time_remaining;

        // Reset strikes
        this.updateStrikes(0);

        // Focus input
        this.elements.answerInput.disabled = false;
        this.elements.submitBtn.disabled = false;
        this.elements.answerInput.focus();
    }

    onGuessResult(data) {
        if (data.matched) {
            this.playSound('ding');
            this.showMessage(data.message, 'success');
            this.revealMyAnswer(data.answer.index, data.answer.text, data.answer.points);

            // Update score from the answer points
            const currentScore = parseInt(this.elements.myScore.textContent) || 0;
            this.elements.myScore.textContent = currentScore + data.answer.points;
        } else {
            if (data.message === 'You already guessed that!' || data.message === 'Already revealed!') {
                this.showMessage(data.message, 'error');
            } else {
                this.playSound('strike');
                this.showMessage(data.message, 'error');
                if (data.strikes !== undefined) {
                    this.updateStrikes(data.strikes);
                }
            }
        }
    }

    onOpponentRevealed(data) {
        const card = document.getElementById(`answer-${data.answer_index}`);
        if (card && !card.classList.contains('revealed')) {
            card.classList.add('opponent-revealed');
        }
        this.elements.opponentScore.textContent = data.opponent_score;
    }

    onTimerTick(data) {
        const remaining = data.time_remaining;
        this.elements.timer.textContent = remaining;

        if (remaining <= 10) {
            this.elements.timer.classList.add('urgent');
        } else {
            this.elements.timer.classList.remove('urgent');
        }
    }

    onGameOver(data) {
        // Disable input
        this.elements.answerInput.disabled = true;
        this.elements.submitBtn.disabled = true;

        // Title
        if (data.winner) {
            const myName = this.elements.myName.textContent;
            if (data.winner.toUpperCase() === myName) {
                this.elements.modalTitle.textContent = 'YOU WIN!';
                this.elements.modalMessage.textContent = 'Congratulations!';
            } else {
                this.elements.modalTitle.textContent = 'YOU LOSE!';
                this.elements.modalMessage.textContent = `${data.winner} wins!`;
            }
        } else {
            this.elements.modalTitle.textContent = "IT'S A TIE!";
            this.elements.modalMessage.textContent = 'Great minds think alike!';
        }

        // Results table
        this.elements.resultsTable.innerHTML = '';
        data.players.forEach((p, i) => {
            const row = document.createElement('div');
            row.className = `result-row${i === 0 && data.winner ? ' winner' : ''}`;
            row.innerHTML = `
                <div>
                    <div>${p.name}</div>
                    <div class="result-details">${p.answers_found} answers, ${p.strikes} strikes</div>
                </div>
                <div class="result-score">${p.score}</div>
            `;
            this.elements.resultsTable.appendChild(row);
        });

        // All answers
        if (data.all_answers && data.all_answers.length > 0) {
            this.elements.allAnswers.innerHTML = `
                <div class="all-answers-title">ALL ANSWERS</div>
                <div class="all-answers-list">
                    ${data.all_answers.map(a =>
                        `<div class="answer-item">${a.text} <span class="answer-item-points">${a.points}</span></div>`
                    ).join('')}
                </div>
            `;
        }

        this.elements.modal.classList.add('active');
    }

    onPlayerLeft(data) {
        this.showMessage(`${data.player_name} left the game`, 'error');
        // If during game, end it
        if (this.elements.gameView.style.display !== 'none') {
            setTimeout(() => {
                this.elements.answerInput.disabled = true;
                this.elements.submitBtn.disabled = true;
                this.elements.modalTitle.textContent = 'OPPONENT LEFT';
                this.elements.modalMessage.textContent = `${data.player_name} disconnected.`;
                this.elements.resultsTable.innerHTML = '';
                this.elements.allAnswers.innerHTML = '';
                this.elements.modal.classList.add('active');
            }, 1500);
        }
    }

    onRoomReset(data) {
        this.elements.modal.classList.remove('active');
        this.elements.gameView.style.display = 'none';
        this.elements.lobbyView.style.display = 'flex';
        this.renderPlayerList(data.players);

        if (this.isHost && data.players.length >= 2) {
            this.elements.waitingMessage.textContent = 'Ready to start!';
            this.elements.startGameBtn.style.display = 'block';
            this.elements.startGameBtn.disabled = false;
        } else if (this.isHost) {
            this.elements.waitingMessage.textContent = 'Waiting for opponent...';
            this.elements.startGameBtn.style.display = 'none';
        } else {
            this.elements.waitingMessage.textContent = 'Waiting for host to start...';
        }
    }

    // --- Rendering ---

    renderPlayerList(players) {
        this.elements.playerList.innerHTML = '';
        players.forEach(p => {
            const item = document.createElement('div');
            item.className = 'player-list-item';
            item.innerHTML = `<span>${p.name}</span>${p.is_host ? '<span class="host-badge">HOST</span>' : ''}`;
            this.elements.playerList.appendChild(item);
        });
    }

    renderBoard(data) {
        this.elements.questionText.textContent = data.question;
        this.elements.answersGrid.innerHTML = '';
        for (let i = 0; i < data.answer_count; i++) {
            const answer = data.answers[i];
            const card = document.createElement('div');
            card.className = 'answer-card hidden';
            card.id = `answer-${i}`;

            const content = document.createElement('div');
            content.className = 'answer-content';
            content.style.display = 'flex';
            content.style.width = '100%';
            content.style.alignItems = 'center';
            content.style.justifyContent = 'space-between';

            const number = document.createElement('div');
            number.className = 'answer-number';
            number.textContent = i + 1;
            content.appendChild(number);

            card.appendChild(content);

            // Opponent indicator dot
            const dot = document.createElement('div');
            dot.className = 'opp-indicator';
            card.appendChild(dot);

            this.elements.answersGrid.appendChild(card);
        }
    }

    revealMyAnswer(index, text, points) {
        const card = document.getElementById(`answer-${index}`);
        if (!card) return;

        card.classList.remove('hidden', 'opponent-revealed');
        card.classList.add('revealed');

        const content = card.querySelector('.answer-content');
        content.innerHTML = '';

        const number = document.createElement('div');
        number.className = 'answer-number';
        number.textContent = index + 1;

        const textEl = document.createElement('div');
        textEl.className = 'answer-text';
        textEl.textContent = text;

        const pointsEl = document.createElement('div');
        pointsEl.className = 'answer-points';
        pointsEl.textContent = points;

        content.appendChild(number);
        content.appendChild(textEl);
        content.appendChild(pointsEl);
    }

    updateStrikes(strikes) {
        for (let i = 1; i <= 3; i++) {
            const el = document.getElementById(`strike${i}`);
            if (el) {
                if (i <= strikes) {
                    el.classList.add('active');
                } else {
                    el.classList.remove('active');
                }
            }
        }
    }

    // --- Utility ---

    showMessage(text, type) {
        this.elements.message.textContent = text;
        this.elements.message.className = `message ${type}`;
        if (text && type) {
            setTimeout(() => {
                this.elements.message.className = 'message';
                this.elements.message.textContent = '';
            }, 3000);
        }
    }

    showLobbyMessage(text, type) {
        this.elements.lobbyMessage.textContent = text;
        this.elements.lobbyMessage.className = `message ${type}`;
        if (text && type) {
            setTimeout(() => {
                this.elements.lobbyMessage.className = 'message';
                this.elements.lobbyMessage.textContent = '';
            }, 3000);
        }
    }

    playSound(soundName) {
        try {
            const sound = this.sounds[soundName];
            if (sound) {
                sound.currentTime = 0;
                sound.play().catch(e => console.log('Sound play failed:', e));
            }
        } catch (error) {
            console.log('Error playing sound:', error);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.multiplayerGame = new MultiplayerGame();
});
