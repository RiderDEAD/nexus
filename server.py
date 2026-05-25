# -*- coding: utf-8 -*-
"""
Nexus Defense v2 - Python Backend
Flask REST API: wave configs, scores, difficulty
Cross-platform: Windows / macOS / Linux
"""

import json, os, webbrowser, threading, time, math, random
from flask import Flask, jsonify, render_template, request

app = Flask(__name__, template_folder='templates')

# ── DIFFICULTY MULTIPLIERS ───────────────────────────────────────────
DIFFICULTY_PARAMS = {
    'easy':   {'hp': 0.70, 'speed': 0.85, 'count': 0.80, 'reward': 1.30, 'start_gold': 350, 'nexus_hp': 30, 'label': 'EASY'},
    'normal': {'hp': 1.00, 'speed': 1.00, 'count': 1.00, 'reward': 1.00, 'start_gold': 200, 'nexus_hp': 20, 'label': 'NORMAL'},
    'hard':   {'hp': 1.50, 'speed': 1.20, 'count': 1.30, 'reward': 0.80, 'start_gold': 150, 'nexus_hp': 15, 'label': 'HARD'},
}

MAX_WAVES = 20

def generate_wave_config(wave: int, difficulty: str = 'normal') -> dict:
    dm = DIFFICULTY_PARAMS.get(difficulty, DIFFICULTY_PARAMS['normal'])
    w  = wave
    scale = 1 + (w - 1) * 0.12
    hp_scale  = scale * dm['hp']
    spd_scale = dm['speed']
    cnt_scale = dm['count']

    enemies = []
    t = 0  # delay accumulator ms

    # ── Wave compositions by wave number ───────────────────────────
    # Wave 1-3: only scouts
    scout_n = max(1, int((3 + w * 2) * cnt_scale))
    for i in range(scout_n):
        enemies.append({'type': 'Scout', 'hp': int(55 * hp_scale), 'speed': round(1.55 * spd_scale, 2),
                        'reward': int(8 * dm['reward']), 'delay': i * 38})
    t = scout_n * 38 + 200

    # Wave 2+: Soldiers
    if w >= 2:
        sol_n = max(1, int(((w - 1) * 2) * cnt_scale))
        for i in range(sol_n):
            enemies.append({'type': 'Soldier', 'hp': int(140 * hp_scale), 'speed': round(1.0 * spd_scale, 2),
                            'reward': int(18 * dm['reward']), 'delay': t + i * 55})
        t += sol_n * 55 + 250

    # Wave 3+: Shielders (slow, tanky front-liners)
    if w >= 3:
        sh_n = max(1, int(math.ceil((w - 2) * 0.8) * cnt_scale))
        for i in range(sh_n):
            enemies.append({'type': 'Shielder', 'hp': int(320 * hp_scale), 'speed': round(0.65 * spd_scale, 2),
                            'reward': int(30 * dm['reward']), 'delay': t + i * 70})
        t += sh_n * 70 + 300

    # Wave 4+: Tanks
    if w >= 4:
        tank_n = max(1, int((w - 3) * cnt_scale))
        for i in range(tank_n):
            enemies.append({'type': 'Tank', 'hp': int(450 * hp_scale), 'speed': round(0.55 * spd_scale, 2),
                            'reward': int(45 * dm['reward']), 'delay': t + i * 90})
        t += tank_n * 90 + 300

    # Wave 5+: Speedsters (fast glass cannons)
    if w >= 5:
        sp_n = max(2, int((2 + (w - 5)) * cnt_scale))
        for i in range(sp_n):
            enemies.append({'type': 'Speedster', 'hp': int(80 * hp_scale), 'speed': round(2.8 * spd_scale, 2),
                            'reward': int(22 * dm['reward']), 'delay': t + i * 28})
        t += sp_n * 28 + 250

    # Wave 7+: Ghosts (immune to splash)
    if w >= 7:
        gh_n = max(1, int((w - 6) * cnt_scale))
        for i in range(gh_n):
            enemies.append({'type': 'Ghost', 'hp': int(180 * hp_scale), 'speed': round(1.3 * spd_scale, 2),
                            'reward': int(35 * dm['reward']), 'delay': t + i * 50, 'immune_splash': True})
        t += gh_n * 50 + 300

    # Wave 9+: Regen enemies
    if w >= 9:
        rg_n = max(1, int(math.ceil((w - 8) * 0.7) * cnt_scale))
        for i in range(rg_n):
            enemies.append({'type': 'Regen', 'hp': int(260 * hp_scale), 'speed': round(0.9 * spd_scale, 2),
                            'reward': int(40 * dm['reward']), 'delay': t + i * 65, 'regen': 3})
        t += rg_n * 65 + 300

    # Wave 12+: Swarm (many weak enemies at once)
    if w >= 12:
        sw_n = max(4, int(8 * cnt_scale))
        for i in range(sw_n):
            enemies.append({'type': 'Swarm', 'hp': int(35 * hp_scale), 'speed': round(2.0 * spd_scale, 2),
                            'reward': int(6 * dm['reward']), 'delay': t + i * 18})
        t += sw_n * 18 + 200

    # Wave 15+: Titan (mega tank)
    if w >= 15:
        titan_n = max(1, int(math.ceil((w - 14) * 0.5) * cnt_scale))
        for i in range(titan_n):
            enemies.append({'type': 'Titan', 'hp': int(1800 * hp_scale), 'speed': round(0.35 * spd_scale, 2),
                            'reward': int(120 * dm['reward']), 'delay': t + i * 200})
        t += titan_n * 200 + 400

    # Boss waves: 5, 10, 15, 20
    if w % 5 == 0:
        enemies.append({'type': 'Boss', 'hp': int(1200 * hp_scale * (1 + w * 0.05)),
                        'speed': round(0.72 * spd_scale, 2),
                        'reward': int(180 * dm['reward']), 'delay': t + 300, 'is_boss': True})

    enemies.sort(key=lambda e: e['delay'])

    return {
        'wave': w,
        'difficulty': difficulty,
        'enemies': enemies,
        'reward_bonus': int((35 + w * 12) * dm['reward']),
        'is_boss_wave': w % 5 == 0,
    }


