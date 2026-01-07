from flask import Flask, render_template, request, redirect, url_for, session
import requests
import json
import os
import time
import datetime

app = Flask(__name__)
app.secret_key = 'RAMATHON_PURPLE_KEY'

# --- CONFIGURATION ---
CLIENT_ID = '194111'
CLIENT_SECRET = 'be307cce9818cd549fae09f324aa0a31c7da5add'

# We remove the hardcoded REDIRECT_URI here and generate it dynamically in the routes
# to ensure it matches exactly where the server is running (localhost vs 127.0.0.1).

# --- DATABASE HANDLER ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'database.json')

# --- TRANSLATIONS (THAI & ENGLISH) ---
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
        # Profile
        'profile_file': 'Member File',
        'status_claim': 'CLAIMABLE',
        'status_locked': 'LOCKED',
        'msg_close': 'Keep going! You are only',
        'msg_km_away': 'KM away from the club shirt.',
        'msg_win': 'Splendid! You have qualified. Visit the Faculty Lounge to claim.',
        'btn_sync': '⟳ Sync Strava',
        'btn_save': 'Save Profile',
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
        # Profile
        'profile_file': 'แฟ้มประวัติ',
        'status_claim': 'รับสิทธิ์ได้',
        'status_locked': 'ยังไม่ครบ',
        'msg_close': 'อีกนิดเดียว! คุณขาดอีกเพียง',
        'msg_km_away': 'กม. จะได้รับเสื้อวิ่ง',
        'msg_win': 'ยอดเยี่ยม! คุณผ่านเกณฑ์แล้ว ติดต่อรับของรางวัลได้ที่คณะ',
        'btn_sync': '⟳ อัพเดทข้อมูล Strava',
        'btn_save': 'บันทึกข้อมูล',
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

# --- DATABASE HELPERS ---
def load_db():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except: return {}

def save_db(data):
    try:
        with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving DB: {e}")

# --- CONTEXT PROCESSOR ---
@app.context_processor
def inject_text():
    lang = session.get('lang', 'th') 
    return dict(text=TRANSLATIONS[lang], current_lang=lang)

# --- ROUTES ---
@app.route('/set_lang/<lang_code>')
def set_lang(lang_code):
    if lang_code in ['en', 'th']:
        session['lang'] = lang_code
    return redirect(request.referrer or url_for('home'))

@app.route('/')
def home():
    db = load_db()
    members_list = list(db.values())
    members_list.sort(key=lambda x: x.get('total_distance', 0), reverse=True)
    return render_template('index.html', members=members_list)

@app.route('/rules')
def rules():
    return render_template('rules.html')

@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    if not user_id: return redirect(url_for('login'))
    db = load_db()
    user_data = db.get(user_id)
    if not user_data: return redirect(url_for('logout'))
    return render_template('profile.html', user=user_data)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    user_id = session.get('user_id')
    if not user_id: return redirect(url_for('login'))
    
    db = load_db()
    if user_id in db:
        db[user_id]['team'] = request.form.get('team')
        db[user_id]['year'] = request.form.get('year') 
        db[user_id]['status'] = request.form.get('status')
        db[user_id]['motto'] = request.form.get('motto')
        db[user_id]['shoe'] = request.form.get('shoe')
        
        save_db(db)
        
    return redirect(url_for('profile'))

@app.route('/login')
def login():
    # Dynamically generate the redirect URI to match the current server address
    # This prevents the 127.0.0.1 vs localhost mismatch
    redirect_uri = url_for('callback', _external=True)
    
    scope = "activity:read_all"
    strava_url = (f"https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}"
                  f"&response_type=code&redirect_uri={redirect_uri}&approval_prompt=auto&scope={scope}")
    return redirect(strava_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return f"<h1>Error from Strava</h1><p>{error}</p><a href='/'>Go Home</a>"
    if not code: 
        return "<h1>Error</h1><p>No code received from Strava.</p><a href='/'>Go Home</a>"
    
    # Dynamically match the Redirect URI used in login
    redirect_uri = url_for('callback', _external=True)

    token_url = 'https://www.strava.com/oauth/token'
    payload = {
        'client_id': CLIENT_ID, 
        'client_secret': CLIENT_SECRET, 
        'code': code, 
        'grant_type': 'authorization_code'
    }
    
    try:
        r = requests.post(token_url, data=payload)
        r.raise_for_status() # Check for HTTP errors
        data = r.json()
    except Exception as e:
        return f"<h1>Connection Error</h1><p>{str(e)}</p><p>Response: {r.text if 'r' in locals() else 'None'}</p>"
    
    if 'access_token' not in data: 
        return f"<h1>Token Error</h1><p>Strava did not return a token.</p><p>Debug info: {data}</p>"
    
    try:
        athlete = data['athlete']
        uid = str(athlete['id'])
        db = load_db()
        
        # Preserve existing stats if re-logging in
        existing_user = db.get(uid, {})
        current_dist = existing_user.get('total_distance', 0)
        current_team = existing_user.get('team', '')
        current_year = existing_user.get('year', '')
        current_status = existing_user.get('status', '')
        current_motto = existing_user.get('motto', '')
        current_shoe = existing_user.get('shoe', '')
        
        db[uid] = {
            'strava_id': uid,
            'firstname': athlete['firstname'],
            'lastname': athlete['lastname'],
            'profile': athlete['profile'],
            'access_token': data['access_token'],
            'refresh_token': data['refresh_token'],
            'expires_at': data['expires_at'],
            'total_distance': current_dist,
            'team': current_team,
            'year': current_year,
            'status': current_status,
            'motto': current_motto,
            'shoe': current_shoe
        }
        save_db(db)
        session['user_id'] = uid
        return redirect(url_for('profile'))
    except Exception as e:
        return f"<h1>Processing Error</h1><p>Failed to save user data.</p><p>{str(e)}</p>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/update_stats')
def update_stats():
    # Sync logic placeholder
    return redirect(url_for('home'))

# --- NEW EVENT ROUTES ---
@app.route('/events')
def events():
    return render_template('events.html')

@app.route('/events/meetups')
def meetups():
    return render_template('meetups.html')

@app.route('/events/recap2024')
def recap2024():
    return render_template('recap_2024.html')
    
if __name__ == '__main__':
    # ENABLE DEBUG MODE to see errors in browser
    app.run(debug=True)