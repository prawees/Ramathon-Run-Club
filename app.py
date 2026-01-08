from flask import Flask, render_template, request, redirect, url_for, session, abort
import requests
import json
import os
import time
import datetime
from datetime import timezone

app = Flask(__name__)
app.secret_key = 'RAMATHON_PURPLE_KEY'

# --- CONFIGURATION ---
CLIENT_ID = '194111'
CLIENT_SECRET = 'be307cce9818cd549fae09f324aa0a31c7da5add'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'database.json')

# --- RPG GAMIFICATION CONFIG ---
# Ranks determined by Total Yearly Distance
LEVELS = [
    {'id': 'D', 'name': 'Class D: Rookie', 'min': 0, 'max': 50, 'color': '#888888', 'icon': '🌱'},
    {'id': 'C', 'name': 'Class C: Runner', 'min': 50, 'max': 200, 'color': '#4CAF50', 'icon': '🏃'},
    {'id': 'B', 'name': 'Class B: Pacer', 'min': 200, 'max': 500, 'color': '#2196F3', 'icon': '⚡'},
    {'id': 'A', 'name': 'Class A: Elite', 'min': 500, 'max': 1000, 'color': '#9C27B0', 'icon': '🔥'},
    {'id': 'S', 'name': 'Class S: Legend', 'min': 1000, 'max': 99999, 'color': '#FFD700', 'icon': '👑'}
]

TRANSLATIONS = {
    'en': {
        'title': 'Ramathon Run Club',
        'nav_leaderboard': 'LEADERBOARD',
        'nav_events': 'EVENTS',
        'nav_rules': 'RULES',
        'nav_profile': 'MY PROFILE',
        'nav_connect': 'CONNECT STRAVA',
        'nav_logout': 'LOGOUT',
        'btn_sync': '⟳ Sync Strava',
        'btn_save': 'Save Profile',
        'lbl_team': 'Team',
        'lbl_year': 'Role',
        'lbl_status': 'Status',
        'lbl_motto': 'Motto',
        'lbl_shoe': 'Shoe',
        'stats_month': 'MONTHLY',
        'stats_quarter': 'QUARTERLY',
        'stats_total': 'ANNUAL RANK',
        'level_prefix': 'RANK',
        'badge_shirt_qual': 'SHIRT QUALIFIED',
        'badge_shirt_wait': 'ALREADY CLAIMED',
        'msg_shirt_win': 'You have qualified for the Quarterly Shirt! Contact staff.',
        'msg_shirt_next': 'Great job! You have already claimed a shirt this year.',
        'view_profile': 'View Profile',
        'empty_db': 'No runners active yet.'
    },
    'th': {
        'title': 'Ramathon Run Club',
        'nav_leaderboard': 'ตารางคะแนน',
        'nav_events': 'กิจกรรม',
        'nav_rules': 'กติกา',
        'nav_profile': 'ข้อมูลส่วนตัว',
        'nav_connect': 'เชื่อมต่อ STRAVA',
        'nav_logout': 'ออกจากระบบ',
        'btn_sync': '⟳ อัพเดทข้อมูล',
        'btn_save': 'บันทึกข้อมูล',
        'lbl_team': 'ทีม/สังกัด',
        'lbl_year': 'ชั้นปี/ตำแหน่ง',
        'lbl_status': 'สเตตัส',
        'lbl_motto': 'คติประจำใจ',
        'lbl_shoe': 'รองเท้า',
        'stats_month': 'รายเดือน',
        'stats_quarter': 'รายไตรมาส',
        'stats_total': 'ระดับประจำปี',
        'level_prefix': 'ระดับ',
        'badge_shirt_qual': 'รับเสื้อได้',
        'badge_shirt_wait': 'รับสิทธิ์แล้ว',
        'msg_shirt_win': 'ยินดีด้วย! คุณผ่านเกณฑ์รับเสื้อประจำไตรมาสนี้ ติดต่อรับได้ที่คณะ',
        'msg_shirt_next': 'ยอดเยี่ยม! (คุณได้รับสิทธิ์เสื้อของปีนี้ไปแล้ว)',
        'view_profile': 'ดูโปรไฟล์',
        'empty_db': 'ยังไม่มีข้อมูลนักวิ่ง'
    }
}

