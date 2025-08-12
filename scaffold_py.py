import pathlib, json, datetime, re, subprocess, webbrowser

def w(p, c):
    path = pathlib.Path(p)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(c, encoding="utf-8")

w("scripts_py/preview.py", """import http.server, socketserver, os, pathlib
PORT=5173
root=pathlib.Path('app').resolve()
os.chdir(root)
class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('','/'):
            self.path='/index.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
with socketserver.TCPServer(("",PORT),H) as httpd:
    print(f"Preview: http://localhost:{PORT}")
    httpd.serve_forever()
""")

w("scripts_py/run_headed.py", """import json, pathlib
from playwright.sync_api import sync_playwright
spec_path=pathlib.Path('.agent/tests/home.json')
out_dir=pathlib.Path('.agent/artifacts'); out_dir.mkdir(parents=True, exist_ok=True)
spec=json.loads(spec_path.read_text(encoding='utf-8'))
def run():
    with sync_playwright() as p:
        ctx=p.chromium.launch_persistent_context(user_data_dir=str(pathlib.Path('.agent/user-data').resolve()), headless=False, viewport={'width':spec['viewport']['width'],'height':spec['viewport']['height']}, record_video_dir=str((out_dir/'videos').resolve()))
        page=ctx.new_page()
        page.goto(spec['start'], wait_until='domcontentloaded')
        for a in spec['actions']:
            t=a['type']
            if t=='visit':
                page.goto(spec['start']+a['url'], wait_until='domcontentloaded')
            elif t=='click':
                page.wait_for_selector(a['selector'], state='visible'); page.click(a['selector'])
            elif t=='fill':
                page.wait_for_selector(a['selector'], state='visible'); page.fill(a['selector'], a.get('value',''))
            elif t=='press':
                page.keyboard.press(a['key'])
            elif t=='waitFor':
                page.wait_for_timeout(a.get('ms',500))
            elif t=='assertText':
                page.wait_for_selector(a['selector'], state='visible'); txt=page.text_content(a['selector'])
                if (txt or '').strip()!=a['equals']:
                    raise RuntimeError(f"assertText failed: {a['selector']}")
            elif t=='screenshot':
                page.screenshot(path=str(out_dir/f"{a.get('name','shot')}.png"), full_page=True)
        print("OK: headed test finished. Artifacts in .agent/artifacts")
        ctx.close()
if __name__=='__main__': run()
""")

w("scripts_py/safe_exec.py", """import json, subprocess, os, sys, shlex, pathlib
from colorama import Fore, Style, init
init(autoreset=True)
pol=json.loads(pathlib.Path('.agent/policies.json').read_text(encoding='utf-8'))
chg=json.loads(pathlib.Path('.agent/changes/pending.json').read_text(encoding='utf-8'))
allow=set(pol.get('allow',[])); deny=[x.lower() for x in pol.get('deny',[])]
timeout=int(pol.get('timeoutSec',120))
def denied(c):
    s=c.lower()
    return any(x in s for x in deny)
def allowed(c):
    first=shlex.split(c)[0] if c.strip() else ''
    return first in allow
print(f"Changeset: {chg['id']} :: {chg['summary']}")
print("Commands:")
for i,c in enumerate(chg.get('commands',[]),1): print(f"{i}. {c}")
for c in chg.get('commands',[]):
    if denied(c):
        print(Fore.YELLOW+f"SKIP (denied): {c}"); continue
    if not allowed(c):
        ans=input(Fore.CYAN+f"HOLD (not in allow): {c}\\nApprove this command? [y/N] ").strip().lower()
        if ans!='y': continue
    print(Fore.GREEN+f"EXEC: {c}")
    try:
        env=os.environ.copy(); env['HUSKY']='0'; env['CI']='1'
        subprocess.run(c, shell=True, check=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        print(Fore.RED+f"TIMEOUT: {c}"); sys.exit(1)
    except subprocess.CalledProcessError:
        print(Fore.RED+f"FAILED: {c}"); sys.exit(1)
print(Style.BRIGHT+"Done.")
""")

w("scripts_py/gitworker.py", """import subprocess, json, webbrowser, re, sys, pathlib, datetime
pend=json.loads(pathlib.Path('.agent/changes/pending.json').read_text(encoding='utf-8'))
def sh(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8',errors='ignore').strip()
def parse_remote(u):
    if u.startswith('git@'):
        m=re.search(r':(.+)/(.+)\\.git$',u); return m.group(1),m.group(2)
    if u.startswith('https://'):
        m=re.search(r'github\\.com/([^/]+)/([^/]+)\\.git$',u); return m.group(1),m.group(2)
    raise RuntimeError('unsupported remote url')
def now():
    return datetime.datetime.now().strftime('%Y%m%d-%H%M')
def slug(s):
    return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')[:24]
def main():
    try: sh('git rev-parse --is-inside-work-tree')
    except: print('not a git repo'); sys.exit(1)
    owner,repo=parse_remote(sh('git config --get remote.origin.url'))
    sh('git fetch --all')
    try: sh('git switch main')
    except: sh('git checkout -b main')
    try: sh('git pull --ff-only')
    except: pass
    branch=f"feature/{now()}-{slug(pend.get('summary','change'))}"
    try: sh(f'git checkout -b "{branch}"')
    except: sh(f'git switch "{branch}"')
    try:
        sh('git add -A')
        sh(f'git commit -m "{pend.get("summary","update")} [changeset:{pend.get("id","")}]\\\""')
    except: pass
    sh(f'git push -u origin "{branch}"')
    pr=f"https://github.com/{owner}/{repo}/compare/{branch}?expand=1"
    print('Open PR:', pr); webbrowser.open(pr)
if __name__=='__main__': main()
""")

print("OK: scripts_py generated.")
