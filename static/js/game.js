/**
 * Family Feud Game - Frontend Controller
 */

class FamilyFeudGame {
    constructor() {
        this.gameState = null;
        this.sounds = {
            ding: document.getElementById('dingSound'),
            buzzer: document.getElementById('buzzerSound'),
            strike: document.getElementById('strikeSound')
        };

        // DOM elements
        this.elements = {
            questionText: document.getElementById('questionText'),
            answersGrid: document.getElementById('answersGrid'),
            answerInput: document.getElementById('answerInput'),
            submitBtn: document.getElementById('submitBtn'),
            score: document.getElementById('score'),
            strikes: document.getElementById('strikes'),
            message: document.getElementById('message'),
            modal: document.getElementById('gameOverModal'),
            modalTitle: document.getElementById('modalTitle'),
            modalMessage: document.getElementById('modalMessage'),
            modalScore: document.getElementById('modalScore'),
            playAgainBtn: document.getElementById('playAgainBtn')
        };

        this.initEventListeners();
        this.startNewGame();
    }

    initEventListeners() {
        // Submit button click
        this.elements.submitBtn.addEventListener('click', () => this.submitGuess());

        // Enter key press
        this.elements.answerInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.submitGuess();
            }
        });

        // Play again button
        this.elements.playAgainBtn.addEventListener('click', () => {
            this.closeModal();
            this.startNewGame();
        });
    }

    async startNewGame() {
        try {
            this.showMessage('Loading new question...', '');

            const response = await fetch('/api/game/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.success) {
                this.gameState = data.data;
                this.renderGame();
                this.elements.answerInput.value = '';
                this.elements.answerInput.focus();
                this.showMessage('', '');
            } else {
                this.showMessage('Error loading game: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Error starting game:', error);
            this.showMessage('Failed to start game. Please refresh the page.', 'error');
        }
    }

    renderGame() {
        // Render question
        this.elements.questionText.textContent = this.gameState.question;

        // Render answers
        this.elements.answersGrid.innerHTML = '';
        this.gameState.answers.forEach((answer, index) => {
            const card = this.createAnswerCard(answer, index);
            this.elements.answersGrid.appendChild(card);
        });

        // Update score and strikes
        this.updateScore(this.gameState.score);
        this.updateStrikes(this.gameState.strikes);
    }

    createAnswerCard(answer, index) {
        const card = document.createElement('div');
        card.className = `answer-card ${answer.revealed ? 'revealed' : 'hidden'}`;
        card.id = `answer-${index}`;

        const content = document.createElement('div');
        content.className = 'answer-content';
        content.style.display = 'flex';
        content.style.width = '100%';
        content.style.alignItems = 'center';
        content.style.justifyContent = 'space-between';

        if (answer.revealed) {
            const number = document.createElement('div');
            number.className = 'answer-number';
            number.textContent = index + 1;

            const text = document.createElement('div');
            text.className = 'answer-text';
            text.textContent = answer.text;

            const points = document.createElement('div');
            points.className = 'answer-points';
            points.textContent = answer.points;

            content.appendChild(number);
            content.appendChild(text);
            content.appendChild(points);
        } else {
            const number = document.createElement('div');
            number.className = 'answer-number';
            number.textContent = index + 1;

            content.appendChild(number);
        }

        card.appendChild(content);
        return card;
    }

    async submitGuess() {
        const guess = this.elements.answerInput.value.trim();

        if (!guess) {
            this.showMessage('Please enter an answer!', 'error');
            return;
        }

        // Disable input during processing
        this.elements.submitBtn.disabled = true;
        this.elements.answerInput.disabled = true;

        try {
            const response = await fetch('/api/game/guess', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ guess })
            });

            const data = await response.json();

            if (data.success) {
                this.handleGuessResult(data.data);
            } else {
                this.showMessage('Error: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Error submitting guess:', error);
            this.showMessage('Failed to submit answer. Please try again.', 'error');
        } finally {
            // Re-enable input
            this.elements.submitBtn.disabled = false;
            this.elements.answerInput.disabled = false;
            this.elements.answerInput.focus();
        }
    }

    handleGuessResult(data) {
        const result = data.result;
        this.gameState = data.game_state;

        if (result.matched) {
            // Correct answer
            this.playSound('ding');
            this.showMessage(result.message, 'success');
            this.revealAnswer(result.answer.index);
            this.updateScore(this.gameState.score);

            // Clear input
            this.elements.answerInput.value = '';

            // Check if game is won
            if (result.game_over && result.state === 'won') {
                setTimeout(() => this.showGameOver(true), 1000);
            }
        } else {
            // Wrong answer
            if (result.message === 'You already guessed that!' ||
                result.message === 'That answer is already revealed!') {
                this.showMessage(result.message, 'error');
            } else {
                this.playSound('buzzer');
                this.playSound('strike');
                this.showMessage(result.message, 'error');
                this.updateStrikes(this.gameState.strikes);

                // Check if game is lost
                if (result.game_over && result.state === 'lost') {
                    // Reveal all answers before showing game over
                    this.revealAllAnswers(() => {
                        this.showGameOver(false);
                    });
                }
            }
        }
    }

    revealAnswer(index) {
        const card = document.getElementById(`answer-${index}`);
        if (card) {
            card.classList.remove('hidden');
            card.classList.add('revealed');

            // Update card content
            const answer = this.gameState.answers[index];
            card.innerHTML = '';

            const content = document.createElement('div');
            content.className = 'answer-content';
            content.style.display = 'flex';
            content.style.width = '100%';
            content.style.alignItems = 'center';
            content.style.justifyContent = 'space-between';

            const number = document.createElement('div');
            number.className = 'answer-number';
            number.textContent = index + 1;

            const text = document.createElement('div');
            text.className = 'answer-text';
            text.textContent = answer.text;

            const points = document.createElement('div');
            points.className = 'answer-points';
            points.textContent = answer.points;

            content.appendChild(number);
            content.appendChild(text);
            content.appendChild(points);
            card.appendChild(content);
        }
    }

    revealAllAnswers(callback) {
        // Find all unrevealed answers
        const unrevealedIndices = [];
        this.gameState.answers.forEach((answer, index) => {
            if (!answer.revealed) {
                unrevealedIndices.push(index);
            }
        });

        if (unrevealedIndices.length === 0) {
            // No unrevealed answers, just call callback
            if (callback) callback();
            return;
        }

        // Reveal each answer with a delay (staggered animation)
        let currentIndex = 0;
        const revealDelay = 600; // 600ms between each reveal

        const revealNext = () => {
            if (currentIndex < unrevealedIndices.length) {
                const answerIndex = unrevealedIndices[currentIndex];

                // Play ding sound for each reveal
                this.playSound('ding');

                // Reveal the answer
                this.revealAnswer(answerIndex);

                currentIndex++;
                setTimeout(revealNext, revealDelay);
            } else {
                // All answers revealed, wait a bit then show game over
                setTimeout(() => {
                    if (callback) callback();
                }, 800);
            }
        };

        // Start revealing after a short delay
        setTimeout(revealNext, 500);
    }

    updateScore(score) {
        this.elements.score.textContent = score;
    }

    updateStrikes(strikes) {
        for (let i = 1; i <= 3; i++) {
            const strikeElement = document.getElementById(`strike${i}`);
            if (i <= strikes) {
                strikeElement.classList.add('active');
            } else {
                strikeElement.classList.remove('active');
            }
        }
    }

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

    showGameOver(won) {
        if (won) {
            this.elements.modalTitle.textContent = 'CONGRATULATIONS!';
            this.elements.modalMessage.textContent = 'You guessed all the answers!';
        } else {
            this.elements.modalTitle.textContent = 'GAME OVER!';
            this.elements.modalMessage.textContent = 'Three strikes - you\'re out!';
        }

        this.elements.modalScore.textContent = this.gameState.score;
        this.elements.modal.classList.add('active');

        // Disable input
        this.elements.submitBtn.disabled = true;
        this.elements.answerInput.disabled = true;
    }

    closeModal() {
        this.elements.modal.classList.remove('active');

        // Re-enable input
        this.elements.submitBtn.disabled = false;
        this.elements.answerInput.disabled = false;
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

// Initialize game when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.game = new FamilyFeudGame();
});
