from flask import Flask, render_template, request, redirect, url_for, session, abort, flash
import requests
import json
import os
import time
import datetime
from datetime import timezone, timedelta
import calendar
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# SECURITY
app.secret_key = os.getenv('FLASK_SECRET_KEY')
CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
# You can get a free token from https://aqicn.org/data-platform/token/
AQI_TOKEN = os.getenv('AQI_TOKEN', 'demo') 

# CONFIGURATION
app.permanent_session_lifetime = datetime.timedelta(days=365)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'database.json')

# --- CONSTANTS ---
SHIRT_CAMPAIGN_ACTIVE = False
CAMPAIGN_END_DATE = datetime.datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone(timedelta(hours=7)))
ADMIN_IDS = ['48771896'] 

# --- THEMES ---
MONTH_THEMES = {
    1: {'color': '#1E88E5', 'name': 'Cool Blue'},
    2: {'color': '#F48FB1', 'name': 'Pastel Love'},
    3: {'color': '#43A047', 'name': 'Fresh Green'},
    4: {'color': '#FB8C00', 'name': 'Solar Orange'},
    5: {'color': '#8E24AA', 'name': 'Royal Purple'},
    6: {'color': '#00ACC1', 'name': 'Ocean Cyan'},
    7: {'color': '#FFB300', 'name': 'Golden Hour'},
    8: {'color': '#1E88E5', 'name': 'Mother Blue'},
    9: {'color': '#F4511E', 'name': 'Autumn Rust'},
    10: {'color': '#546E7A', 'name': 'Shadow Grey'},
    11: {'color': '#6D4C41', 'name': 'Vintage Brown'},
    12: {'color': '#E53935', 'name': 'Holiday Red'}
}

LEVELS = [
    {'id': 'D', 'name': 'Class D: Rookie', 'min': 0, 'max': 50, 'color': '#C0C0C0', 'icon': '🌱'},
    {'id': 'C', 'name': 'Class C: Runner', 'min': 50, 'max': 200, 'color': '#4CAF50', 'icon': '🏃'},
    {'id': 'B', 'name': 'Class B: Pacer', 'min': 200, 'max': 500, 'color': '#2196F3', 'icon': '⚡'},
    {'id': 'A', 'name': 'Class A: Elite', 'min': 500, 'max': 1000, 'color': '#9C27B0', 'icon': '🔥'},
    {'id': 'S', 'name': 'Class S: Legend', 'min': 1000, 'max': 99999, 'color': '#FFD700', 'icon': '👑'}
]