# --- HELPERS ---
def load_db():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except: return {}

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

def get_level(km):
    """Returns the level dict based on total KM."""
    for lvl in LEVELS:
        if km < lvl['max']:
            return lvl
    return LEVELS[-1] # Return max level if exceeded

def get_valid_token(user_id):
    db = load_db()
    user = db.get(user_id)
    if not user: return None
    # Check expiration (buffer 5 mins)
    if time.time() < user['expires_at'] - 300:
        return user['access_token']
    
    # Refresh logic
    print(f"Refreshing token for {user.get('firstname')}...")
    token_url = 'https://www.strava.com/oauth/token'
    payload = {
        'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET,
        'grant_type': 'refresh_token', 'refresh_token': user['refresh_token']
    }
    try:
        r = requests.post(token_url, data=payload).json()
        if 'access_token' in r:
            user.update({
                'access_token': r['access_token'],
                'refresh_token': r['refresh_token'],
                'expires_at': r['expires_at']
            })
            db[user_id] = user
            save_db(db)
            return user['access_token']
    except Exception as e:
        print(f"Refresh Error: {e}")
    return None

def get_time_boundaries():
    """Calculates timestamps for start of Month, Quarter, and Year."""
    now = datetime.datetime.now()
    
    # Start of Year
    year_start = datetime.datetime(now.year, 1, 1).replace(tzinfo=timezone.utc).timestamp()
    
    # Start of Month
    month_start = datetime.datetime(now.year, now.month, 1).replace(tzinfo=timezone.utc).timestamp()
    
    # Start of Quarter
    q_month = (now.month - 1) // 3 * 3 + 1
    quarter_start = datetime.datetime(now.year, q_month, 1).replace(tzinfo=timezone.utc).timestamp()
    
    return int(month_start), int(quarter_start), int(year_start)

# --- ROUTES ---
@app.context_processor
def inject_globals():
    lang = session.get('lang', 'th')
    return dict(text=TRANSLATIONS[lang], current_lang=lang, get_level=get_level)

@app.route('/set_lang/<lang_code>')
def set_lang(lang_code):
    if lang_code in ['en', 'th']: session['lang'] = lang_code
    return redirect(request.referrer or url_for('home'))

@app.route('/')
def home():
    db = load_db()
    members = list(db.values())
    # Sort by MONTHLY distance by default for the active leaderboard
    members.sort(key=lambda x: x.get('dist_month', 0), reverse=True)
    return render_template('index.html', members=members)

@app.route('/profile')
def profile():
    """Editable profile for logged-in user"""
    user_id = session.get('user_id')
    if not user_id: return redirect(url_for('login'))
    db = load_db()
    user = db.get(user_id)
    if not user: return redirect(url_for('logout'))
    return render_template('profile.html', user=user, readonly=False)

@app.route('/profile/<user_id>')
def public_profile(user_id):
    """Read-only profile for visitors"""
    db = load_db()
    user = db.get(user_id)
    if not user: abort(404)
    
    # If viewing own profile, redirect to editable version
    if session.get('user_id') == user_id:
        return redirect(url_for('profile'))
        
    return render_template('profile.html', user=user, readonly=True)

