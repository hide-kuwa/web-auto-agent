import json, pathlib, textwrap
from playwright.sync_api import sync_playwright

root=pathlib.Path('.agent/relay')
cfg=json.loads((root/'config.json').read_text(encoding='utf-8-sig'))
sel=json.loads((root/'selectors.json').read_text(encoding='utf-8-sig'))

def cnt(page, css):
    try: return page.locator(css).count()
    except: return -1

def sample(page, css):
    try:
        loc=page.locator(css)
        n=loc.count()
        if n<=0: return '(none)'
        t=loc.nth(n-1).inner_text() or ''
        return textwrap.shorten(' '.join(t.split()), width=120)
    except Exception as e:
        return f'(error: {e})'

with sync_playwright() as p:
    ctx=p.chromium.launch_persistent_context(str(pathlib.Path('.agent/user-data').resolve()), headless=False, channel='msedge')
    g=ctx.new_page(); g.goto(cfg['gemini_url'])
    c=ctx.new_page(); c.goto(cfg['chapi_url'])
    input("各タブにログイン/会話画面を開いたら Enter：")
    print('--- GEMINI ---')
    print(' input:',cnt(g,sel['gemini']['input']))
    print('  send:',cnt(g,sel['gemini']['send']))
    print('  last:',cnt(g,sel['gemini']['last_msg']), '| sample:', sample(g,sel['gemini']['last_msg']))
    print('--- CHAPI ---')
    print(' input:',cnt(c,sel['chapi']['input']))
    print('  send:',cnt(c,sel['chapi']['send']))
    print('  last:',cnt(c,sel['chapi']['last_msg']), '| sample:', sample(c,sel['chapi']['last_msg']))
    input("結果をメモしたら Enter で終了")
    ctx.close()
