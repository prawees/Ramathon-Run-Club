from flask import Flask, render_template, request, redirect, url_for, session, abort, flash
import requests
import json
import os
import time
import datetime
from datetime import timezone, timedelta
import calendar
import random # [NEW] Import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# SECURITY
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev_key')
CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
AQI_TOKEN = os.getenv('AQI_TOKEN', 'demo') 

# CONFIGURATION
app.permanent_session_lifetime = datetime.timedelta(days=365)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'database.json')

# --- CONSTANTS ---
SHIRT_CAMPAIGN_ACTIVE = False
CAMPAIGN_END_DATE = datetime.datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone(timedelta(hours=7)))
ADMIN_IDS = ['48771896'] 

# [NEW] Animal List for Random Emoji
ANIMALS = ['🦖', '🐆', '🐇', '🐢', '🐎', '🦌', '🐅', '🦈', '🦅', '🦍', '🐉', '🐕', '🦄']

# [NEW] Thai Month Abbreviations for Future-proofing
THAI_MONTHS_ABBR = [
    "", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
    "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."
]

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
    'en': { 
        'title': 'Ramathon Run Club', 'nav_leaderboard': 'LEADERBOARD', 'nav_events': 'EVENTS', 'nav_rules': 'RULES', 'nav_profile': 'MY PROFILE', 'nav_connect': 'CONNECT STRAVA', 'nav_logout': 'LOGOUT', 'btn_sync': '⟳ Sync Strava', 'btn_save': 'Save Profile', 'view_profile': 'View Public Profile', 'footer_line': 'Join OpenChat', 
        'countdown_intro': "The fun starts now! Let's run Ramathibodians! Link your Strava now!", 'countdown_sub': "Shirt Quest starts Q2 2026: Apr 1st! (But Yearly Rank XP accumulation starts TODAY!)", 'countdown_label': 'SEASON STARTS IN:', 
        'stats_month': 'MONTHLY GRIND', 'stats_quarter': 'QUARTERLY QUEST', 'stats_total': 'ANNUAL CAREER', 'level_prefix': 'RANK', 'xp_to_next': 'KM to level up to', 'xp_max': 'MAX LEVEL REACHED', 'xp_desc': '(Yearly XP - Resets Jan 1st)', 'locked_q2': 'UNLOCKS Q2 2026', 
        'badge_section': 'MONTHLY BADGES', 'badge_locked': 'Locked', 'badge_shirt_qual': 'SHIRT UNLOCKED', 'badge_shirt_wait': 'ALREADY CLAIMED', 'msg_shirt_win': 'You have qualified for the Quarterly Shirt! Contact staff to claim.', 'msg_shirt_next': 'Great job! You have already claimed a shirt this year.', 
        'ig_promo': "✨ Special: Link IG by 25 Mar '26 to win a Starbucks Card! ☕", 'ig_verified': 'IG Verified', 
        'lbl_team': 'Team / Affiliation', 'lbl_year': 'Year / Role', 'lbl_campus': 'Campus', 'lbl_status': 'Status Message', 'lbl_motto': 'Running Motto', 'lbl_shoe': 'Battle Shoe', 'lbl_route': 'Fav. Running Route', 'lbl_social': 'Social Connect', 'lbl_ig': 'Instagram Handle (no @)', 'lbl_show_strava': 'Show Strava Link on Profile', 
        'filter_search': 'Search Name...', 'filter_all_teams': 'All Teams', 'filter_all_years': 'All Years', 'filter_all_campus': 'All Campuses', 'opt_md': 'MD (Medicine)', 'opt_nr': 'NR (Nursing)', 'opt_er': 'ER (Paramedic)', 'opt_cd': 'CD (Comm. Disorders)', 'opt_staff': 'Staff / Faculty', 'opt_other': 'Other', 'opt_grad': 'Alumni / Grad', 'opt_pyt': 'PYT (Phayathai)', 'opt_cnmi': 'CNMI (Chakri)', 'opt_salaya': 'Salaya', 
        'empty_db': 'No adventurers found yet.', 'events_main_title': 'CLUB EVENTS', 'badge_upcoming': 'UPCOMING', 'badge_archive': 'ARCHIVE', 'evt_meetup_title': '🏃 Ramathon Meetups', 'evt_meetup_desc': "Join the 'Easy Pace' crew. Monthly runs at Suan Chitralada & Benchakitti Park.", 'evt_meetup_btn': 'View Schedule →', 'evt_recap_title': '📜 Virtual Run 2024 Recap', 'evt_recap_desc': 'A look back at our previous success: 10,000+ KM ran by 283 Ramathibodians.', 'evt_recap_btn': 'Read Report →', 
        'rules_title': 'Club Regulations', 'rpg_title': '2. The RPG System', 'rpg_monthly_title': 'Monthly Mission', 'rpg_monthly_desc': 'Goal: 50 KM. Resets every month. Collect badges!', 'rpg_quarterly_title': 'Quarterly Quest', 'rpg_quarterly_desc': 'Goal: 100 KM within the current quarter. Unlocks Shirt (1/Year).', 'rpg_quarterly_note': '(Distance resets every quarter: Jan-Mar, Apr-Jun, etc.)', 'rpg_annual_title': 'Annual Career Ranks', 'rpg_annual_desc': 'Accumulate distance all year to rank up!', 'rpg_special_title': 'Year-End Rewards', 'rpg_special_a': 'Class A Finishers: Lucky draw for 5x Running Gear Sets.', 'rpg_special_s': 'Class S Finishers: Lucky draw for Shokz OpenRun Pro 2.', 
        'rules_1_title': '1. The Mission', 'rules_1_text': 'Fostering health and camaraderie among Ramathibodi medical students and staff.', 'rules_2_title': '2. The Rewards', 'rules_2_li1': '50 KM: Qualify for the Club Monthly Shirt.', 'rules_2_li2': '100 KM: Unlock Elite Monthly Status.', 'rules_3_title': '3. Sync Rules', 'rules_3_text': 'Only Public runs count.', 
        'recap_top_label': 'ARCHIVE REPORT: TK13', 'recap_main_title': 'Virtual Ramathon 2024', 'recap_date': 'November 1 - 30, 2024', 'recap_stat_runners': 'Runners Joined', 'recap_stat_km': 'Total KM Ran', 'recap_stat_finishers': 'Finishers', 'recap_roster_title': 'The Roster', 'recap_baby': 'Baby Marathon (30k)', 'recap_super': 'Super Marathon (50k)', 'recap_voices_title': 'Voices from the Track', 'recap_q1': '"Helped me lose 3-4 kg with quality! Gave me so much confidence."', 'recap_q2': '"Better mental health. Body feels stronger and I have more energy."', 'recap_q3': '"A reason to get out of bed and put on running shoes even on lazy days."', 'recap_budget_title': 'Budget Summary (Transparent)', 'recap_grant': 'Grant Received:', 'recap_used': 'Actual Used:', 'recap_returned': 'Returned to Faculty:', 'recap_footer': 'Data sourced from Official Report: TK13 / 9 Jan 2025', 
        'meetup_page_title': 'Ramathon Meetups', 'meetup_quote': '"From Virtual to Reality"', 'meetup_card_title': '🌳 The "Easy Pace" Sundays', 'meetup_card_text': 'Connect with fellow medics, nurses, and staff in a relaxed environment. No PBs, just vibes.', 'meetup_loc_label': 'Locations:', 'meetup_loc_val': 'Suan Chitralada & Benchakitti Park', 'meetup_time_label': 'Time:', 'meetup_time_val': 'Every last Sunday of the month, 06:00 AM', 'meetup_pace_label': 'Pace:', 'meetup_pace_val': 'Zone 2 (Conversation Pace)', 'meetup_next_box': 'Next Session:', 'meetup_next_date': 'February 22, 2026 @ Benchakitti Park', 'meetup_meeting_point': 'Meeting Point: Main Amphitheater', 
        'aqi_good': 'Air is great! Go run! 🏃💨', 'aqi_mod': 'Acceptable. Enjoy run.', 'aqi_sens': 'Sensitive: Reduce run.', 'aqi_bad': 'Bad air! Use treadmill! 😷',
        # [NEW] Stats Labels
        'stat_longest_run': 'Longest Run',
        'stat_club_total': 'Club Total',
        'stat_mvp_year': 'Year MVP (XP)'
    },
    'th': { 
        'title': 'Ramathon Run Club', 'nav_leaderboard': 'ตารางคะแนน', 'nav_events': 'กิจกรรม', 'nav_rules': 'กติกา', 'nav_profile': 'ข้อมูลส่วนตัว', 'nav_connect': 'เชื่อมต่อ STRAVA', 'nav_logout': 'ออกจากระบบ', 'btn_sync': '⟳ อัพเดทข้อมูล', 'btn_save': 'บันทึกข้อมูล', 'view_profile': 'ดูโปรไฟล์', 'footer_line': 'เข้ากลุ่ม OpenChat', 
        'countdown_intro': "ความสนุกเริ่มแล้ว! ชาวรามาธิบดีเชื่อมต่อ Strava แล้วออกวิ่งได้เลย!", 'countdown_sub': "ภารกิจชิงเสื้อเริ่ม Q2 2569: 1 เมษายน 2569 (แต่เริ่มสะสมระยะทางประจำปีเพื่อลุ้นรางวัลใหญ่ได้ตั้งแต่วันนี้)", 'countdown_label': 'เปิดซีซั่นในอีก:', 
        'stats_month': 'ภารกิจรายเดือน', 'stats_quarter': 'ภารกิจพิชิตเสื้อ', 'stats_total': 'ระดับนักวิ่ง (XP)', 'level_prefix': 'ระดับ', 'xp_to_next': 'กม. สู่ระดับ', 'xp_max': 'ระดับสูงสุด', 'xp_desc': '(สะสมรายปี - รีเซ็ต 1 ม.ค.)', 'locked_q2': 'เปิดระบบ Q2 2569', 
        'badge_section': 'เหรียญตราประจำเดือน', 'badge_locked': 'ยังไม่ปลดล็อค', 'badge_shirt_qual': 'รับเสื้อได้', 'badge_shirt_wait': 'รับสิทธิ์แล้ว', 'msg_shirt_win': 'ยินดีด้วย! คุณผ่านเกณฑ์รับเสื้อประจำไตรมาสนี้ ติดต่อรับได้ที่คณะ', 'msg_shirt_next': 'ยอดเยี่ยม! (คุณได้รับสิทธิ์เสื้อของปีนี้ไปแล้ว)', 
        'ig_promo': "✨ พิเศษ: ใส่ IG ภายใน 25 มี.ค. 69 ลุ้นรับ Starbucks Card! ☕", 'ig_verified': 'IG Verified', 
        'lbl_team': 'สังกัด / ทีม', 'lbl_year': 'ชั้นปี / ตำแหน่ง', 'lbl_campus': 'วิทยาเขตหลัก', 'lbl_status': 'สเตตัสวันนี้', 'lbl_motto': 'คติประจำใจนักวิ่ง', 'lbl_shoe': 'รองเท้าคู่ใจ', 'lbl_route': 'เส้นทางวิ่งโปรด', 'lbl_social': 'ช่องทางติดต่อ', 'lbl_ig': 'Instagram ID (ไม่ต้องใส่ @)', 'lbl_show_strava': 'แสดงปุ่ม Strava บนหน้าโปรไฟล์', 
        'filter_search': 'ค้นหาชื่อ...', 'filter_all_teams': 'ทุกทีม', 'filter_all_years': 'ทุกชั้นปี', 'filter_all_campus': 'ทุกวิทยาเขต', 'opt_md': 'MD (แพทยศาสตร์)', 'opt_nr': 'NR (พยาบาลศาสตร์)', 'opt_er': 'ER (ฉุกเฉินการแพทย์)', 'opt_cd': 'CD (สื่อสารความหมายฯ)', 'opt_staff': 'Staff (อาจารย์/บุคลากร)', 'opt_other': 'Other (อื่นๆ)', 'opt_grad': 'ศิษย์เก่า (Alumni)', 'opt_pyt': 'พญาไท', 'opt_cnmi': 'จักรีนฤบดินทร์', 'opt_salaya': 'ศาลายา', 
        'empty_db': 'ยังไม่มีสมาชิกในระบบ', 'events_main_title': 'กิจกรรมชมรม', 'badge_upcoming': 'เร็วๆ นี้', 'badge_archive': 'ทำเนียบรุ่น', 'evt_meetup_title': '🏃 นัดวิ่งรามาธอน (Meetups)', 'evt_meetup_desc': "เข้าร่วมกลุ่ม 'Easy Pace' วิ่งสบายๆ ทุกเดือนที่สวนจิตรลดา และ สวนเบญจกิติ", 'evt_meetup_btn': 'ดูตารางกิจกรรม →', 'evt_recap_title': '📜 สรุปผล Virtual Run 2024', 'evt_recap_desc': 'ย้อนดูความสำเร็จในปีที่ผ่านมา: ระยะทางรวมกว่า 10,000 กม. จากชาวรามาธิบดี 283 ท่าน', 'evt_recap_btn': 'อ่านรายงานสรุป →', 
        'rules_title': 'ระเบียบการ', 'rpg_title': '๒. ระบบเลเวลและภารกิจ', 'rpg_monthly_title': 'ภารกิจรายเดือน', 'rpg_monthly_desc': 'เป้าหมาย: 50 กม. รีเซ็ตทุกเดือน สะสมเหรียญเดือน!', 'rpg_quarterly_title': 'ภารกิจพิชิตเสื้อ (ไตรมาส)', 'rpg_quarterly_desc': 'เป้าหมาย: 100 กม. ภายในไตรมาสเพื่อรับเสื้อ (จำกัด 1 ตัว/ปี)', 'rpg_quarterly_note': '(ระยะสะสมนับใหม่ทุกไตรมาส: ม.ค.-มี.ค., เม.ย.-มิ.ย. เป็นต้น)', 'rpg_annual_title': 'ระดับนักวิ่งประจำปี', 'rpg_annual_desc': 'สะสมระยะวิ่งทั้งปีเพื่อเลื่อนยศ!', 'rpg_special_title': 'รางวัลพิเศษปลายปี', 'rpg_special_a': 'ผู้จบ Class A: ลุ้นรับรางวัลอุปกรณ์วิ่ง 5 รางวัล', 'rpg_special_s': 'ผู้จบ Class S: ลุ้นรับหูฟัง Shokz OpenRun Pro 2', 
        'rules_1_title': '๑. พันธกิจ', 'rules_1_text': 'ส่งเสริมสุขภาพและความสามัคคีในหมู่นักศึกษาและบุคลากรรามาธิบดี', 'rules_2_title': '๒. รางวัล', 'rules_2_li1': 'สะสมครบ ๕๐ กม.: รับเสื้อวิ่งประจำเดือน (Club Monthly Shirt)', 'rules_2_li2': 'สะสมครบ ๑๐๐ กม.: ปลดล็อคระดับ Elite ประจำเดือน', 'rules_3_title': '๓. กติกาการส่งผล', 'rules_3_text': 'นับเฉพาะการวิ่ง และต้องตั้งค่าเป็นสาธารณะ (Public)', 
        'recap_top_label': 'รายงานสรุปผล: TK13', 'recap_main_title': 'Virtual Ramathon 2024', 'recap_date': '1 - 30 พฤศจิกายน 2567', 'recap_stat_runners': 'ผู้เข้าร่วม', 'recap_stat_km': 'ระยะทางรวม', 'recap_stat_finishers': 'ผู้พิชิตเป้าหมาย', 'recap_roster_title': 'ทำเนียบนักวิ่ง', 'recap_baby': 'Baby Marathon (30k)', 'recap_super': 'Super Marathon (50k)', 'recap_voices_title': 'เสียงจากสนามวิ่ง', 'recap_q1': '"ช่วยลดน้ำหนักผมลงไป 3-4 กก.แบบมีคุณภาพครับ ส่งผลให้มีความมั่นใจมากขึ้น"', 'recap_q2': '"สุขภาพจิตดีขึ้น ร่างกายแข็งแรงขึ้น มีแรงมากขึ้น"', 'recap_q3': '"ทำให้มีข้ออ้างพาตัวเองไปออกกำลังกายครับ (เริ่มต้นวันด้วยจิตใจที่สดชื่น)"', 'recap_budget_title': 'สรุปงบประมาณ (โปร่งใส)', 'recap_grant': 'งบประมาณที่ได้รับ:', 'recap_used': 'ใช้จ่ายจริง:', 'recap_returned': 'ยอดเงินคืนคณะฯ:', 'recap_footer': 'ข้อมูลจากรายงานโครงการฉบับสมบูรณ์: TK13 / 9 ม.ค. 2568', 
        'meetup_page_title': 'นัดวิ่งรามาธอน', 'meetup_quote': '"จากโลกออนไลน์ สู่สนามจริง"', 'meetup_card_title': '🌳 อาทิตย์วิ่งสบาย (The "Easy Pace" Sundays)', 'meetup_card_text': 'พบปะเพื่อนนักศึกษา แพทย์ พยาบาล และบุคลากรในบรรยากาศสบายๆ ไม่เน้นทำเวลา เน้นมิตรภาพ', 'meetup_loc_label': 'สถานที่:', 'meetup_loc_val': 'สวนจิตรลดา และ สวนเบญจกิติ', 'meetup_time_label': 'เวลา:', 'meetup_time_val': 'ทุกวันอาทิตย์สุดท้ายของเดือน เวลา 06:00 น.', 'meetup_pace_label': 'เพซ (Pace):', 'meetup_pace_val': 'โซน 2 (Conversation Pace วิ่งไปคุยไป)', 'meetup_next_box': 'นัดถัดไป:', 'meetup_next_date': '22 กุมภาพันธ์ 2569 @ สวนเบญจกิติ', 'meetup_meeting_point': 'จุดนัดพบ: อัฒจันทร์ใหญ่ (Amphitheater)', 'aqi_good': 'อากาศดี (วิ่งได้โลด! 🏃💨)', 'aqi_mod': 'ปานกลาง (วิ่งได้ปกติ)', 'aqi_sens': 'เริ่มมีผลกระทบ (กลุ่มเสี่ยงลดการวิ่ง)', 'aqi_bad': 'อากาศแย่! (งดวิ่งกลางแจ้ง 😷)',
        # [NEW] Stats Labels
        'stat_longest_run': 'วิ่งไกลสุดเดือนนี้',
        'stat_club_total': 'ระยะรวมชมรมเดือนนี้',
        'stat_mvp_year': 'สะสมสูงสุดแห่งปี (MVP)'
    }
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

