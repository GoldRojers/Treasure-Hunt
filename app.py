from flask import Flask, request, render_template, redirect, url_for, session
import random
import hashlib
import base64
import time
import re
import os
from dotenv import load_dotenv
load_dotenv()
from pymongo import MongoClient
from collections import Counter

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "defaultsecret")

# ✅ Now safe to access environment variables
MONGO_URI = os.getenv("MONGO_URI")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

client = MongoClient(MONGO_URI)
db = client["iicc_treasurehunt"]  # Database name
users_collection = db["users"]    # Example collection
teams_collection = db["teams"]
progress_collection = db["progress"]
puzzles_collection = db["puzzles"]
puzzle_bank = {
    doc["level"]: doc for doc in puzzles_collection.find()
}


# ----- PUZZLE GENERATORS -----


def generate_caesar(text, shift=3):
    return "".join(
        chr((ord(c) - base + shift) % 26 + base) if c.isalpha() else c
        for c in text
        for base in [ord("A") if c.isupper() else ord("a")]
        if c.isalpha()
    )


def generate_md5(text):
    return hashlib.md5(text.encode()).hexdigest()


def generate_binary(text):
    return " ".join(format(ord(c), "08b") for c in text)


def generate_base64(text):
    return base64.b64encode(text.encode()).decode()


def generate_rot13(text):
    return text.translate(
        str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm",
        )
    )


