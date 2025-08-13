import json, pathlib
root = pathlib.Path('.agent/relay'); root.mkdir(parents=True, exist_ok=True)
cfg = {
  "gemini_url": "https://gemini.google.com/app",
  "chapi_url": "https://chat.openai.com/",
  "poll_ms": 1500,
  "rounds": 5
}
sel = {
  "gemini": {
    "input": "textarea",
    "send": "button[aria-label='Send']",
    "last_msg": "[data-message]"
  },
  "chapi": {
    "input": "textarea",
    "send": "button[data-testid='send-button']",
    "last_msg": "[data-message-author-role]"
  }
}
(root/'config.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding='utf-8')
(root/'selectors.json').write_text(json.dumps(sel, ensure_ascii=False, indent=2), encoding='utf-8')
print('OK: relay config created.')