def get_aqi(lang='th'):
    """Fetches AQI with Fallback and Translated Messages"""
    try:
        url = f"https://api.waqi.info/feed/ratchathewi/?token={AQI_TOKEN}"
        r = requests.get(url, timeout=3)
        data = r.json()
        
        if data.get('status') != 'ok':
            url = f"https://api.waqi.info/feed/bangkok/?token={AQI_TOKEN}"
            r = requests.get(url, timeout=3)
            data = r.json()

        if data.get('status') == 'ok':
            aqi = data['data']['aqi']
            msgs = TRANSLATIONS[lang]
            if aqi <= 50: return {'val': aqi, 'status': 'Good', 'color': '#4CAF50', 'msg': msgs['aqi_good']}
            elif aqi <= 100: return {'val': aqi, 'status': 'Moderate', 'color': '#FFC107', 'msg': msgs['aqi_mod']}
            elif aqi <= 150: return {'val': aqi, 'status': 'Unhealthy (Sens.)', 'color': '#FF9800', 'msg': msgs['aqi_sens']}
            else: return {'val': aqi, 'status': 'Unhealthy', 'color': '#F44336', 'msg': msgs['aqi_bad']}
    except:
        pass
    
    return {'val': '-', 'status': 'No Data', 'color': '#9E9E9E', 'msg': 'API Error'}