SCORES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scores.json')

def load_scores():
    try:
        with open(SCORES_FILE) as f:
            return json.load(f)
    except Exception:
        return []

def save_score(entry):
    scores = load_scores()
    scores.append(entry)
    scores.sort(key=lambda s: (s.get('wave', 0), s.get('kills', 0)), reverse=True)
    scores = scores[:20]
    try:
        with open(SCORES_FILE, 'w') as f:
            json.dump(scores, f, indent=2)
    except Exception:
        pass
    return scores


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/wave/<int:wave_number>')
def get_wave(wave_number):
    if wave_number < 1 or wave_number > MAX_WAVES:
        return jsonify({'error': 'Wave out of range'}), 400
    difficulty = request.args.get('difficulty', 'normal')
    if difficulty not in DIFFICULTY_PARAMS:
        difficulty = 'normal'
    return jsonify(generate_wave_config(wave_number, difficulty))

@app.route('/api/difficulty_configs')
def difficulty_configs():
    return jsonify({k: {'label': v['label'], 'start_gold': v['start_gold'], 'nexus_hp': v['nexus_hp']}
                    for k, v in DIFFICULTY_PARAMS.items()})

@app.route('/api/scores', methods=['GET'])
def get_scores():
    return jsonify(load_scores())

@app.route('/api/scores', methods=['POST'])
def post_score():
    data = request.json
    if not data:
        return jsonify({'error': 'No data'}), 400
    entry = {
        'name':       str(data.get('name', 'Commander'))[:20],
        'wave':       int(data.get('wave', 0)),
        'kills':      int(data.get('kills', 0)),
        'gold':       int(data.get('gold', 0)),
        'difficulty': str(data.get('difficulty', 'normal')),
        'time':       str(data.get('time', '')),
    }
    scores = save_score(entry)
    return jsonify(scores)

@app.route('/api/tower_configs')
def tower_configs():
    return jsonify({
        'Gunner':  {'cost': 60,  'damage': 20,  'range': 130, 'cooldown': 26, 'splash': 0,   'slow': 0,
                    'color': '#4fc3f7', 'icon': 'G', 'desc': 'Fast single-target. Great vs scouts.',
                    'upgrades': [{'damage': 30, 'range': 145, 'cooldown': 22}, {'damage': 46, 'range': 160, 'cooldown': 18}]},
        'Cannon':  {'cost': 120, 'damage': 65,  'range': 150, 'cooldown': 72, 'splash': 55,  'slow': 0,
                    'color': '#ff8a50', 'icon': 'C', 'desc': 'Splash damage. Shreds groups.',
                    'upgrades': [{'damage': 95, 'range': 165, 'cooldown': 60, 'splash': 68}, {'damage': 145, 'range': 180, 'cooldown': 50, 'splash': 82}]},
        'Laser':   {'cost': 100, 'damage': 10,  'range': 125, 'cooldown': 4,  'splash': 0,   'slow': 0.5,
                    'color': '#ce93d8', 'icon': 'L', 'desc': 'Slows enemies. Continuous beam.',
                    'upgrades': [{'damage': 16, 'range': 138, 'cooldown': 3, 'slow': 0.62}, {'damage': 25, 'range': 152, 'cooldown': 2, 'slow': 0.75}]},
        'Sniper':  {'cost': 150, 'damage': 130, 'range': 225, 'cooldown': 88, 'splash': 0,   'slow': 0,
                    'color': '#ffd54f', 'icon': 'S', 'desc': 'Extreme range. High single-target damage.',
                    'upgrades': [{'damage': 195, 'range': 255, 'cooldown': 72}, {'damage': 300, 'range': 295, 'cooldown': 58}]},
        'Tesla':   {'cost': 200, 'damage': 45,  'range': 140, 'cooldown': 35, 'splash': 70,  'slow': 0.3, 'chain': 3,
                    'color': '#80deea', 'icon': 'T', 'desc': 'Chains lightning. Slows & damages groups.',
                    'upgrades': [{'damage': 68, 'range': 155, 'cooldown': 28, 'chain': 4}, {'damage': 105, 'range': 170, 'cooldown': 22, 'chain': 5}]},
        'Missile': {'cost': 180, 'damage': 110, 'range': 200, 'cooldown': 110,'splash': 90,  'slow': 0,
                    'color': '#ef9a9a', 'icon': 'M', 'desc': 'Huge splash. Destroys groups & tanks.',
                    'upgrades': [{'damage': 165, 'range': 215, 'cooldown': 92, 'splash': 110}, {'damage': 250, 'range': 235, 'cooldown': 75, 'splash': 135}]},
    })


def open_browser():
    time.sleep(1.0)
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    print('=' * 52)
    print('  NEXUS DEFENSE v2 — Server starting...')
    print('  Open: http://localhost:5000')
    print('  Ctrl+C to stop')
    print('=' * 52)
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(debug=False, port=5000, host='0.0.0.0')