TRANSLATIONS = {
    'en': { 'title': 'Ramathon Run Club', 'nav_leaderboard': 'LEADERBOARD', 'nav_events': 'EVENTS', 'nav_rules': 'RULES', 'nav_profile': 'MY PROFILE', 'nav_connect': 'CONNECT STRAVA', 'nav_logout': 'LOGOUT', 'btn_sync': '⟳ Sync Strava', 'btn_save': 'Save Profile', 'view_profile': 'View Public Profile', 'footer_line': 'Join OpenChat', 'countdown_intro': "The fun starts now! Let's run Ramathibodians! Link your Strava now!", 'countdown_sub': "Shirt Quest starts Q2 2026: Apr 1st! (But Yearly Rank XP accumulation starts TODAY!)", 'countdown_label': 'SEASON STARTS IN:', 'stats_month': 'MONTHLY GRIND', 'stats_quarter': 'QUARTERLY QUEST', 'stats_total': 'ANNUAL CAREER', 'level_prefix': 'RANK', 'xp_to_next': 'KM to level up to', 'xp_max': 'MAX LEVEL REACHED', 'xp_desc': '(Yearly XP - Resets Jan 1st)', 'locked_q2': 'UNLOCKS Q2 2026', 'badge_section': 'MONTHLY BADGES', 'badge_locked': 'Locked', 'badge_shirt_qual': 'SHIRT UNLOCKED', 'badge_shirt_wait': 'ALREADY CLAIMED', 'msg_shirt_win': 'You have qualified for the Quarterly Shirt! Contact staff to claim.', 'msg_shirt_next': 'Great job! You have already claimed a shirt this year.', 'ig_promo': "✨ Special: Link IG by 25 Mar '26 to win a Starbucks Card! ☕", 'ig_verified': 'IG Verified', 'lbl_team': 'Team / Affiliation', 'lbl_year': 'Year / Role', 'lbl_campus': 'Campus', 'lbl_status': 'Status Message', 'lbl_motto': 'Running Motto', 'lbl_shoe': 'Battle Shoe', 'lbl_route': 'Fav. Running Route', 'lbl_social': 'Social Connect', 'lbl_ig': 'Instagram Handle (no @)', 'lbl_show_strava': 'Show Strava Link on Profile', 'filter_search': 'Search Name...', 'filter_all_teams': 'All Teams', 'filter_all_years': 'All Years', 'filter_all_campus': 'All Campuses', 'opt_md': 'MD (Medicine)', 'opt_nr': 'NR (Nursing)', 'opt_er': 'ER (Paramedic)', 'opt_cd': 'CD (Comm. Disorders)', 'opt_staff': 'Staff / Faculty', 'opt_other': 'Other', 'opt_grad': 'Alumni / Grad', 'opt_pyt': 'PYT (Phayathai)', 'opt_cnmi': 'CNMI (Chakri)', 'opt_salaya': 'Salaya', 'empty_db': 'No adventurers found yet.' },
    'th': { 'title': 'Ramathon Run Club', 'nav_leaderboard': 'ตารางคะแนน', 'nav_events': 'กิจกรรม', 'nav_rules': 'กติกา', 'nav_profile': 'ข้อมูลส่วนตัว', 'nav_connect': 'เชื่อมต่อ STRAVA', 'nav_logout': 'ออกจากระบบ', 'btn_sync': '⟳ อัพเดทข้อมูล', 'btn_save': 'บันทึกข้อมูล', 'view_profile': 'ดูโปรไฟล์', 'footer_line': 'เข้ากลุ่ม OpenChat', 'countdown_intro': "ความสนุกเริ่มแล้ว! ชาวรามาธิบดีเชื่อมต่อ Strava แล้วออกวิ่งได้เลย!", 'countdown_sub': "ภารกิจชิงเสื้อเริ่ม Q2 2569: 1 เมษายน 2569 (แต่เริ่มสะสมระยะทางประจำปีเพื่อลุ้นรางวัลใหญ่ได้ตั้งแต่วันนี้)", 'countdown_label': 'เปิดซีซั่นในอีก:', 'stats_month': 'ภารกิจรายเดือน', 'stats_quarter': 'ภารกิจพิชิตเสื้อ', 'stats_total': 'ระดับนักวิ่ง (XP)', 'level_prefix': 'ระดับ', 'xp_to_next': 'กม. สู่ระดับ', 'xp_max': 'ระดับสูงสุด', 'xp_desc': '(สะสมรายปี - รีเซ็ต 1 ม.ค.)', 'locked_q2': 'เปิดระบบ Q2 2569', 'badge_section': 'เหรียญตราประจำเดือน', 'badge_locked': 'ยังไม่ปลดล็อค', 'badge_shirt_qual': 'รับเสื้อได้', 'badge_shirt_wait': 'รับสิทธิ์แล้ว', 'msg_shirt_win': 'ยินดีด้วย! คุณผ่านเกณฑ์รับเสื้อประจำไตรมาสนี้ ติดต่อรับได้ที่คณะ', 'msg_shirt_next': 'ยอดเยี่ยม! (คุณได้รับสิทธิ์เสื้อของปีนี้ไปแล้ว)', 'ig_promo': "✨ พิเศษ: ใส่ IG ภายใน 25 มี.ค. 69 ลุ้นรับ Starbucks Card! ☕", 'ig_verified': 'IG Verified', 'lbl_team': 'สังกัด / ทีม', 'lbl_year': 'ชั้นปี / ตำแหน่ง', 'lbl_campus': 'วิทยาเขตหลัก', 'lbl_status': 'สเตตัสวันนี้', 'lbl_motto': 'คติประจำใจนักวิ่ง', 'lbl_shoe': 'รองเท้าคู่ใจ', 'lbl_route': 'เส้นทางวิ่งโปรด', 'lbl_social': 'ช่องทางติดต่อ', 'lbl_ig': 'Instagram ID (ไม่ต้องใส่ @)', 'lbl_show_strava': 'แสดงปุ่ม Strava บนหน้าโปรไฟล์', 'filter_search': 'ค้นหาชื่อ...', 'filter_all_teams': 'ทุกทีม', 'filter_all_years': 'ทุกชั้นปี', 'filter_all_campus': 'ทุกวิทยาเขต', 'opt_md': 'MD (แพทยศาสตร์)', 'opt_nr': 'NR (พยาบาลศาสตร์)', 'opt_er': 'ER (ฉุกเฉินการแพทย์)', 'opt_cd': 'CD (สื่อสารความหมายฯ)', 'opt_staff': 'Staff (อาจารย์/บุคลากร)', 'opt_other': 'Other (อื่นๆ)', 'opt_grad': 'ศิษย์เก่า (Alumni)', 'opt_pyt': 'พญาไท', 'opt_cnmi': 'จักรีนฤบดินทร์', 'opt_salaya': 'ศาลายา', 'empty_db': 'ยังไม่มีสมาชิกในระบบ' }
}

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
    payload = { 'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET, 'grant_type': 'refresh_token', 'refresh_token': user['refresh_token'] }
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
    tz = timezone(timedelta(hours=7))
    now = datetime.datetime.now(tz)
    year_start = datetime.datetime(now.year, 1, 1, tzinfo=tz)
    month_start = datetime.datetime(now.year, now.month, 1, tzinfo=tz)
    q_month = (now.month - 1) // 3 * 3 + 1
    quarter_start = datetime.datetime(now.year, q_month, 1, tzinfo=tz)
    return int(month_start.timestamp()), int(quarter_start.timestamp()), int(year_start.timestamp())

def get_aqi():
    """Fetches AQI for Ratchathewi, Bangkok"""
    try:
        # Using a public feed URL. If AQI_TOKEN is 'demo', it uses the demo token.
        url = f"https://api.waqi.info/feed/ratchathewi/?token={AQI_TOKEN}"
        r = requests.get(url, timeout=5)
        data = r.json()
        if data['status'] == 'ok':
            aqi = data['data']['aqi']
            
            # Interpret AQI
            if aqi <= 50: return {'val': aqi, 'status': 'Good', 'color': '#4CAF50', 'msg': 'Air is great! Go run! 🏃💨'}
            elif aqi <= 100: return {'val': aqi, 'status': 'Moderate', 'color': '#FFC107', 'msg': 'Acceptable quality. Enjoy your run.'}
            elif aqi <= 150: return {'val': aqi, 'status': 'Unhealthy (Sens.)', 'color': '#FF9800', 'msg': 'Sensitive groups should reduce outdoor running.'}
            else: return {'val': aqi, 'status': 'Unhealthy', 'color': '#F44336', 'msg': 'Bad air! Use a treadmill or wear a mask! 😷'}
            
    except:
        pass
    return None

@app.context_processor
def inject_globals():
    lang = session.get('lang', 'th')
    tz = timezone(timedelta(hours=7))
    now = datetime.datetime.now(tz)
    theme = MONTH_THEMES.get(now.month, MONTH_THEMES[1])
    
    return dict(
        text=TRANSLATIONS[lang], current_lang=lang, 
        get_level=get_level, get_next_level=get_next_level,
        shirt_active=SHIRT_CAMPAIGN_ACTIVE,
        now_year=now.year, now_month=now.month, now_month_name=now.strftime("%B"),
        theme_color=theme['color'], theme_name=theme['name'],
        campaign_finished=(now > CAMPAIGN_END_DATE)
    )

@app.errorhandler(404)
def page_not_found(e): return render_template('404.html'), 404

@app.route('/set_lang/<lang_code>')
def set_lang(lang_code):
    if lang_code in ['en', 'th']: session['lang'] = lang_code
    return redirect(request.referrer or url_for('home'))

@app.route('/')
def home():
    db = load_db()
    tz = timezone(timedelta(hours=7))
    now = datetime.datetime.now(tz)
    current_month_key = now.strftime("%Y-%m")
    
    members = []
    
    # Logic for "Fun Facts"
    longest_run_champion = None
    max_single_run = 0

    for uid, data in db.items():
        # Get stats
        monthly_dist = (data.get('monthly_stats') or {}).get(current_month_key, 0)
        
        # Check Longest Run for this month
        user_max_run = (data.get('longest_runs') or {}).get(current_month_key, 0)
        if user_max_run > max_single_run:
            max_single_run = user_max_run
            longest_run_champion = {'name': data['firstname'], 'dist': user_max_run, 'pic': data['profile']}

        member_display = data.copy()
        member_display['display_dist'] = monthly_dist
        members.append(member_display)
        
    members.sort(key=lambda x: x['display_dist'], reverse=True)
    
    # Get Air Quality
    aqi_data = get_aqi()

    return render_template('index.html', members=members, aqi=aqi_data, fun_fact=longest_run_champion)

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
    
    activities = []
    page = 1
    while True:
        params = {'after': ts_year, 'per_page': 200, 'page': page}
        try:
            r = requests.get("https://www.strava.com/api/v3/athlete/activities", headers=headers, params=params)
            new_data = r.json()
            if not new_data or not isinstance(new_data, list): break
            activities.extend(new_data)
            if len(new_data) < 200: break
            page += 1
        except: break
            
    try:
        d_month, d_quarter, d_year = 0, 0, 0
        monthly_totals = {}
        monthly_max_run = {} # Track longest run per month
        
        for act in activities:
            if act.get('type') == 'Run' and act.get('visibility') == 'everyone':
                act_dt = datetime.datetime.strptime(act['start_date'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                act_ts = int(act_dt.timestamp())
                dist_km = act.get('distance', 0) / 1000
                
                d_year += dist_km
                if act_ts >= ts_quarter: d_quarter += dist_km
                if act_ts >= ts_month: d_month += dist_km
                
                # Bin by Month
                local_dt = act_dt + timedelta(hours=7)
                month_key = local_dt.strftime("%Y-%m")
                monthly_totals[month_key] = monthly_totals.get(month_key, 0) + dist_km
                
                # Track Longest Run for that month
                if dist_km > monthly_max_run.get(month_key, 0):
                    monthly_max_run[month_key] = dist_km
        
        earned_badges = [k for k, v in monthly_totals.items() if v >= 50]
        
        db = load_db()
        if user_id in db:
            # Preserve existing max runs if not calculated (e.g. partial sync), 
            # but here we resync everything so it's fine to overwrite.
            current_longest_runs = db[user_id].get('longest_runs', {})
            current_longest_runs.update(monthly_max_run)

            db[user_id].update({
                'dist_month': round(d_month, 2),
                'dist_quarter': round(d_quarter, 2),
                'dist_year': round(d_year, 2),
                'badges': earned_badges,
                'monthly_stats': monthly_totals,
                'longest_runs': current_longest_runs
            })
            save_db(db)
            flash('Synced successfully!', 'success')
    except: flash('Sync failed.', 'error')

    return redirect(url_for('profile'))

@app.route('/update_profile', methods=['POST'])
def update_profile():
    user_id = session.get('user_id')
    if not user_id: return redirect(url_for('login'))
    db = load_db()
    if user_id in db:
        show_strava = 'on' if request.form.get('show_strava') else 'off'
        db[user_id].update({
            'team': request.form.get('team'), 'year': request.form.get('year'),
            'campus': request.form.get('campus'), 'status': request.form.get('status'),
            'motto': request.form.get('motto'), 'shoe': request.form.get('shoe'),
            'fav_route': request.form.get('fav_route'), 'instagram': request.form.get('instagram'),
            'show_strava': show_strava
        })
        save_db(db)
        flash('Profile updated!', 'success')
    return redirect(url_for('profile'))

@app.route('/login')
def login():
    redirect_uri = url_for('callback', _external=True)
    return redirect(f"https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={redirect_uri}&approval_prompt=auto&scope=activity:read_all")

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code: return redirect(url_for('home'))
    redirect_uri = url_for('callback', _external=True)
    data = requests.post('https://www.strava.com/oauth/token', data={
        'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET, 'code': code, 'grant_type': 'authorization_code'
    }).json()
    if 'access_token' in data:
        uid = str(data['athlete']['id'])
        db = load_db()
        if uid not in db:
            db[uid] = {'dist_month': 0, 'dist_quarter': 0, 'dist_year': 0, 'badges': [], 'team': '', 'year': '', 'campus': '', 'status': '', 'motto': '', 'shoe': '', 'fav_route': '', 'instagram': '', 'show_strava': 'off', 'monthly_stats': {}, 'longest_runs': {}}
        db[uid].update({
            'strava_id': uid, 'firstname': data['athlete']['firstname'], 'lastname': data['athlete']['lastname'],
            'profile': data['athlete']['profile'], 'access_token': data['access_token'],
            'refresh_token': data['refresh_token'], 'expires_at': data['expires_at']
        })
        save_db(db)
        session.permanent = True; session['user_id'] = uid
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

@app.route('/admin')
def admin_hub():
    if session.get('user_id') not in ADMIN_IDS: return redirect(url_for('home'))
    return render_template('admin_hub.html')

@app.route('/admin/art')
def admin_art():
    if session.get('user_id') not in ADMIN_IDS: return redirect(url_for('home'))
    db = load_db(); total_km = sum(u.get('dist_year', 0) for u in db.values()); total_members = len(db)
    mvp = max(db.values(), key=lambda x: x.get('dist_year', 0)) if db else None
    return render_template('admin_art.html', total_km=int(total_km), total_members=total_members, mvp=mvp)

@app.route('/secret-finishers')
def finishers_hub():
    now = datetime.datetime.now()
    return render_template('finishers_hub.html', current_year=now.year, current_month=now.month)

@app.route('/secret-finishers/<int:year>/<int:month>')
def finishers_canvas(year, month):
    db = load_db()
    badge_key = f"{year}-{month:02d}"
    
    # 1. Filter Finishers
    finishers = [u for u in db.values() if badge_key in u.get('badges', [])]
    
    # 2. Sort logic
    finishers.sort(key=lambda x: (x.get('monthly_stats') or {}).get(badge_key, 0), reverse=True)
    
    # 3. Hist Theme
    hist_theme = MONTH_THEMES.get(month, MONTH_THEMES[1])
    
    return render_template('finishers.html', 
                           finishers=finishers, 
                           year=year, 
                           month_name=calendar.month_name[month],
                           badge_key=badge_key,
                           hist_theme=hist_theme)

if __name__ == '__main__': app.run(debug=True)