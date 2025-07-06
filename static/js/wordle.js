document.addEventListener('DOMContentLoaded', () => {
    const secretWord = "CHAIR"; // You can randomize later
    const maxTries = 6;
    let currentTry = 0;

    const grid = document.getElementById("grid");
    const input = document.getElementById("guess-input");
    const submitBtn = document.getElementById("submit-btn");
    const message = document.getElementById("message");

    // Build 6 rows × 5 cells
    for (let i = 0; i < maxTries; i++) {
        const row = document.createElement("div");
        row.classList.add("row");
        for (let j = 0; j < 5; j++) {
            const cell = document.createElement("div");
            cell.classList.add("cell");
            row.appendChild(cell);
        }
        grid.appendChild(row);
    }

    submitBtn.addEventListener("click", () => {
        const guess = input.value.toUpperCase();
        if (guess.length !== 5) {
            message.textContent = "❌ Must be a 5-letter word";
            return;
        }

        const row = grid.children[currentTry];
        const used = secretWord.split("");
        const guessLetters = guess.split("");

        // First pass – mark correct positions (green)
        for (let i = 0; i < 5; i++) {
            const cell = row.children[i];
            cell.textContent = guess[i];
            cell.classList.add("filled");

            if (guess[i] === secretWord[i]) {
                cell.classList.add("correct");
                used[i] = null;
                guessLetters[i] = null;
            }
        }

        // Second pass – mark present (yellow) and absent (gray)
        for (let i = 0; i < 5; i++) {
            const cell = row.children[i];
            if (!guessLetters[i]) continue;

            const index = used.indexOf(guessLetters[i]);
            if (index !== -1) {
                cell.classList.add("present");
                used[index] = null;
            } else {
                cell.classList.add("absent");
            }
        }

        currentTry++;
        input.value = "";

        if (guess === secretWord) {
            message.textContent = "🎉 You guessed it!";
            input.disabled = true;
            submitBtn.disabled = true;
        } else if (currentTry === maxTries) {
            message.textContent = `💀 Out of tries. Word was ${secretWord}`;
            input.disabled = true;
            submitBtn.disabled = true;
        }
    });
});