def generate_sudoku():
    base = 3
    side = base * base

    def pattern(r, c):
        return (base * (r % base) + r // base + c) % side

    def shuffle(s):
        return random.sample(s, len(s))

    r_base = range(base)
    rows = [g * base + r for g in shuffle(r_base) for r in shuffle(r_base)]
    cols = [g * base + c for g in shuffle(r_base) for c in shuffle(r_base)]
    nums = shuffle(range(1, side + 1))
    board = [[nums[pattern(r, c)] for c in cols] for r in rows]
    for p in random.sample(range(side * side), side * side * 3 // 4):
        board[p // side][p % side] = 0
    return board


# ----- ROUTES -----
@app.route("/")
def home():
    teams = [team.get("name") for team in teams_collection.find({}, {"name": 1}) if team.get("name")]
    return render_template("index.html", teams=teams)


@app.route("/join", methods=["POST"])
def join():
    team = request.form.get("team")
    name = request.form.get("name")
    uid = request.form.get("uid")

    # Check if user already exists
    if users_collection.find_one({"uid": uid}):
        return render_template("index.html", error="ID already registered. Please login instead.")

    # Check if team exists
    team_data = teams_collection.find_one({"name": team})
    if not team_data:
        return render_template("index.html", error="Invalid team selected.")

    # Check if team is full
    if len(team_data.get("members", [])) >= 5:
        return render_template("index.html", error=f"{team} is full.")

    # Add player to team
    teams_collection.update_one(
        {"name": team},
        {"$push": {"members": name}}
    )

    # Register user
    users_collection.insert_one({"uid": uid, "name": name, "team": team})

    # Initialize progress if team doesn't have it
    if not progress_collection.find_one({"team": team}):
        progress_collection.insert_one({
            "team": team,
            "members": [name],
            "votes": {},
            "leader": None,
            "started": False,
            "start_time": None,
            "current_level": 1,
            "completed": False,
            "points": 0,
            "hint_count": 0
        })
    else:
        # Add to existing team progress
        progress_collection.update_one(
            {"team": team},
            {"$push": {"members": name}}
        )

    session["team"] = team
    session["name"] = name
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["POST"])
def login():
    uid = request.form.get("uid")

    user = users_collection.find_one({"uid": uid})
    if user:
        session["team"] = user["team"]
        session["name"] = user["name"]
        return redirect(url_for("dashboard"))

    return render_template("index.html", error="ID not found. Please join first.")


@app.route("/dashboard")
def dashboard():
    team = session.get("team")
    name = session.get("name")

    if not team or not name:
        return redirect(url_for("home"))

    # ✅ FIXED: use "team" field, not "name"
    team_data = progress_collection.find_one({"team": team})
    if not team_data:
        return redirect(url_for("home"))

    # ✅ Check if game has not started → show waiting room
    if not team_data.get("started"):
        return render_template(
            "waiting_room.html",
            team=team,
            name=name,
            members=team_data.get("members", []),
            votes=team_data.get("votes", {}),
            leader=team_data.get("leader")
        )

    # Proceed to puzzle/dashboard
    level = team_data.get("current_level", 1)
    puzzle = puzzle_bank.get(level, {})
    ptype = puzzle.get("type", "text")

    if ptype == "password_rules":
        return render_template(
            "games/password_game/progressive.html",
            team=team,
            name=name,
            level=level,
            instructions=puzzle.get("instructions", ""),
            error=None,
        )

    return render_template(
        "dashboard.html",
        team=team,
        name=name,
        level=level,
        clue=puzzle.get("question", "Await puzzle"),
        ptype=ptype,
        progress={team: team_data}
    )

@app.route("/vote_leader", methods=["POST"])
def vote_leader():
    team = session.get("team")
    name = session.get("name")
    vote_for = request.form.get("vote_for")

    # Fetch team progress document
    team_data = progress_collection.find_one({"team": team})

    if team_data and name and vote_for in team_data.get("members", []):
        # Update the vote
        votes = team_data.get("votes", {})
        votes[name] = vote_for

        # Count the leader
        leader = Counter(votes.values()).most_common(1)[0][0]

        # Update both votes and leader in DB
        progress_collection.update_one(
            {"team": team},
            {"$set": {"votes": votes, "leader": leader}}
        )

    return redirect(url_for("dashboard"))



@app.route("/start_game", methods=["POST"])
def start_game():
    team = session.get("team")
    name = session.get("name")

    team_data = progress_collection.find_one({"team": team})  # <-- FIXED

    if team_data and team_data.get("leader") == name:
        if not team_data.get("started", False):
            progress_collection.update_one(
                {"team": team},
                {
                    "$set": {
                        "started": True,
                        "start_time": time.time()
                    }
                }
            )

    return redirect(url_for("dashboard"))




@app.route("/submit_clue", methods=["POST"])
def submit_clue():
    team = session.get("team")
    name = session.get("name")

    if not team:
        return redirect(url_for("home"))

    team_data = progress_collection.find_one({"name": team})
    if not team_data or not team_data.get("started"):
        return redirect(url_for("dashboard"))

    answer = request.form.get("answer")
    level = team_data.get("current_level", 1)
    puzzle = puzzle_bank.get(level, {})
    expected = puzzle.get("answer", "").strip().lower()

    if answer.strip().lower() == expected:
        next_level = level + 1
        new_points = team_data.get("points", 0) + 10

        # Check for final level
        if next_level > max(puzzle_bank.keys()):
            end_time = time.time()
            duration = end_time - team_data.get("start_time", end_time)
            minutes = duration / 60
            base = round(minutes, 2)

            # Time-based bonus
            if minutes <= 120:
                bonus = 20
            elif minutes <= 150:
                bonus = 10
            else:
                bonus = 0

            hint_count = team_data.get("hint_count", 0)
            penalty = hint_count * 5

            # Check if this is the first team to complete
            other_completed = progress_collection.count_documents({
                "team": {"$ne": team},
                "completed": True
            })

            if other_completed == 0:
                bonus += 10

            total_time = base + bonus - penalty
            final_points = new_points + bonus - penalty

            # Update DB
            progress_collection.update_one(
                {"name": team},
                {"$set": {
                    "current_level": next_level,
                    "completed": True,
                    "base": base,
                    "time_bonus": bonus,
                    "hint_penalty": penalty,
                    "total_time": total_time,
                    "points": final_points
                }}
            )

            leaderboard.append((team, duration, final_points))
            leaderboard.sort(key=lambda x: (-x[2], x[1]))
        else:
            # Just update level and points
            progress_collection.update_one(
                {"name": team},
                {"$set": {
                    "current_level": next_level,
                    "points": new_points
                }}
            )

        return redirect(url_for("dashboard"))

    else:
        # Wrong answer → -5 points
        new_points = team_data.get("points", 0) - 5
        progress_collection.update_one(
            {"name": team},
            {"$set": {"points": new_points}}
        )

        return render_template(
            "dashboard.html",
            team=team,
            name=name,
            level=level,
            error="Wrong answer.",
            clue=puzzle.get("question", ""),
            ptype=puzzle.get("type", "text"),
            progress={team: team_data}
        )

@app.route("/take_hint", methods=["POST"])
def take_hint():
    team = session.get("team")

    if not team:
        return redirect(url_for("dashboard"))

    team_data = progress_collection.find_one({"name": team})
    if not team_data:
        return redirect(url_for("dashboard"))

    hint_count = team_data.get("hint_count", 0)
    points = team_data.get("points", 0)

    deduction = 5 + (hint_count * 5)  # Hint 1: -5, Hint 2: -10, etc.
    new_points = points - deduction
    new_hint_count = hint_count + 1

    # Update in MongoDB
    progress_collection.update_one(
        {"name": team},
        {"$set": {
            "points": new_points,
            "hint_count": new_hint_count
        }}
    )

    return redirect(url_for("dashboard"))

@app.route("/leaderboard")
def show_leaderboard():
    scores = []

    completed_teams = progress_collection.find({"completed": True})

    for team_data in completed_teams:
        team = team_data.get("team")
        duration = (team_data.get("total_time", 0)) * 60  # convert back to seconds if needed
        points = team_data.get("points", 0)
        members = team_data.get("members", [])
        hint_used = team_data.get("hint_count", 0)
        base = team_data.get("base", 0)
        bonus = team_data.get("time_bonus", 0)
        penalty = team_data.get("hint_penalty", hint_used * 5)
        total = base + bonus - penalty

        scores.append({
            "team": team,
            "duration": round(duration, 2),
            "points": points,
            "members": members,
            "hints": hint_used,
            "base": base,
            "time_bonus": bonus,
            "hint_penalty": penalty,
            "total": total,
        })

    # Sort by points descending, then duration ascending
    scores.sort(key=lambda x: (-x["points"], x["duration"]))

    return render_template("leaderboard.html", scores=scores)

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        return render_template("admin_login.html", error="Invalid credentials")
    return render_template("admin_login.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    return render_template("admin/dashboard.html")


@app.route("/admin/panel", methods=["GET", "POST"])
def admin_panel():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        try:
            level = int(request.form.get("level"))
            text = request.form.get("text", "")
            answer = request.form.get("answer", "")
            ptype = request.form.get("type", "manual")
            instructions = request.form.get("instructions", "")

            # Generate clue based on puzzle type
            clue = (
                text
                if ptype == "password_rules"
                else {
                    "caesar": generate_caesar,
                    "md5": generate_md5,
                    "binary": generate_binary,
                    "base64": generate_base64,
                    "rot13": generate_rot13,
                }.get(ptype, lambda x: x)(text)
            )
            expected = "" if ptype == "password_rules" else answer.strip().lower()

            # Upsert puzzle to MongoDB
            puzzles_collection.update_one(
                {"level": level},
                {
                    "$set": {
                        "question": clue,
                        "answer": expected,
                        "type": ptype,
                        "instructions": instructions,
                        "text": text
                    }
                },
                upsert=True
            )

            session["success_message"] = f"Puzzle for Level {level} saved."
            return redirect(url_for("admin_panel"))

        except Exception as e:
            return render_template("admin_panel.html", error=f"Invalid input: {e}")

    return render_template(
        "admin_panel.html", success=session.pop("success_message", None)
    )

@app.route("/admin/control", methods=["GET", "POST"])
def admin_controls():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    msg = None

    if request.method == "POST":
        action = request.form.get("action")

        if action == "reset":
            # Delete all users, teams, and progress
            users_collection.delete_many({})
            teams_collection.delete_many({})
            progress_collection.delete_many({})
            msg = "✅ Game has been reset successfully."

        elif action == "broadcast":
            message = request.form.get("message")
            # Here, you could store this message in a collection or broadcast logic
            # For now, we just display the confirmation
            msg = f"📢 Message sent to all teams: {message}"

    return render_template("admin/controls.html", msg=msg)

@app.route("/admin/teams", methods=["GET", "POST"])
def manage_teams():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add":
            new_team = request.form.get("new_team")
            if new_team:
                existing = teams_collection.find_one({"name": new_team})
                if not existing:
                    teams_collection.insert_one({"name": new_team, "members": []})
        elif action == "remove":
            remove_team = request.form.get("remove_team")
            if remove_team:
                teams_collection.delete_one({"name": remove_team})
                progress_collection.delete_one({"team": remove_team})

    # ✅ Always execute this
    teams_cursor = teams_collection.find()
    teams = {team_doc["name"]: team_doc.get("members", []) for team_doc in teams_cursor}

    return render_template("admin/teams.html", teams=teams)

@app.route("/admin/games")
def manage_games():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    return render_template("admin/special_games.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/games/special")
def special_games():
    team = session.get("team")
    name = session.get("name")
    if not team or not name:
        return redirect(url_for("home"))
    return render_template("special_games.html", team=team, name=name)


@app.route("/games/sudoku")
def play_sudoku():
    return render_template("games/sudoku/sudoku.html")


@app.route("/games/wordle")
def play_wordle():
    return render_template("games/wordle/wordle.html")


@app.route("/games/game21")
def play_game21():
    return render_template("games/game21/game21.html")


@app.route("/score/update", methods=["POST"])
def update_game21_score():
    team = session.get("team")
    if not team:
        return {"error": "Not logged in"}, 403

    result = progress_collection.update_one(
        {"name": team},
        {"$inc": {"points": 30}}  # Adds 30 points for Game of 21
    )

    if result.modified_count == 1:
        updated = progress_collection.find_one({"name": team})
        return {
            "status": "ok",
            "new_score": updated.get("points", 0)
        }

    return {"error": "Score update failed"}, 500



@app.route("/games/sliding")
def play_sliding_puzzle():
    return render_template("games/sliding_puzzle/sliding_puzzle.html")


@app.route("/games/password")
def play_password_game():
    team = session.get("team")
    name = session.get("name")
    if not team or not name:
        return redirect(url_for("home"))

    return render_template("games/password_game/progressive.html", team=team, name=name)


@app.before_request
def debug_session():
    # ONLY ENABLE FOR DEVELOPMENT
    if app.debug and "team" not in session:
        session["team"] = "Team A"
        session["name"] = "TestUser"
        print("Session:", session)

@app.route("/admin/players", methods=["GET", "POST"])
def manage_players():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    # Reset team timer if requested
    if request.method == "POST":
        reset_team = request.form.get("reset_timer_team")
        if reset_team:
            progress_collection.update_one(
                {"team": reset_team},
                {"$set": {"start_time": time.time()}}
            )
            session["msg"] = f"Timer reset for {reset_team}."

    # Group users by team
    users = users_collection.find()
    team_groups = {}
    for user in users:
        team = user.get("team")
        name = user.get("name")
        uid = user.get("uid")
        team_groups.setdefault(team, []).append({"name": name, "uid": uid})

    # Load progress with time spent
    progress_data = {}
    for doc in progress_collection.find():
        start_time = doc.get("start_time")
        if start_time:
            time_spent = round((time.time() - start_time) / 60, 2)
        else:
            time_spent = None
        progress_data[doc["team"]] = {
            **doc,
            "time_spent": time_spent
        }

    return render_template(
        "admin/players.html",
        team_groups=team_groups,
        progress=progress_data,
        msg=session.pop("msg", None)
    )


@app.route("/admin/players/remove", methods=["POST"])
def remove_player():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    uid = request.form.get("uid")
    user = users_collection.find_one({"uid": uid})

    if user:
        name = user["name"]
        team = user["team"]

        # Remove from MongoDB users collection
        users_collection.delete_one({"uid": uid})

        # Remove from teams collection
        teams_collection.update_one(
            {"name": team},
            {"$pull": {"members": name}}
        )

        # Remove from progress document
        progress_collection.update_one(
            {"name": team},
            {"$pull": {"members": name}}
        )

        # Also update in-memory if needed
        registered_users.pop(uid, None)
        if team in teams and name in teams[team]:
            teams[team].remove(name)
        if team in progress and name in progress[team].get("members", []):
            progress[team]["members"].remove(name)

    return redirect(url_for("manage_players"))



@app.route("/admin/players/edit", methods=["POST"])
def edit_player_form():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    uid = request.form.get("uid")
    user = users_collection.find_one({"uid": uid})
    if not user:
        return redirect(url_for("manage_players"))  # Or show an error page/message

    name = user.get("name", "")
    team = user.get("team", "")
    return render_template("admin/edit_player.html", uid=uid, name=name, team=team)


@app.route("/admin/players/update", methods=["POST"])
def update_player():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    uid = request.form.get("uid")
    new_name = request.form.get("new_name")

    user = users_collection.find_one({"uid": uid})
    if user:
        old_name = user["name"]
        team = user["team"]

        # Update user's name in users collection
        users_collection.update_one({"uid": uid}, {"$set": {"name": new_name}})

        # Update name in teams collection
        teams_collection.update_one(
            {"team": team, "members": old_name},
            {"$set": {"members.$": new_name}}
        )

        # Update name in progress collection
        progress_collection.update_one(
            {"team": team, "members": old_name},
            {"$set": {"members.$": new_name}}
        )

        # Also update in-memory (optional, for current session consistency)
        registered_users[uid] = (new_name, team)
        if team in teams:
            teams[team] = [new_name if n == old_name else n for n in teams[team]]
        if team in progress:
            progress[team]["members"] = [
                new_name if n == old_name else n for n in progress[team]["members"]
            ]

    return redirect(url_for("manage_players"))



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render will set PORT
    app.run(host='0.0.0.0', port=port, debug=True)



