document.addEventListener('DOMContentLoaded', () => {
    const puzzle = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],

        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],

        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9]
    ];

    const board = document.getElementById('sudoku-board');
    const message = document.getElementById('message');

    // Render 9x9 grid
    for (let row = 0; row < 9; row++) {
        const rowDiv = document.createElement('div');
        rowDiv.classList.add('sudoku-row');
        for (let col = 0; col < 9; col++) {
            const cell = document.createElement('input');
            cell.type = 'text';
            cell.maxLength = 1;
            cell.classList.add('sudoku-cell');

            if (puzzle[row][col] !== 0) {
                cell.value = puzzle[row][col];
                cell.disabled = true;
                cell.classList.add('prefilled');
            }

            rowDiv.appendChild(cell);
        }
        board.appendChild(rowDiv);
    }

    // Get current values from grid
    function getGridValues() {
        const inputs = document.querySelectorAll('.sudoku-cell');
        return Array.from({ length: 9 }, (_, i) =>
            Array.from({ length: 9 }, (_, j) =>
                parseInt(inputs[i * 9 + j].value) || 0
            )
        );
    }

    // Validate Sudoku rules
    function isValid(grid) {
        for (let i = 0; i < 9; i++) {
            const row = new Set(), col = new Set(), box = new Set();
            for (let j = 0; j < 9; j++) {
                const r = grid[i][j];
                const c = grid[j][i];
                const b = grid[3 * Math.floor(i / 3) + Math.floor(j / 3)]
                          [3 * (i % 3) + (j % 3)];

                if (r && row.has(r)) return false;
                if (c && col.has(c)) return false;
                if (b && box.has(b)) return false;

                row.add(r);
                col.add(c);
                box.add(b);
            }
        }
        return true;
    }

    // Check button
    document.getElementById('check-btn').addEventListener('click', () => {
        const grid = getGridValues();

        // Remove any previous animation class
        board.classList.remove('success', 'shake');

        if (grid.flat().includes(0)) {
            message.textContent = "❗ Fill all cells first.";
            message.style.color = "orange";
        } else if (isValid(grid)) {
            message.textContent = "✅ Sudoku is correct!";
            message.style.color = "green";
            board.classList.add('success');
            setTimeout(() => board.classList.remove('success'), 700);
        } else {
            message.textContent = "❌ Invalid solution.";
            message.style.color = "red";
            board.classList.add('shake');
            setTimeout(() => board.classList.remove('shake'), 500);
        }
    });

    // Reset button
    document.getElementById('reset-btn').addEventListener('click', () => {
        const inputs = document.querySelectorAll('.sudoku-cell:not(.prefilled)');
        inputs.forEach(input => input.value = '');
        message.textContent = '';
    });
});
