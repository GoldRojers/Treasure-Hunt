document.addEventListener('DOMContentLoaded', () => {
  let currentTotal = 0;
  let isPlayerTurn = true;
  const status = document.getElementById('status');
  const totalDisplay = document.getElementById('total');
  const dialButtons = document.querySelectorAll('.add-btn');

function updateDialLabels() {
  dialButtons.forEach(segment => {
    const value = parseInt(segment.dataset.value);
    segment.textContent = currentTotal + value <= 21 ? (currentTotal + value) : '❌';
    segment.disabled = currentTotal + value > 21;
  });
}

function updateUI() {
  totalDisplay.textContent = currentTotal;
  gsap.fromTo('#total', { scale: 1.3 }, { scale: 1, duration: 0.3 });
  updateDialLabels();
}


function checkGameOver() {
  if (currentTotal >= 21) {
    const playerWon = isPlayerTurn;
    status.textContent = playerWon ? 'You won! 🎉' : 'You lost! 😢';
    status.className = playerWon ? 'win' : 'lose';
    dialButtons.forEach(btn => btn.style.pointerEvents = 'none');
    
    if (playerWon) {
      confetti();
      // 🔄 Update score on server
      fetch('/score/update', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
          console.log('Score updated!', data);
        })
        .catch(err => console.error('Score update failed:', err));
    }
  }
}


  function logMove(who, value, totalAfterMove) {
  const start = totalAfterMove - value + 1;
  const numbers = Array.from({ length: value }, (_, i) => start + i).join(', ');

  const li = document.createElement('li');
  li.textContent = who === 'You'
    ? `🟢 You picked ${numbers}`
    : `🔴 Computer picked ${numbers}`;
    
  li.className = who === 'You' ? 'player-move' : 'computer-move';
  document.getElementById('moveList').appendChild(li);
}

function computerMove() {
  const safeNumbers = [ 12, 16, 20];
  let choice = 1;

  // Find the next safe number greater than currentTotal
  for (let target of safeNumbers) {
    if (target > currentTotal) {
      const diff = target - currentTotal;
      if (diff >= 1 && diff <= 3) {
        choice = diff;
        break;
      }
    }
  }

  // If no safe number is reachable, fallback to random
  if (currentTotal + choice > 21) {
    choice = Math.floor(Math.random() * Math.min(3, 21 - currentTotal)) + 1;
  }

  currentTotal += choice;
  logMove('Computer', choice, currentTotal);
  isPlayerTurn = true;
  updateUI();
  checkGameOver();
}


  dialButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      if (!isPlayerTurn) return;

      const value = parseInt(btn.dataset.value);
      currentTotal += value;
      logMove('You', value, currentTotal);
      isPlayerTurn = false;
      updateUI();
      checkGameOver();

      if (currentTotal < 21) {
        setTimeout(computerMove, 1000);
      }
    });
  });

  updateUI();
});
