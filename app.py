from flask import Flask, request, jsonify, send_from_directory, Response
import os, requests, sqlite3, hmac, html
from datetime import datetime, timezone
app = Flask(__name__, static_folder="static", static_url_path="/static")
# ===================== تنظیمات امن =====================
# مقادیر محرمانه را در Environment Variables هاست تنظیم کنید، نه در کد عمومی.
OPENAI_API_KEY = "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"
OPENAI_MODEL = "gpt-4o-mini"
ADMIN_PASSWORD = "Amani_2026"
TELEGRAM_BOT_TOKEN = "8780530022:AAGpoovO1BQlwFjM9IKyF5OAWwhqlfHtdGQ"
TELEGRAM_ADMIN_CHAT_ID = "8764900501"
DATABASE_PATH = "team810_stats.sqlite3"
# ===========================================================
PROMPTS = {
 "math": "You are a careful mathematics tutor. Solve step by step. Reply in the user's language.",
 "physics": "You are a careful physics tutor. Explain and solve step by step with units. Reply in the user's language.",
 "chemistry": "You are a careful chemistry tutor. Explain concepts and balance equations step by step. Reply in the user's language."
}
def db():
 c=sqlite3.connect(DATABASE_PATH, timeout=10)
 c.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, event TEXT NOT NULL, detail TEXT, created_at TEXT NOT NULL)')
 c.commit(); return c
def log_event(event, detail=''):
 try:
  with db() as c: c.execute('INSERT INTO events(event,detail,created_at) VALUES(?,?,?)',(event,str(detail)[:100],datetime.now(timezone.utc).isoformat()))
 except Exception as e: app.logger.warning('analytics logging failed: %s',e)
def telegram(message):
 if not TELEGRAM_BOT_TOKEN or not TELEGRAM_ADMIN_CHAT_ID: return
 try: requests.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',json={'chat_id':TELEGRAM_ADMIN_CHAT_ID,'text':message},timeout=8)
 except requests.RequestException as e: app.logger.warning('Telegram notification failed: %s',e)
@app.route('/manifest.webmanifest')
def manifest():
 return send_from_directory('static','manifest.webmanifest',mimetype='application/manifest+json')
@app.route('/service-worker.js')
def service_worker():
 response=send_from_directory('static','service-worker.js',mimetype='application/javascript')
 response.headers['Service-Worker-Allowed'] = '/'
 response.headers['Cache-Control'] = 'no-cache'
 return response
@app.route('/')
def home():
 log_event('visit','home'); telegram('🌐 بازدید جدید از TEAM 810 SCIENCE\nزمان: '+datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')); return send_from_directory('static','index.html')
@app.route('/api/event',methods=['POST'])
def event():
 d=request.get_json(silent=True) or {}; name=d.get('event','interaction')
 if name not in ('language_selected','feature_open','ad_click'): name='interaction'
 log_event(name,d.get('detail','')); return jsonify(ok=True)
@app.route('/api/solve',methods=['POST'])
def solve():
 d=request.get_json(silent=True) or {}; sub=d.get('subject','math'); q=(d.get('question') or '').strip()
 if sub not in PROMPTS:return jsonify(error='بخش انتخاب‌شده معتبر نیست.'),400
 if not q:return jsonify(error='لطفاً سوال خود را بنویسید.'),400
 if not OPENAI_API_KEY.strip() or OPENAI_API_KEY == 'PASTE_YOUR_OPENAI_API_KEY_HERE':return jsonify(error='متغیر محیطی OPENAI_API_KEY را در تنظیمات هاست وارد کنید.'),503
 log_event('ai_question',sub)
 telegram('📚 TEAM 810 SCIENCE\nدرخواست هوش مصنوعی: '+sub+'\nزمان: '+datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))
 try:
  r=requests.post('https://api.openai.com/v1/chat/completions',headers={'Authorization':'Bearer '+OPENAI_API_KEY.strip(),'Content-Type':'application/json'},json={'model':OPENAI_MODEL,'messages':[{'role':'system','content':PROMPTS[sub]},{'role':'user','content':q}],'temperature':0.2},timeout=90)
  if r.status_code>=400:return jsonify(error='خطای API؛ کلید، اعتبار حساب و نام مدل را بررسی کنید.'),502
  return jsonify(answer=r.json().get('choices',[{}])[0].get('message',{}).get('content','پاسخی دریافت نشد.'))
 except requests.RequestException:return jsonify(error='ارتباط با سرویس هوش مصنوعی برقرار نشد.'),502
@app.route('/owner-stats')
def owner_stats():
 supplied=request.headers.get('X-Admin-Password','') or request.args.get('key','')
 if not ADMIN_PASSWORD or not hmac.compare_digest(supplied,ADMIN_PASSWORD): return Response('Not found',status=404)
 with db() as c:
  total=c.execute("SELECT COUNT(*) FROM events WHERE event='visit'").fetchone()[0]
  today=c.execute("SELECT COUNT(*) FROM events WHERE event='visit' AND substr(created_at,1,10)=?",(datetime.now(timezone.utc).date().isoformat(),)).fetchone()[0]
  ai=c.execute("SELECT COUNT(*) FROM events WHERE event='ai_question'").fetchone()[0]
  recent=c.execute('SELECT event,detail,created_at FROM events ORDER BY id DESC LIMIT 30').fetchall()
 rows=''.join('<tr><td>'+html.escape(str(a))+'</td><td>'+html.escape(str(b))+'</td><td>'+html.escape(str(c))+'</td></tr>' for a,b,c in recent)
 page='''<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>گزارش خصوصی TEAM 810</title><style>body{font-family:Tahoma;background:#08131b;color:#f5f5f5;padding:20px}.box{display:inline-block;background:#12382b;border:1px solid #2a8b5d;border-radius:12px;padding:18px;margin:6px}table{width:100%;border-collapse:collapse;margin-top:20px}td,th{border:1px solid #345;padding:8px;text-align:right}h1{color:#5cda91}</style><h1>گزارش خصوصی TEAM 810 SCIENCE</h1><div class="box">بازدید کل: <b>'''+str(total)+'''</b></div><div class="box">بازدید امروز UTC: <b>'''+str(today)+'''</b></div><div class="box">درخواست‌های هوش مصنوعی: <b>'''+str(ai)+'''</b></div><p>این آمار تعداد بازدید صفحه است و لزوماً تعداد افراد یکتا نیست.</p><table><tr><th>رویداد</th><th>جزئیات</th><th>زمان UTC</th></tr>'''+rows+'''</table></html>'''
 return Response(page,mimetype='text/html')
if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT','5000')))
