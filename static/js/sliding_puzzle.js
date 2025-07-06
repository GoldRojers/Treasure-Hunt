document.addEventListener('DOMContentLoaded', () => {
    const board = document.getElementById('puzzle-board');
    const message = document.getElementById('message');
    const countdownEl = document.getElementById('countdown');

    let tiles = [];
    let timeLeft = 300; // 5 minutes
    let countdownStarted = false;
    let countdownInterval;

    function createTiles() {
        const numbers = [...Array(15).keys()].map(n => n + 1);
        numbers.push(null);
        shuffle(numbers);

        board.innerHTML = '';
        tiles = [];

        numbers.forEach((num, i) => {
            const tile = document.createElement('div');
            tile.classList.add('tile');
            if (num !== null) {
                tile.textContent = num;
                tile.classList.add('filled');
            } else {
                tile.classList.add('empty');
            }

            tile.addEventListener('click', () => moveTile(i));
            tiles.push(tile);
            board.appendChild(tile);
        });
    }

    function shuffle(arr) {
        for (let i = arr.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [arr[i], arr[j]] = [arr[j], arr[i]];
        }
    }

    function moveTile(index) {
        startTimer();  // 👈 Start timer on first move
        const emptyIndex = tiles.findIndex(t => t.classList.contains('empty'));
        const validMoves = getAdjacentIndices(emptyIndex);

        if (validMoves.includes(index)) {
            const temp = tiles[emptyIndex].textContent;
            tiles[emptyIndex].textContent = tiles[index].textContent;
            tiles[index].textContent = temp;

            tiles[emptyIndex].classList.toggle('empty');
            tiles[emptyIndex].classList.toggle('filled');
            tiles[index].classList.toggle('empty');
            tiles[index].classList.toggle('filled');

            checkWin();
        }
    }

    function getAdjacentIndices(i) {
        const adjacent = [];
        if (i % 4 !== 0) adjacent.push(i - 1);
        if (i % 4 !== 3) adjacent.push(i + 1);
        if (i - 4 >= 0) adjacent.push(i - 4);
        if (i + 4 < 16) adjacent.push(i + 4);
        return adjacent;
    }

    function checkWin() {
        const current = tiles.map(tile => tile.textContent || '');
        const target = [...Array(15).keys()].map(n => (n + 1).toString()).concat('');
        if (JSON.stringify(current) === JSON.stringify(target)) {
            message.textContent = "🎉 You solved it!";
            message.style.color = 'green';
            clearInterval(countdownInterval); // ✅ Stop timer
        } else {
            message.textContent = '';
        }
    }

    function updateTimerDisplay(seconds) {
        const mins = String(Math.floor(seconds / 60)).padStart(2, '0');
        const secs = String(seconds % 60).padStart(2, '0');
        countdownEl.textContent = `⏱️ Time Left: ${mins}:${secs}`;
    }

    function startTimer() {
        if (countdownStarted) return;
        countdownStarted = true;

        countdownInterval = setInterval(() => {
            timeLeft--;
            updateTimerDisplay(timeLeft);

            if (timeLeft <= 30) {
                countdownEl.classList.add('low-time');
            } else {
                countdownEl.classList.remove('low-time');
            }

            if (timeLeft <= 0) {
                clearInterval(countdownInterval);
                countdownEl.textContent = "⏱️ Time's up!";
                countdownEl.style.color = "red";
                countdownEl.classList.remove('low-time');

                setTimeout(() => {
                    location.reload();
                }, 1500);
            }
        }, 1000);
    }

    window.resetPuzzle = createTiles;
    createTiles();
    updateTimerDisplay(timeLeft);
});
