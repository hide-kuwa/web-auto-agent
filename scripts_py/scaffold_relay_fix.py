import json
import pathlib

root = pathlib.Path(".agent/relay")
root.mkdir(parents=True, exist_ok=True)
selectors = {
    "gemini": {
        "input": "[contenteditable='true'][aria-label*='相談' i], [contenteditable='true'][aria-label*='message' i], div[role='textbox'], textarea",
        "send": "button[aria-label*='送信' i], button[aria-label*='send' i]",
        "last_msg": "[data-message], article [data-md]",
    },
    "chapi": {
        "input": "textarea, div[role='textbox'], [contenteditable='true']",
        "send": "button[data-testid='send-button'], button[aria-label*='送信' i], button[aria-label*='send' i]",
        "last_msg": "[data-message-author-role]",
    },
}
config = {
    "gemini_url": "https://gemini.google.com/app",
    "chapi_url": "https://chat.openai.com/",
    "poll_ms": 1500,
    "rounds": -1,
}
policy = {"allowed_prefixes": ["#relay"], "loop_marker": "⟲", "approve_mode": "risky"}
(root / "selectors.json").write_text(
    json.dumps(selectors, ensure_ascii=False, indent=2), encoding="utf-8"
)
(root / "config.json").write_text(
    json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
)
(root / "policy.json").write_text(
    json.dumps(policy, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("OK: relay files written")
