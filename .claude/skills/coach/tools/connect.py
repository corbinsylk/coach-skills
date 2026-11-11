"""Connect Gemini: opens a small page in the coach's browser where they paste their Google AI Studio key. The key goes from
that page straight into a private file on their computer; it is never shown in the chat or printed here.

usage: connect.py          (opens the page, waits until they save, prints CONNECTED or a reason)
       connect.py --status (prints CONNECTED or NOT CONNECTED, nothing else)"""
import http.server, json, sys, threading, webbrowser
from gemini import load_key, save_key, test_key

if "--status" in sys.argv:
    k = load_key()
    print("CONNECTED" if k and test_key(k)[0] else "NOT CONNECTED"); sys.exit()

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Connect Gemini</title><style>
body{margin:0;background:#F4F2EE;font:16px/1.5 -apple-system,'Segoe UI',sans-serif;color:#121417;display:flex;justify-content:center}
.c{max-width:560px;margin:60px 20px;background:#fff;border-radius:24px;padding:36px 40px;box-shadow:0 20px 50px rgba(0,0,0,.08)}
h1{font-size:28px;margin:0 0 6px;letter-spacing:-.02em}p{color:#5B636B;margin:0 0 18px}ol{padding-left:20px;margin:0 0 22px}li{margin:8px 0}
a.b{display:inline-block;background:#121417;color:#fff;text-decoration:none;padding:10px 16px;border-radius:12px;font-weight:600}
input{width:100%;box-sizing:border-box;padding:14px;border:1.5px solid #D9D5CA;border-radius:12px;font-size:16px;margin:6px 0 14px}
button{width:100%;padding:14px;border:0;border-radius:12px;background:#16A34A;color:#fff;font-size:16px;font-weight:700;cursor:pointer}
#m{margin-top:14px;font-weight:600;min-height:24px}.ok{color:#16A34A}.no{color:#DC2626}small{color:#8A9099}</style></head><body><div class="c">
<h1>Connect Gemini</h1><p>Your coach skills use Google's Gemini to draw new muscles and food photos. It takes two minutes, once.</p>
<ol><li><a class="b" href="https://aistudio.google.com/apikey" target="_blank">Open Google AI Studio</a> and sign in with your Google account.</li>
<li>Click <b>Create API key</b>, then copy it.</li>
<li>Paste it below and click Save.</li></ol>
<input id="k" type="password" placeholder="Paste your key here" autocomplete="off">
<button onclick="save()">Save</button><div id="m"></div>
<p style="margin-top:18px"><small>The key stays on this computer. Images cost about 4 cents each on Google's side; if Google asks, turn on billing in AI Studio.</small></p>
</div><script>
async function save(){const m=document.getElementById('m');m.className='';m.textContent='Checking...';
const r=await fetch('/save',{method:'POST',body:JSON.stringify({k:document.getElementById('k').value})});const d=await r.json();
m.className=d.ok?'ok':'no';m.textContent=d.ok?'Connected. You can close this tab and go back to Claude.':'Not saved: '+d.msg;}
</script></body></html>"""
result = {}


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers(); self.wfile.write(PAGE.encode())

    def do_POST(self):
        k = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}").get("k", "").strip()
        ok, msg = test_key(k) if k else (False, "paste the key first")
        if ok:
            save_key(k); result["ok"] = True
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(json.dumps({"ok": ok, "msg": msg}).encode())
        if ok: threading.Thread(target=self.server.shutdown).start()


srv = http.server.HTTPServer(("127.0.0.1", 0), H)
url = f"http://127.0.0.1:{srv.server_address[1]}/"
print(f"OPENED: {url} (waiting up to 15 minutes for the key)", flush=True)
webbrowser.open(url)
t = threading.Timer(900, srv.shutdown); t.start()
srv.serve_forever(); t.cancel()
print("CONNECTED" if result.get("ok") else "NOT CONNECTED: the page was closed or timed out. Run it again when ready.")
