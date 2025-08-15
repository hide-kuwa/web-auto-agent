import json
import pathlib
import shutil
from PIL import Image, ImageChops
import numpy as np

spec = json.loads(
    pathlib.Path(".agent/tests/home.json").read_text(encoding="utf-8-sig")
)
shots = spec.get("screenshots", [])
art = pathlib.Path(".agent/artifacts")
base = pathlib.Path(".agent/baseline")
base.mkdir(parents=True, exist_ok=True)
diff = pathlib.Path(".agent/diff")
diff.mkdir(parents=True, exist_ok=True)
report = []
threshold = 0.01


def load(p):
    img = Image.open(p).convert("RGBA")
    return img


def compare(a, b):
    if a.size != b.size:
        b = b.resize(a.size)
    d = ImageChops.difference(a, b)
    arr = np.asarray(d)
    changed = np.count_nonzero(arr)
    total = arr.size
    ratio = changed / total
    return d, ratio


for name in shots:
    cur = art / f"{name}.png"
    if not cur.exists():
        continue
    base_img = base / f"{name}.png"
    if not base_img.exists():
        shutil.copyfile(cur, base_img)
        report.append((name, "initialized", 0.0))
    else:
        a = load(cur)
        b = load(base_img)
        d, r = compare(a, b)
        out = diff / f"{name}.png"
        d.save(out)
        status = "pass" if r < threshold else "fail"
        report.append((name, status, r))

md_lines = []
md_lines.append("| Screenshot | Status | Diff Ratio |")
md_lines.append("|---|---|---|")
for n, s, r in report:
    md_lines.append(f"| {n}.png | {s} | {r:.4%} |")
pathlib.Path("ci_report.md").write_text("\n".join(md_lines), encoding="utf-8")
print("Wrote ci_report.md")
