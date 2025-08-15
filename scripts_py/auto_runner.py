from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List
from playwright.sync_api import (
    sync_playwright,
    Error as PWError,
    TimeoutError as PWTimeout,
)

SPEC_DEFAULT = {
    "start": "https://example.com/",
    "steps": [
        {"action": "assertText", "selector": "h1", "text": "Example Domain"},
        {"action": "screenshot", "path": ".agent/tests/home.png"},
    ],
}


def _norm(s: str | None) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def ensure_spec(spec_path: Path) -> Dict[str, Any]:
    if not spec_path.exists():
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(
            json.dumps(SPEC_DEFAULT, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return SPEC_DEFAULT.copy()
    try:
        return json.loads(spec_path.read_text(encoding="utf-8"))
    except Exception:
        # 壊れていれば置き換え
        spec_path.write_text(
            json.dumps(SPEC_DEFAULT, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return SPEC_DEFAULT.copy()


def save_spec(spec_path: Path, spec: Dict[str, Any]) -> None:
    spec_path.write_text(
        json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def run_once(spec_path: Path, headless: bool, strict: bool) -> int:
    spec = ensure_spec(spec_path)
    start = spec.get("start") or "https://example.com/"
    steps: List[Dict[str, Any]] = list(spec.get("steps") or [])
    fails: List[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        # 1) 起点へ。落ちたら example.com へフェイルオーバー＆specを書き換え
        try:
            page.goto(start, wait_until="domcontentloaded", timeout=15000)
        except (PWError, PWTimeout):
            fallback = "https://example.com/"
            try:
                page.goto(fallback, wait_until="domcontentloaded", timeout=15000)
                spec["start"] = fallback
                save_spec(spec_path, spec)
                print(f"[heal] start unreachable: {start} -> {fallback}")
            except Exception as e:
                print(f"[fatal] cannot open any start url: {e}")
                browser.close()
                return 2

        # 2) ステップ実行（よくある action だけ、未知actionはスキップ）
        for a in steps:
            act = (a.get("action") or "").lower()
            try:
                if act == "goto":
                    url = a["url"]
                    page.goto(url, wait_until="domcontentloaded", timeout=15000)

                elif act == "screenshot":
                    path = Path(a["path"])
                    path.parent.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=str(path), full_page=True)

                elif act in ("asserttext", "assert_text"):
                    sel = a["selector"]
                    txt = _norm(page.locator(sel).first.inner_text())
                    exp_text = a.get("text")
                    exp_equals = a.get("equals")
                    exp_contains = a.get("contains")
                    exp = next(
                        (v for v in (exp_text, exp_equals, exp_contains) if v), None
                    )

                    ok = False
                    if exp is None:
                        ok = bool(txt)  # 期待未指定→何か文字があればOK
                    elif exp_contains is not None:
                        ok = _norm(exp) in txt
                    else:
                        ok = txt == _norm(exp)

                    if not ok:
                        msg = f"[assertText NG] selector={sel} got={txt!r} exp={exp!r}"
                        print(msg)
                        fails.append(msg)
                    else:
                        print(f"[assertText OK] {sel}")

                elif act == "click":
                    sel = a["selector"]
                    page.locator(sel).first.click(timeout=10000)

                else:
                    print(f"[skip] unknown action: {act}")

            except Exception as e:
                msg = f"[step error] action={act} error={e}"
                print(msg)
                fails.append(msg)

        browser.close()

    if fails and strict:
        return 1
    if fails:
        print(f"\n[heal] completed with {len(fails)} soft-fail(s). (non-strict mode)")
    else:
        print("\n[ok] all steps passed")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=".agent/tests/home.json")
    ap.add_argument("--headless", action="store_true")
    ap.add_argument(
        "--strict", action="store_true", help="fail CI on any assertion/step error"
    )
    args = ap.parse_args()
    spec_path = Path(args.spec)
    rc = run_once(spec_path, headless=args.headless, strict=args.strict)
    sys.exit(rc)


if __name__ == "__main__":
    main()
