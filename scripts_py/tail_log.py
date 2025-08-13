import time, pathlib, sys, json
p = pathlib.Path('.agent/relay/log.jsonl')
pos = 0
while True:
    if p.exists():
        with p.open('r', encoding='utf-8') as f:
            f.seek(pos)
            for line in f:
                try:
                    o=json.loads(line.strip())
                    print(o.get('from','skip'), '→', o.get('to',''), '|', (o.get('text','')[:120]).replace('\n',' '))
                except: print(line.strip())
            pos=f.tell()
    time.sleep(1)
