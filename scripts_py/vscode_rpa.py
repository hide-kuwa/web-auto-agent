import os, sys, time, json, argparse, subprocess, shutil, pathlib, ctypes
import uiautomation as uia
import pyperclip

WIN=None
VSCODE_HWND=None
VSCODE_PID=None
GUARD=True

def find_code_launcher():
    exe_candidates = [
        r'%LocalAppData%\Programs\Microsoft VS Code\Code.exe',
        r'C:\Program Files\Microsoft VS Code\Code.exe',
        r'C:\Program Files (x86)\Microsoft VS Code\Code.exe'
    ]
    for p in exe_candidates:
        p = os.path.expandvars(p)
        if os.path.exists(p):
            return ('exe', p)
    try:
        r = subprocess.run(['where','code'], capture_output=True, text=True)
        if r.returncode == 0:
            path = r.stdout.strip().splitlines()[0]
            ext = os.path.splitext(path)[1].lower()
            if ext in ('.cmd', '.bat'):
                return ('cmd', path)
            return ('exe', path)
    except:
        pass
    raise RuntimeError('VS Code launcher not found')

def start_code(folder):
    kind, path = find_code_launcher()
    folder = os.path.abspath(folder)
    if kind == 'exe':
        args = [path, '--disable-workspace-trust', folder]
        subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        comspec = os.environ.get('ComSpec', r'C:\Windows\System32\cmd.exe')
        cmdline = f'"{path}" --disable-workspace-trust "{folder}"'
        subprocess.Popen([comspec, '/c', cmdline], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return wait_window()

def wait_window(timeout=30):
    t0 = time.time()
    while time.time() - t0 < timeout:
        for w in uia.GetRootControl().GetChildren():
            if 'Visual Studio Code' in (w.Name or ''):
                return w
        time.sleep(0.4)
    raise RuntimeError('VS Code window not found')

def focus(win):
    try:
        win.SetActive()
    except:
        try: win.SwitchToThisWindow()
        except: pass
    time.sleep(0.2)

def is_vscode_foreground():
    if not (VSCODE_PID and VSCODE_HWND): return False
    try:
        c = uia.GetFocusedControl()
        pid = getattr(c, 'ProcessId', None)
        return pid == VSCODE_PID
    except:
        return False

def ensure_foreground():
    if not GUARD: return
    while not is_vscode_foreground():
        focus(WIN)
        time.sleep(0.25)

def send_keys(s):
    ensure_foreground()
    uia.SendKeys(s, waitTime=0)

def type_text(s):
    ensure_foreground()
    pyperclip.copy(s)
    uia.SendKeys('^v', waitTime=0)

def command_palette(cmd):
    send_keys('^+p'); time.sleep(0.35)
    type_text(cmd); time.sleep(0.25)
    send_keys('{Enter}'); time.sleep(0.6)

def new_untitled():
    send_keys('^n'); time.sleep(0.35)

def save_as(path):
    send_keys('^s'); time.sleep(0.7)
    type_text(path); time.sleep(0.3)
    send_keys('{Enter}'); time.sleep(0.7)

def write_file(path, text):
    new_untitled()
    type_text(text)
    save_as(path)

def append_file(path, text):
    command_palette('File: Open File'); time.sleep(0.7)
    type_text(path); time.sleep(0.25)
    send_keys('{Enter}'); time.sleep(0.9)
    send_keys('^{End}'); time.sleep(0.15)
    type_text(text)
    send_keys('^s'); time.sleep(0.35)

def ensure_terminal():
    command_palette('Terminal: Create New Terminal'); time.sleep(0.9)

def run_in_terminal(cmd):
    ensure_terminal()
    type_text(cmd)
    send_keys('{Enter}')
    time.sleep(0.9)

def git_commit_push(msg):
    ensure_terminal()
    for c in ['git add -A', f'git commit -m "{msg}"', 'git push -u origin HEAD']:
        type_text(c); send_keys('{Enter}'); time.sleep(1.3)

def main():
    global WIN, VSCODE_HWND, VSCODE_PID, GUARD
    ap = argparse.ArgumentParser()
    ap.add_argument('--folder', required=True)
    ap.add_argument('--plan', default=None)
    ap.add_argument('--fresh', action='store_true')
    ap.add_argument('--guard', choices=['strict','off'], default='strict')
    a = ap.parse_args()
    GUARD = (a.guard=='strict')

    folder = str(pathlib.Path(a.folder).resolve())
    if a.fresh:
        try: shutil.rmtree(os.path.join(os.getenv('TEMP','.'),'vscode-rpa-cache'))
        except: pass

    WIN = start_code(folder)
    VSCODE_HWND = WIN.NativeWindowHandle
    VSCODE_PID = WIN.ProcessId
    focus(WIN)

    actions = []
    if a.plan:
        actions = json.loads(pathlib.Path(a.plan).read_text(encoding='utf-8-sig'))['actions']
    else:
        actions = [
            {"type":"write_file","path":str(pathlib.Path(folder,'RPA_OK.txt')),"text":"RPA OK\n"},
            {"type":"run","shell":"git status"}
        ]

    for act in actions:
        t = act.get('type')
        if t == 'write_file':
            write_file(act['path'], act.get('text',''))
        elif t == 'append':
            append_file(act['path'], act.get('text',''))
        elif t == 'run':
            run_in_terminal(act['shell'])
        elif t == 'git':
            git_commit_push(act.get('message','chore: automated commit'))
        elif t == 'sleep':
            time.sleep(float(act.get('sec',1.0)))

    print('DONE')

if __name__ == '__main__':
    main()

