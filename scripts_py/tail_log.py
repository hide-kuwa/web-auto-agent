# -*- coding: utf-8 -*-
import json
import sys
import time


def main(path: str):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            try:
                o = json.loads(line)
                print(
                    o.get("from", "-"),
                    "->",
                    o.get("to", "-"),
                    "|",
                    (o.get("text", "")[:120]).replace("\n", " "),
                )
            except Exception:
                print(line.rstrip())


if __name__ == "__main__":
    log = sys.argv[1] if len(sys.argv) > 1 else ".agent/log.txt"
    main(log)