@app.context_processor
def inject_globals():
    lang = session.get('lang', 'th')
    tz = timezone(timedelta(hours=7))
    now = datetime.datetime.now(tz)
    theme = MONTH_THEMES.get(now.month, MONTH_THEMES[1])
    
    # [NEW] Random Animal & Dynamic Date Formatting
    random_animal = random.choice(ANIMALS)
    if lang == 'th':
        # "ก.พ." format
        month_abbr = THAI_MONTHS_ABBR[now.month]
        date_display = f"({month_abbr})"
    else:
        # "Feb" format
        date_display = f"({now.strftime('%b')})"

    return dict(
        text=TRANSLATIONS[lang], current_lang=lang, 
        get_level=get_level, get_next_level=get_next_level,
        shirt_active=SHIRT_CAMPAIGN_ACTIVE,
        now_year=now.year, now_month=now.month, 
        now_month_name=now.strftime("%B"),
        now_month_abbr=date_display, # [NEW] Future-proof short month
        random_animal=random_animal, # [NEW] Random Emoji
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
    
    # Stats Containers
    longest_run_champion = None
    max_single_run = 0
    total_month_km = 0 # [NEW]

    for uid, data in db.items():
        monthly_dist = (data.get('monthly_stats') or {}).get(current_month_key, 0)
        total_month_km += monthly_dist # [NEW] Accumulate club total

        user_max_run = (data.get('longest_runs') or {}).get(current_month_key, 0)
        
        if user_max_run > max_single_run:
            max_single_run = user_max_run
            longest_run_champion = {'name': data['firstname'], 'dist': user_max_run, 'pic': data['profile']}

        member_display = data.copy()
        member_display['display_dist'] = monthly_dist
        members.append(member_display)
        
    # [NEW] Calculate MVP of the Year
    mvp_year_data = None
    if members:
        sorted_by_year = sorted(members, key=lambda x: x.get('dist_year', 0), reverse=True)
        if sorted_by_year[0].get('dist_year', 0) > 0:
            top = sorted_by_year[0]
            mvp_year_data = {'name': top['firstname'], 'dist': top.get('dist_year', 0), 'pic': top['profile']}

    # Sort Leaderboard
    members.sort(key=lambda x: (x['display_dist'], x.get('dist_year', 0)), reverse=True)
    
    lang = session.get('lang', 'th')
    aqi_data = get_aqi(lang)

    # [NEW] Pack all stats into one dictionary for the template
    fun_stats = {
        'longest_run': longest_run_champion,
        'club_total': total_month_km,
        'mvp_year': mvp_year_data
    }

    return render_template('index.html', members=members, aqi=aqi_data, fun_stats=fun_stats)