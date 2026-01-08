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
        # Nav
        'nav_leaderboard': 'LEADERBOARD',
        'nav_events': 'EVENTS',
        'nav_rules': 'RULES',
        'nav_profile': 'MY PROFILE',
        'nav_connect': 'CONNECT STRAVA',
        'nav_logout': 'LOGOUT',
        # Home
        'hero_title': "Ramathon 2026",
        'hero_badge': 'EST. 2021 • PHAYATHAI • BANGPHLI • SALAYA',
        'stamp_qual': 'QUALIFIED',
        'rank_elite': '★ ELITE SQUAD',
        'rank_member': '♦ CLUB MEMBER',
        'rank_rookie': '• ROOKIE',
        'dist_month': 'Month Dist.',
        'goal_shirt': 'Target: 50KM Shirt',
        'goal_elite': 'Target: 100KM Elite',
        'empty_db': 'No adventurers found yet.',
        # Profile & RPG
        'profile_file': 'Member File',
        'status_claim': 'CLAIMABLE',
        'status_locked': 'LOCKED',
        'msg_close': 'Keep going! You are only',
        'msg_km_away': 'KM away from the club shirt.',
        'msg_win': 'Splendid! You have qualified. Visit the Faculty Lounge to claim.',
        'btn_sync': '⟳ Sync Strava',
        'btn_save': 'Save Profile',
        'view_profile': 'View Public Profile',
        # RPG Specific
        'stats_month': 'MONTHLY GRIND',
        'stats_quarter': 'QUARTERLY QUEST',
        'stats_total': 'ANNUAL RANK',
        'level_prefix': 'RANK',
        'badge_shirt_qual': 'SHIRT UNLOCKED',
        'badge_shirt_wait': 'ALREADY CLAIMED',
        'msg_shirt_win': 'You have qualified for the Quarterly Shirt! Contact staff to claim.',
        'msg_shirt_next': 'Great job! You have already claimed a shirt this year.',
        # Profile Form
        'lbl_team': 'Team / Affiliation',
        'lbl_year': 'Year / Role',
        'lbl_status': 'Status Message',
        'lbl_motto': 'Running Motto',
        'lbl_shoe': 'Battle Shoe',
        'opt_md': 'MD (Medicine)',
        'opt_nr': 'NR (Nursing)',
        'opt_er': 'ER (Paramedic)',
        'opt_cd': 'CD (Comm. Disorders)',
        'opt_staff': 'Staff / Faculty',
        'opt_other': 'Other',
        'opt_grad': 'Alumni / Grad',
        # Rules
        'rules_title': 'Club Regulations',
        'rules_1_title': '1. The Mission',
        'rules_1_text': 'Fostering health and camaraderie among Ramathibodi medical students and staff.',
        'rules_2_title': '2. The Rewards',
        'rules_2_li1': '50 KM: Qualify for the Club Monthly Shirt.',
        'rules_2_li2': '100 KM: Unlock Elite Monthly Status.',
        'rules_3_title': '3. Sync Rules',
        'rules_3_text': 'Only Public runs count.',
        # Events Hub
        'events_main_title': 'CLUB EVENTS',
        'badge_upcoming': 'UPCOMING',
        'badge_archive': 'ARCHIVE',
        'evt_meetup_title': '🏃 Ramathon Meetups',
        'evt_meetup_desc': "Join the 'Easy Pace' crew. Monthly runs at Suan Chitralada & Benchakitti Park.",
        'evt_meetup_btn': 'View Schedule →',
        'evt_recap_title': '📜 Virtual Run 2024 Recap',
        'evt_recap_desc': 'A look back at our previous success: 10,000+ KM ran by 283 Ramathibodians.',
        'evt_recap_btn': 'Read Report →',
        # Meetups Page
        'meetup_page_title': 'Ramathon Meetups',
        'meetup_quote': '"From Virtual to Reality"',
        'meetup_card_title': '🌳 The "Easy Pace" Sundays',
        'meetup_card_text': 'Connect with fellow medics, nurses, and staff in a relaxed environment. No PBs, just vibes.',
        'meetup_loc_label': 'Locations:',
        'meetup_loc_val': 'Suan Chitralada & Benchakitti Park',
        'meetup_time_label': 'Time:',
        'meetup_time_val': 'Every last Sunday of the month, 06:00 AM',
        'meetup_pace_label': 'Pace:',
        'meetup_pace_val': 'Zone 2 (Conversation Pace)',
        'meetup_next_box': 'Next Session:',
        'meetup_next_date': 'February 22, 2026 @ Benchakitti Park',
        'meetup_meeting_point': 'Meeting Point: Main Amphitheater',
        # Recap 2024 Page
        'recap_top_label': 'ARCHIVE REPORT: TK13',
        'recap_main_title': 'Virtual Ramathon 2024',
        'recap_date': 'November 1 - 30, 2024',
        'recap_stat_runners': 'Runners Joined',
        'recap_stat_km': 'Total KM Ran',
        'recap_stat_finishers': 'Finishers',
        'recap_roster_title': 'The Roster',
        'recap_baby': 'Baby Marathon (30k)',
        'recap_super': 'Super Marathon (50k)',
        'recap_voices_title': 'Voices from the Track',
        'recap_q1': '"Helped me lose 3-4 kg with quality! Gave me so much confidence."',
        'recap_q2': '"Better mental health. Body feels stronger and I have more energy."',
        'recap_q3': '"A reason to get out of bed and put on running shoes even on lazy days."',
        'recap_budget_title': 'Budget Summary (Transparent)',
        'recap_grant': 'Grant Received:',
        'recap_used': 'Actual Used:',
        'recap_returned': 'Returned to Faculty:',
        'recap_footer': 'Data sourced from Official Report: TK13 / 9 Jan 2025'
    },
    'th': {
        'title': 'Ramathon Run Club',
        # Nav
        'nav_leaderboard': 'ตารางคะแนน',
        'nav_events': 'กิจกรรม',
        'nav_rules': 'กติกา',
        'nav_profile': 'ข้อมูลส่วนตัว',
        'nav_connect': 'เชื่อมต่อ STRAVA',
        'nav_logout': 'ออกจากระบบ',
        # Home
        'hero_title': "รามาธอน ๒๕๖๙",
        'hero_badge': 'ก่อตั้ง ๒๕๖๔ • พญาไท • บางพลี • ศาลายา',
        'stamp_qual': 'ผ่านเกณฑ์',
        'rank_elite': '★ ระดับอีลีท',
        'rank_member': '♦ สมาชิกคลับ',
        'rank_rookie': '• มือใหม่',
        'dist_month': 'ระยะเดือนนี้',
        'goal_shirt': 'เป้าหมาย: เสื้อวิ่ง 50 กม.',
        'goal_elite': 'เป้าหมาย: 100 กม.',
        'empty_db': 'ยังไม่มีสมาชิกในระบบ',
        # Profile & RPG
        'profile_file': 'แฟ้มประวัติ',
        'status_claim': 'รับสิทธิ์ได้',
        'status_locked': 'ยังไม่ครบ',
        'msg_close': 'อีกนิดเดียว! คุณขาดอีกเพียง',
        'msg_km_away': 'กม. จะได้รับเสื้อวิ่ง',
        'msg_win': 'ยอดเยี่ยม! คุณผ่านเกณฑ์แล้ว ติดต่อรับของรางวัลได้ที่คณะ',
        'btn_sync': '⟳ อัพเดทข้อมูล Strava',
        'btn_save': 'บันทึกข้อมูล',
        'view_profile': 'ดูโปรไฟล์',
        # RPG Specific
        'stats_month': 'ภารกิจรายเดือน',
        'stats_quarter': 'พิชิตเสื้อ (ไตรมาส)',
        'stats_total': 'ระดับนักวิ่ง (ทั้งปี)',
        'level_prefix': 'ระดับ',
        'badge_shirt_qual': 'รับเสื้อได้',
        'badge_shirt_wait': 'รับสิทธิ์แล้ว',
        'msg_shirt_win': 'ยินดีด้วย! คุณผ่านเกณฑ์รับเสื้อประจำไตรมาสนี้ ติดต่อรับได้ที่คณะ',
        'msg_shirt_next': 'ยอดเยี่ยม! (คุณได้รับสิทธิ์เสื้อของปีนี้ไปแล้ว)',
        # Profile Form
        'lbl_team': 'สังกัด / ทีม',
        'lbl_year': 'ชั้นปี / ตำแหน่ง',
        'lbl_status': 'สเตตัสวันนี้',
        'lbl_motto': 'คติประจำใจนักวิ่ง',
        'lbl_shoe': 'รองเท้าคู่ใจ',
        'opt_md': 'MD (แพทยศาสตร์)',
        'opt_nr': 'NR (พยาบาลศาสตร์)',
        'opt_er': 'ER (ฉุกเฉินการแพทย์)',
        'opt_cd': 'CD (สื่อสารความหมายฯ)',
        'opt_staff': 'Staff (อาจารย์/บุคลากร)',
        'opt_other': 'Other (อื่นๆ)',
        'opt_grad': 'ศิษย์เก่า (Alumni)',
        # Rules
        'rules_title': 'ระเบียบการ',
        'rules_1_title': '๑. พันธกิจ',
        'rules_1_text': 'ส่งเสริมสุขภาพและความสามัคคีในหมู่นักศึกษาและบุคลากรรามาธิบดี',
        'rules_2_title': '๒. รางวัล',
        'rules_2_li1': 'สะสมครบ ๕๐ กม.: รับเสื้อวิ่งประจำเดือน (Club Monthly Shirt)',
        'rules_2_li2': 'สะสมครบ ๑๐๐ กม.: ปลดล็อคระดับ Elite ประจำเดือน',
        'rules_3_title': '๓. กติกาการส่งผล',
        'rules_3_text': 'นับเฉพาะการวิ่ง และต้องตั้งค่าเป็นสาธารณะ (Public)',
        # Events Hub
        'events_main_title': 'กิจกรรมชมรม',
        'badge_upcoming': 'เร็วๆ นี้',
        'badge_archive': 'ทำเนียบรุ่น',
        'evt_meetup_title': '🏃 นัดวิ่งรามาธอน (Meetups)',
        'evt_meetup_desc': "เข้าร่วมกลุ่ม 'Easy Pace' วิ่งสบายๆ ทุกเดือนที่สวนจิตรลดา และ สวนเบญจกิติ",
        'evt_meetup_btn': 'ดูตารางกิจกรรม →',
        'evt_recap_title': '📜 สรุปผล Virtual Run 2024',
        'evt_recap_desc': 'ย้อนดูความสำเร็จในปีที่ผ่านมา: ระยะทางรวมกว่า 10,000 กม. จากชาวรามาธิบดี 283 ท่าน',
        'evt_recap_btn': 'อ่านรายงานสรุป →',
        # Meetups Page
        'meetup_page_title': 'นัดวิ่งรามาธอน',
        'meetup_quote': '"จากโลกออนไลน์ สู่สนามจริง"',
        'meetup_card_title': '🌳 อาทิตย์วิ่งสบาย (The "Easy Pace" Sundays)',
        'meetup_card_text': 'พบปะเพื่อนนักศึกษา แพทย์ พยาบาล และบุคลากรในบรรยากาศสบายๆ ไม่เน้นทำเวลา เน้นมิตรภาพ',
        'meetup_loc_label': 'สถานที่:',
        'meetup_loc_val': 'สวนจิตรลดา และ สวนเบญจกิติ',
        'meetup_time_label': 'เวลา:',
        'meetup_time_val': 'ทุกวันอาทิตย์สุดท้ายของเดือน เวลา 06:00 น.',
        'meetup_pace_label': 'เพซ (Pace):',
        'meetup_pace_val': 'โซน 2 (Conversation Pace วิ่งไปคุยไป)',
        'meetup_next_box': 'นัดถัดไป:',
        'meetup_next_date': '22 กุมภาพันธ์ 2569 @ สวนเบญจกิติ',
        'meetup_meeting_point': 'จุดนัดพบ: อัฒจันทร์ใหญ่ (Amphitheater)',
        # Recap 2024 Page
        'recap_top_label': 'รายงานสรุปผล: TK13',
        'recap_main_title': 'Virtual Ramathon 2024',
        'recap_date': '1 - 30 พฤศจิกายน 2567',
        'recap_stat_runners': 'ผู้เข้าร่วม',
        'recap_stat_km': 'ระยะทางรวม',
        'recap_stat_finishers': 'ผู้พิชิตเป้าหมาย',
        'recap_roster_title': 'ทำเนียบนักวิ่ง',
        'recap_baby': 'Baby Marathon (30k)',
        'recap_super': 'Super Marathon (50k)',
        'recap_voices_title': 'เสียงจากสนามวิ่ง',
        'recap_q1': '"ช่วยลดน้ำหนักผมลงไป 3-4 กก.แบบมีคุณภาพครับ ส่งผลให้มีความมั่นใจมากขึ้น"',
        'recap_q2': '"สุขภาพจิตดีขึ้น ร่างกายแข็งแรงขึ้น มีแรงมากขึ้น"',
        'recap_q3': '"ทำให้มีข้ออ้างพาตัวเองไปออกกำลังกายครับ (เริ่มต้นวันด้วยจิตใจที่สดชื่น)"',
        'recap_budget_title': 'สรุปงบประมาณ (โปร่งใส)',
        'recap_grant': 'งบประมาณที่ได้รับ:',
        'recap_used': 'ใช้จ่ายจริง:',
        'recap_returned': 'ยอดเงินคืนคณะฯ:',
        'recap_footer': 'ข้อมูลจากรายงานโครงการฉบับสมบูรณ์: TK13 / 9 ม.ค. 2568'
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