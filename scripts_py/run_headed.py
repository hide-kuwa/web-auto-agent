import json
import pathlib
from playwright.sync_api import sync_playwright

spec_path = pathlib.Path(".agent/tests/home.json")
out_dir = pathlib.Path(".agent/artifacts")
out_dir.mkdir(parents=True, exist_ok=True)
spec = json.loads(spec_path.read_text(encoding="utf-8"))


def run():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(pathlib.Path(".agent/user-data").resolve()),
            headless=False,
            viewport={
                "width": spec["viewport"]["width"],
                "height": spec["viewport"]["height"],
            },
            record_video_dir=str((out_dir / "videos").resolve()),
        )
        page = ctx.new_page()
        page.goto(spec["start"], wait_until="domcontentloaded")
        for a in spec["actions"]:
            t = a["type"]
            if t == "visit":
                page.goto(spec["start"] + a["url"], wait_until="domcontentloaded")
            elif t == "click":
                page.wait_for_selector(a["selector"], state="visible")
                page.click(a["selector"])
            elif t == "fill":
                page.wait_for_selector(a["selector"], state="visible")
                page.fill(a["selector"], a.get("value", ""))
            elif t == "press":
                page.keyboard.press(a["key"])
            elif t == "waitFor":
                page.wait_for_timeout(a.get("ms", 500))
            elif t == "assertText":
                page.wait_for_selector(a["selector"], state="visible")
                txt = page.text_content(a["selector"])
                if (txt or "").strip() != a["equals"]:
                    raise RuntimeError(f"assertText failed: {a['selector']}")
            elif t == "screenshot":
                page.screenshot(
                    path=str(out_dir / f"{a.get('name','shot')}.png"), full_page=True
                )
        print("OK: headed test finished. Artifacts in .agent/artifacts")
        ctx.close()


if __name__ == "__main__":
    run()
