from flask import Blueprint, render_template, redirect, url_for

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
def dashboard():
    return render_template('admin/dashboard.html')

@admin_bp.route('/puzzles')
def puzzles():
    return render_template('admin/puzzles.html')

@admin_bp.route('/special-games')
def special_games():
    return render_template('templates/admin/special_games.html')

@admin_bp.route('/teams')
def teams():
    return render_template('admin/teams.html')

@admin_bp.route('/leaderboard')
def leaderboard():
    return render_template('admin/leaderboard.html')

@admin_bp.route('/controls')
def controls():
    return render_template('admin/controls.html')
