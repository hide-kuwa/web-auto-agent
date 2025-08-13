import json, subprocess, os, sys, shlex, pathlib
from colorama import Fore, Style, init
init(autoreset=True)
pol=json.loads(pathlib.Path('.agent/policies.json').read_text(encoding='utf-8-sig'))
chg=json.loads(pathlib.Path('.agent/changes/pending.json').read_text(encoding='utf-8-sig'))
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
        ans=input(Fore.CYAN+f"HOLD (not in allow): {c}\nApprove this command? [y/N] ").strip().lower()
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

