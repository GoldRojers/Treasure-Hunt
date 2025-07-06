# 🗺️ IICC Treasure Hunt

**IICC Treasure Hunt** is a Flask-based puzzle adventure platform designed for hybrid campus events. It features multi-level puzzles, QR-based offline progression, and a dynamic scoring system — perfect for engaging first-year students in an immersive experience.

---

## 🔥 Features

- 🧩 **Puzzle Generator** (Caesar, Base64, MD5, Sudoku, Password Rules)
- 🧑‍💻 **Admin Panel**: Create puzzles, monitor progress, control leaderboard
- 👥 **Team Registration** with custom names
- 📍 **Offline Integration**: QR code scans unlock next location or puzzle
- ⏱️ **Time & Point-Based Scoring**
- 📈 **Leaderboard** for real-time ranking

---

## 🏁 Game Flow

1. Teams register with a name and path (optional)
2. Start with an online puzzle
3. Solving leads to a location clue/QR code
4. QR unlocks next level — continues alternately between online and offline
5. Admin tracks and controls team progress
6. Final score combines accuracy + time

---

## 🧠 Puzzle Types

- Caesar Cipher
- Base64 / MD5
- Sudoku-style Puzzles
- Password Rules Challenge
- (Extendable to more puzzle types)

---

## 🚀 Getting Started

### Prerequisites
- Python 3.x
- Flask
- (Optional) QR code tools, SQLite/MongoDB for persistence

### Installation

```bash
git clone https://github.com/yourusername/iicc-treasure-hunt.git
cd iicc-treasure-hunt
pip install -r requirements.txt
python app.py
