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
REDIRECT_URI = 'http://127.0.0.1:5000/callback' 
# --- DATABASE HANDLER ---
# This forces the app to look for the database in the SAME folder as the code
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'database.json')

# --- TRANSLATIONS (THAI & ENGLISH) ---
TRANSLATIONS = {
    'en': {
        'title': 'Ramathon Run Club',
        'nav_leaderboard': 'LEADERBOARD',
        'nav_rules': 'RULES',
        'nav_profile': 'MY PROFILE',
        'nav_connect': 'CONNECT STRAVA',
        'nav_logout': 'LOGOUT',
        'hero_title': "Ramathon 2026",
        'hero_badge': 'EST. 2021 • PHAYATHAI • BANGPHLI • SALAYA',
        'ledger_title': 'Runner Leaderboard',
        'ledger_sub': 'RANKINGS • JANUARY 2026',
        'rank_elite': '★ ELITE SQUAD',
        'rank_member': '♦ CLUB MEMBER',
        'rank_rookie': '• ROOKIE',
        'dist_month': 'Month Dist.',
        'goal_shirt': 'Target: 50KM Shirt',
        'goal_elite': 'Target: 100KM Elite',
        'stamp_qual': 'QUALIFIED',
        'profile_file': 'Member File',
        'status_claim': 'CLAIMABLE',
        'status_locked': 'LOCKED',
        'msg_close': 'Keep going! You are only',
        'msg_km_away': 'KM away from the club shirt.',
        'msg_win': 'Splendid! You have qualified. Visit the Faculty Lounge to claim.',
        'btn_sync': '⟳ Sync Strava',
        'rules_title': 'Club Regulations',
        'rules_1_title': '1. The Mission',
        'rules_1_text': 'Fostering health and camaraderie among Ramathibodi medical students and staff.',
        'rules_2_title': '2. The Rewards',
        'rules_2_li1': '50 KM: Qualify for the Club Monthly Shirt.',
        'rules_2_li2': '100 KM: Unlock Elite Monthly Status.',
        'rules_3_title': '3. Sync Rules',
        'rules_3_text': 'Only Public runs count.',
        'empty_db': 'No adventurers found yet.'
    },
    'th': {
        'title': 'Ramathon Run Club',
        'nav_leaderboard': 'ตารางคะแนน',
        'nav_rules': 'กติกา',
        'nav_profile': 'ข้อมูลส่วนตัว',
        'nav_connect': 'เชื่อมต่อ STRAVA',
        'nav_logout': 'ออกจากระบบ',
        'hero_title': "Ramathon 2026",
        'hero_badge': 'ก่อตั้ง ๒๕๖๔ • พญาไท • บางพลี • ศาลายา',
        'ledger_title': 'ตารางอันดับ',
        'ledger_sub': 'ประจำเดือน มกราคม ๒๕๖๙',
        'rank_elite': '★ ระดับอีลีท',
        'rank_member': '♦ สมาชิกคลับ',
        'rank_rookie': '• มือใหม่',
        'dist_month': 'ระยะเดือนนี้',
        'goal_shirt': 'เป้าหมาย: เสื้อวิ่ง 50 กม.',
        'goal_elite': 'เป้าหมาย: 100 กม.',
        'stamp_qual': 'ผ่านเกณฑ์',
        'profile_file': 'แฟ้มประวัติ',
        'status_claim': 'รับสิทธิ์ได้',
        'status_locked': 'ยังไม่ครบ',
        'msg_close': 'อีกนิดเดียว! คุณขาดอีกเพียง',
        'msg_km_away': 'กม. จะได้รับเสื้อวิ่ง',
        'msg_win': 'ยอดเยี่ยม! คุณผ่านเกณฑ์แล้ว ติดต่อรับของรางวัลได้ที่คณะ',
        'btn_sync': '⟳ อัพเดทข้อมูล',
        'rules_title': 'ระเบียบการ',
        'rules_1_title': '๑. พันธกิจ',
        'rules_1_text': 'ส่งเสริมสุขภาพและความสามัคคีในหมู่นักศึกษาและบุคลากรรามาธิบดี',
        'rules_2_title': '๒. รางวัล',
        'rules_2_li1': 'สะสมครบ ๕๐ กม.: รับเสื้อวิ่งประจำเดือน (Club Monthly Shirt)',
        'rules_2_li2': 'สะสมครบ ๑๐๐ กม.: ปลดล็อคระดับ Elite ประจำเดือน',
        'rules_3_title': '๓. กติกาการส่งผล',
        'rules_3_text': 'นับเฉพาะการวิ่ง และต้องตั้งค่าเป็นสาธารณะ (Public)',
        'empty_db': 'ยังไม่มีสมาชิกในระบบ'
    }
}

# --- DATABASE HELPERS ---
def load_db():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except: return {}

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# --- CONTEXT PROCESSOR (Injects Text into Templates) ---
@app.context_processor
def inject_text():
    """Automatically sends the right language text to every page"""
    lang = session.get('lang', 'th') # Default to English
    return dict(text=TRANSLATIONS[lang], current_lang=lang)

# --- ROUTES ---

@app.route('/set_lang/<lang_code>')
def set_lang(lang_code):
    """Switch Language"""
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

@app.route('/login')
def login():
    scope = "activity:read_all"
    strava_url = (f"https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}"
                  f"&response_type=code&redirect_uri={REDIRECT_URI}&approval_prompt=auto&scope={scope}")
    return redirect(strava_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code: return "No code received"
    
    token_url = 'https://www.strava.com/oauth/token'
    payload = {'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET, 'code': code, 'grant_type': 'authorization_code'}
    r = requests.post(token_url, data=payload)
    data = r.json()
    
    if 'access_token' not in data: return "Token Error"
    
    athlete = data['athlete']
    uid = str(athlete['id'])
    db = load_db()
    current_dist = db.get(uid, {}).get('total_distance', 0)
    
    db[uid] = {
        'strava_id': uid,
        'firstname': athlete['firstname'],
        'lastname': athlete['lastname'],
        'profile': athlete['profile'],
        'access_token': data['access_token'],
        'refresh_token': data['refresh_token'],
        'expires_at': data['expires_at'],
        'total_distance': current_dist
    }
    save_db(db)
    session['user_id'] = uid
    return redirect(url_for('profile'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/update_stats')
def update_stats():
    # (Same update logic as before - abbreviated for brevity)
    # Ensure you keep the 'visibility' check!
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=False)