@app.route('/update_stats')
def update_stats():
    user_id = session.get('user_id')
    if not user_id: return redirect(url_for('login'))
    token = get_valid_token(user_id)
    if not token: return redirect(url_for('login'))

    # Fetch activities from start of the year
    ts_month, ts_quarter, ts_year = get_time_boundaries()
    
    headers = {'Authorization': f"Bearer {token}"}
    # Fetch enough activities to cover the year (limit 200 for prototype)
    params = {'after': ts_year, 'per_page': 200, 'page': 1}
    
    try:
        r = requests.get("https://www.strava.com/api/v3/athlete/activities", headers=headers, params=params)
        activities = r.json()
        
        if isinstance(activities, list):
            d_month, d_quarter, d_year = 0, 0, 0
            
            for act in activities:
                # Filter: Run only + Public only
                if act.get('type') == 'Run' and act.get('visibility') == 'everyone':
                    # Strava returns dates in ISO format e.g. "2024-01-01T10:00:00Z"
                    # We can use the logic that we asked API for data 'after' Jan 1st
                    # So everything here is part of d_year.
                    # We just need to check month/quarter timestamps.
                    
                    # Convert start_date to timestamp
                    act_dt = datetime.datetime.strptime(act['start_date'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    act_ts = int(act_dt.timestamp())
                    dist_km = act.get('distance', 0) / 1000

                    d_year += dist_km
                    if act_ts >= ts_quarter:
                        d_quarter += dist_km
                    if act_ts >= ts_month:
                        d_month += dist_km
            
            db = load_db()
            if user_id in db:
                db[user_id]['dist_month'] = round(d_month, 2)
                db[user_id]['dist_quarter'] = round(d_quarter, 2)
                db[user_id]['dist_year'] = round(d_year, 2)
                
                # Compatibility: Ensure older users have new fields
                if 'has_received_shirt' not in db[user_id]: 
                    db[user_id]['has_received_shirt'] = False
                    
                save_db(db)
    except Exception as e:
        print(f"Sync Error: {e}")

    return redirect(url_for('profile'))

@app.route('/update_profile', methods=['POST'])
def update_profile():
    user_id = session.get('user_id')
    if not user_id: return redirect(url_for('login'))
    db = load_db()
    if user_id in db:
        db[user_id].update({
            'team': request.form.get('team'),
            'year': request.form.get('year'),
            'status': request.form.get('status'),
            'motto': request.form.get('motto'),
            'shoe': request.form.get('shoe')
        })
        save_db(db)
    return redirect(url_for('profile'))

@app.route('/login')
def login():
    redirect_uri = url_for('callback', _external=True)
    scope = "activity:read_all"
    return redirect(f"https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={redirect_uri}&approval_prompt=auto&scope={scope}")

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code: return redirect(url_for('home'))
    
    redirect_uri = url_for('callback', _external=True)
    data = requests.post('https://www.strava.com/oauth/token', data={
        'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET, 
        'code': code, 'grant_type': 'authorization_code'
    }).json()
    
    if 'access_token' in data:
        uid = str(data['athlete']['id'])
        db = load_db()
        
        # Initialize default values for new users
        if uid not in db:
            db[uid] = {
                'dist_month': 0, 'dist_quarter': 0, 'dist_year': 0, 
                'has_received_shirt': False,
                'team': '', 'year': '', 'status': '', 'motto': '', 'shoe': ''
            }
        
        db[uid].update({
            'strava_id': uid,
            'firstname': data['athlete']['firstname'],
            'lastname': data['athlete']['lastname'],
            'profile': data['athlete']['profile'],
            'access_token': data['access_token'],
            'refresh_token': data['refresh_token'],
            'expires_at': data['expires_at']
        })
        save_db(db)
        session['user_id'] = uid
        return redirect(url_for('update_stats')) # Auto-sync on login
        
    return "Login Failed"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/rules')
def rules(): return render_template('rules.html')

@app.route('/events')
def events(): return render_template('events.html')

@app.route('/events/meetups')
def meetups(): return render_template('meetups.html')

@app.route('/events/recap2024')
def recap2024(): return render_template('recap_2024.html')

if __name__ == '__main__':
    app.run(debug=True)