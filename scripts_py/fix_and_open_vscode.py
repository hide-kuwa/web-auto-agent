# scripts_py/fix_and_open_vscode.py
# -*- coding: utf-8 -*-
import os
import sys
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(cmd, check=False, capture=False):
    print(f"$ {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=ROOT, text=True,
                         stdout=subprocess.PIPE if capture else None,
                         stderr=subprocess.STDOUT if capture else None)
    if check and res.returncode != 0:
        print(res.stdout or "")
        raise SystemExit(res.returncode)
    return res

def has_staged_changes() -> bool:
    return subprocess.run("git diff --cached --quiet", shell=True, cwd=ROOT).returncode != 0

def has_worktree_changes() -> bool:
    return subprocess.run("git diff --quiet", shell=True, cwd=ROOT).returncode != 0

def ensure_precommit():
    run("pre-commit --version", check=False)

def precommit_loop(max_iter=3):
    for i in range(max_iter):
        r = run("pre-commit run --all-files", capture=True)
        print(r.stdout or "")
        # hookがファイルを書き換えたらステージ→コミット（no-verifyで無限ループ回避）
        run("git add -A")
        if has_staged_changes():
            run('git commit -m "style: pre-commit auto-fix" --no-verify')
        # もう直すものがなければ抜ける
        if "files were modified by this hook" not in (r.stdout or ""):
            break

def auto_fix_linters():
    # 追加で安全な自動修正（idempotent）
    run("ruff --fix .", check=False)
    run("black .", check=False)
    run("git add -A")
    if has_staged_changes():
        run('git commit -m "style: ruff/black auto-fix" --no-verify')

def run_tests(strict=True) -> bool:
    args = "--headless --strict" if strict else ""
    r = run(f"python scripts_py/auto_runner.py {args}", capture=True)
    print(r.stdout or "")
    return "[ok] all steps passed" in (r.stdout or "")

def last_changed_files(n=1):
    r = run(f"git diff --name-only HEAD~{n}..HEAD", capture=True)
    files = [ln.strip() for ln in (r.stdout or "").splitlines() if ln.strip()]
    return files

def open_in_vscode(files):
    # 既に開いているウィンドウを再利用
    run("code -r .")
    for f in files:
        # 変更ファイルをまとめて開く
        run(f'code -r -g "{f}"')

def main():
    ensure_precommit()
    precommit_loop()
    auto_fix_linters()

    ok = run_tests(strict=True)
    if ok:
        # テストが通ったらコミットしてpush
        run('git add -A')
        if has_staged_changes() or has_worktree_changes():
            run('git commit -m "ci: green after autofix" --no-verify')
        run("git push", check=False)
        print("\n✅ done: tests green. VS Codeを開きます。")
        # 直近コミットの変更ファイルを開く（なければワークスペースのみ）
        files = last_changed_files(1) or []
        open_in_vscode(files)
        sys.exit(0)
    else:
        print("\n❌ tests failed: 手当が必要。変更点をVS Codeで開きます。")
        # 失敗時はワークツリーの変更＆直近差分を開く
        run("git add -N .")  # 変更検知のためのno-op
        files = last_changed_files(1) or []
        if not files:
            # ダーティなファイル一覧
            r = run('git status --porcelain', capture=True)
            files = [ln.split()[-1] for ln in (r.stdout or "").splitlines() if ln.strip()]
        open_in_vscode(files)
        sys.exit(1)

if __name__ == "__main__":
    main()
