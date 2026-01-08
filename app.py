from flask import Flask, render_template, request, redirect, url_for, session, abort
import requests
import json
import os
import time
import datetime
from datetime import timezone
import calendar

app = Flask(__name__)
app.secret_key = 'RAMATHON_PURPLE_KEY'

# --- CONFIGURATION ---
CLIENT_ID = '194111'
CLIENT_SECRET = 'be307cce9818cd549fae09f324aa0a31c7da5add'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'database.json')

# --- CAMPAIGN STATUS ---
SHIRT_CAMPAIGN_ACTIVE = False 

# --- RPG GAMIFICATION CONFIG ---
LEVELS = [
    # CHANGED: Class D color to #C0C0C0 (Lighter Silver/Grey)
    {'id': 'D', 'name': 'Class D: Rookie', 'min': 0, 'max': 50, 'color': '#C0C0C0', 'icon': '🌱'},
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
        'view_profile': 'View Public Profile',
        'footer_line': 'Join OpenChat',
        # Countdown & Header
        'countdown_intro': "The fun starts now! Let's run Ramathibodians! Link your Strava now!",
        'countdown_sub': "Shirt challenges begin Q2 2026: 1 Apr 2026!",
        'countdown_label': 'SEASON STARTS IN:',
        # RPG Specific
        'stats_month': 'MONTHLY GRIND',
        'stats_quarter': 'QUARTERLY QUEST',
        'stats_total': 'ANNUAL CAREER',
        'level_prefix': 'RANK',
        'xp_to_next': 'KM to level up to',
        'xp_max': 'MAX LEVEL REACHED',
        'xp_desc': '(Yearly XP - Resets Jan 1st)',
        'locked_q2': 'UNLOCKS Q2 2026',
        'badge_section': 'MONTHLY BADGES',
        # IG Campaign
        'ig_promo': "✨ Special: Link IG by 25 Mar '26 to win a Starbucks Card! ☕",
        'ig_verified': 'IG Verified',
        # Profile Form
        'lbl_team': 'Team / Affiliation',
        'lbl_year': 'Year / Role',
        'lbl_campus': 'Campus',
        'lbl_status': 'Status Message',
        'lbl_motto': 'Running Motto',
        'lbl_shoe': 'Battle Shoe',
        'lbl_route': 'Fav. Running Route',
        'lbl_social': 'Social Connect',
        'lbl_ig': 'Instagram Handle (no @)',
        'lbl_show_strava': 'Show Strava Link on Profile',
        # Filter
        'filter_search': 'Search Name...',
        'filter_all_teams': 'All Teams',
        'filter_all_years': 'All Years',
        'filter_all_campus': 'All Campuses',
        # Options
        'opt_pyt': 'PYT (Phayathai)',
        'opt_cnmi': 'CNMI (Chakri)',
        'opt_salaya': 'Salaya',
        'empty_db': 'No adventurers found yet.'
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
        'view_profile': 'ดูโปรไฟล์',
        'footer_line': 'เข้ากลุ่ม OpenChat',
        # Countdown & Header
        'countdown_intro': "ความสนุกเริ่มแล้ว! ชาวรามาธิบดีเชื่อมต่อ Strava ได้เลย!",
        'countdown_sub': "ภารกิจชิงเสื้อเริ่ม Q2 2569: 1 เมษายน 2569",
        'countdown_label': 'เปิดซีซั่นในอีก:',
        # RPG Specific
        'stats_month': 'ภารกิจรายเดือน',
        'stats_quarter': 'ภารกิจพิชิตเสื้อ',
        'stats_total': 'ระดับนักวิ่ง (XP)',
        'level_prefix': 'ระดับ',
        'xp_to_next': 'กม. สู่ระดับ',
        'xp_max': 'ระดับสูงสุด',
        'xp_desc': '(สะสมรายปี - รีเซ็ต 1 ม.ค.)',
        'locked_q2': 'เปิดระบบ Q2 2569',
        'badge_section': 'เหรียญตราประจำเดือน',
        # IG Campaign
        'ig_promo': "✨ พิเศษ: ใส่ IG ภายใน 25 มี.ค. 69 ลุ้นรับ Starbucks Card! ☕",
        # CHANGED: 'ยืนยัน IG' -> 'IG Verified'
        'ig_verified': 'IG Verified',
        # Profile Form
        'lbl_team': 'สังกัด / ทีม',
        'lbl_year': 'ชั้นปี / ตำแหน่ง',
        'lbl_campus': 'วิทยาเขตหลัก',
        'lbl_status': 'สเตตัสวันนี้',
        'lbl_motto': 'คติประจำใจนักวิ่ง',
        'lbl_shoe': 'รองเท้าคู่ใจ',
        'lbl_route': 'เส้นทางวิ่งโปรด',
        'lbl_social': 'ช่องทางติดต่อ',
        'lbl_ig': 'Instagram ID (ไม่ต้องใส่ @)',
        'lbl_show_strava': 'แสดงปุ่ม Strava บนหน้าโปรไฟล์',
        # Filter
        'filter_search': 'ค้นหาชื่อ...',
        'filter_all_teams': 'ทุกทีม',
        'filter_all_years': 'ทุกชั้นปี',
        'filter_all_campus': 'ทุกวิทยาเขต',
        # Options
        'opt_pyt': 'พญาไท',
        'opt_cnmi': 'จักรีนฤบดินทร์',
        'opt_salaya': 'ศาลายา',
        'empty_db': 'ยังไม่มีสมาชิกในระบบ'
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
    for lvl in LEVELS:
        if km < lvl['max']: return lvl
    return LEVELS[-1]

def get_next_level(km):
    for lvl in LEVELS:
        if km < lvl['max']:
            idx = LEVELS.index(lvl)
            if idx + 1 < len(LEVELS):
                return LEVELS[idx + 1], round(lvl['max'] - km, 2)
    return None, 0

def get_valid_token(user_id):
    db = load_db()
    user = db.get(user_id)
    if not user: return None
    if time.time() < user['expires_at'] - 300: return user['access_token']
    
    token_url = 'https://www.strava.com/oauth/token'
    payload = {
        'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET,
        'grant_type': 'refresh_token', 'refresh_token': user['refresh_token']
    }
    try:
        r = requests.post(token_url, data=payload).json()
        if 'access_token' in r:
            user.update({'access_token': r['access_token'], 'refresh_token': r['refresh_token'], 'expires_at': r['expires_at']})
            db[user_id] = user
            save_db(db)
            return user['access_token']
    except: pass
    return None

def get_season_stats():
    now = datetime.datetime.now()
    year_start = datetime.datetime(now.year, 1, 1).replace(tzinfo=timezone.utc).timestamp()
    month_start = datetime.datetime(now.year, now.month, 1).replace(tzinfo=timezone.utc).timestamp()
    q_month = (now.month - 1) // 3 * 3 + 1
    quarter_start = datetime.datetime(now.year, q_month, 1).replace(tzinfo=timezone.utc).timestamp()
    return int(month_start), int(quarter_start), int(year_start)

# --- ROUTES ---
@app.context_processor
def inject_globals():
    lang = session.get('lang', 'th')
    return dict(
        text=TRANSLATIONS[lang], 
        current_lang=lang, 
        get_level=get_level,
        get_next_level=get_next_level,
        shirt_active=SHIRT_CAMPAIGN_ACTIVE,
        now_year=datetime.datetime.now().year
    )

@app.route('/set_lang/<lang_code>')
def set_lang(lang_code):
    if lang_code in ['en', 'th']: session['lang'] = lang_code
    return redirect(request.referrer or url_for('home'))

@app.route('/')
def home():
    db = load_db()
    members = list(db.values())
    members.sort(key=lambda x: x.get('dist_month', 0), reverse=True)
    return render_template('index.html', members=members)

@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    if not user_id: return redirect(url_for('login'))
    db = load_db()
    user = db.get(user_id)
    if not user: return redirect(url_for('logout'))
    return render_template('profile.html', user=user, readonly=False)

@app.route('/profile/<user_id>')
def public_profile(user_id):
    db = load_db()
    user = db.get(user_id)
    if not user: abort(404)
    if session.get('user_id') == user_id: return redirect(url_for('profile'))
    return render_template('profile.html', user=user, readonly=True)

@app.route('/update_stats')
def update_stats():
    user_id = session.get('user_id')
    if not user_id: return redirect(url_for('login'))
    token = get_valid_token(user_id)
    if not token: return redirect(url_for('login'))

    ts_month, ts_quarter, ts_year = get_season_stats()
    headers = {'Authorization': f"Bearer {token}"}
    params = {'after': ts_year, 'per_page': 200, 'page': 1}
    
    try:
        r = requests.get("https://www.strava.com/api/v3/athlete/activities", headers=headers, params=params)
        activities = r.json()
        if isinstance(activities, list):
            d_month, d_quarter, d_year = 0, 0, 0
            monthly_totals = {}
            
            for act in activities:
                if act.get('type') == 'Run' and act.get('visibility') == 'everyone':
                    act_dt = datetime.datetime.strptime(act['start_date'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    act_ts = int(act_dt.timestamp())
                    dist_km = act.get('distance', 0) / 1000
                    
                    d_year += dist_km
                    if act_ts >= ts_quarter: d_quarter += dist_km
                    if act_ts >= ts_month: d_month += dist_km
                    
                    month_key = act_dt.strftime("%Y-%m")
                    monthly_totals[month_key] = monthly_totals.get(month_key, 0) + dist_km
            
            earned_badges = [k for k, v in monthly_totals.items() if v >= 50]
            
            db = load_db()
            if user_id in db:
                db[user_id].update({
                    'dist_month': round(d_month, 2),
                    'dist_quarter': round(d_quarter, 2),
                    'dist_year': round(d_year, 2),
                    'badges': earned_badges
                })
                save_db(db)
    except Exception as e: print(f"Sync Error: {e}")
    return redirect(url_for('profile'))

@app.route('/update_profile', methods=['POST'])
def update_profile():
    user_id = session.get('user_id')
    if not user_id: return redirect(url_for('login'))
    db = load_db()
    if user_id in db:
        show_strava = 'on' if request.form.get('show_strava') else 'off'
        db[user_id].update({
            'team': request.form.get('team'),
            'year': request.form.get('year'),
            'campus': request.form.get('campus'),
            'status': request.form.get('status'),
            'motto': request.form.get('motto'),
            'shoe': request.form.get('shoe'),
            'fav_route': request.form.get('fav_route'),
            'instagram': request.form.get('instagram'),
            'show_strava': show_strava
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
        if uid not in db:
            db[uid] = {
                'dist_month': 0, 'dist_quarter': 0, 'dist_year': 0, 'badges': [],
                'team': '', 'year': '', 'campus': '', 'status': '', 
                'motto': '', 'shoe': '', 'fav_route': '', 'instagram': '', 'show_strava': 'off'
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
        return redirect(url_for('update_stats'))
    return "Login Failed"

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('home'))

@app.route('/rules')
def rules(): return render_template('rules.html')
@app.route('/events')
def events(): return render_template('events.html')
@app.route('/events/meetups')
def meetups(): return render_template('meetups.html')
@app.route('/events/recap2024')
def recap2024(): return render_template('recap_2024.html')

if __name__ == '__main__': app.run(debug=True)