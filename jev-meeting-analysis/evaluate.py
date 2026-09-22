"""Score the pipeline against hand-labelled answer keys.

Usage:
    python3 evaluate.py [meeting ...]      # default: every data/<m>.txt that has data/gold_<m>.json

Answer keys follow label_spec.md: {"field": {"label": ..., "evidence": ..., "certainty": "high|medium|low"}}.
Yes/no answers are correct on the right side of 0.5, scores when rounded to the gold level, choices on exact match.
"""
import concurrent.futures as cf
import glob
import json
import os
import sys

from analyze import HERE, analyze

DATA = os.path.join(HERE, "data")


def load_meta(m):
    p = os.path.join(DATA, f"{m}.meta.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def main():
    ms = sys.argv[1:] or sorted(os.path.basename(p)[5:-5] for p in glob.glob(os.path.join(DATA, "gold_*.json")))
    with cf.ThreadPoolExecutor(8) as ex:
        runs = dict(zip(ms, ex.map(lambda m: analyze(open(os.path.join(DATA, f"{m}.txt")).read(), load_meta(m)), ms)))
    total = correct = auto = auto_ok = 0
    by_cert, misses = {}, []
    for m in ms:
        gold = json.load(open(os.path.join(DATA, f"gold_{m}.json")))
        for k, a in runs[m]["answers"].items():
            g = gold[k]["label"]
            hit = (bool(a["answer"]) == g) if isinstance(g, bool) else (a["answer"] == g)
            total += 1
            correct += hit
            c = by_cert.setdefault(gold[k].get("certainty", "?"), [0, 0])
            c[0] += 1
            c[1] += hit
            if not a["review"]:
                auto += 1
                auto_ok += hit
            if not hit:
                misses.append(f"  MISS {m:18} {k:24} jev={a['answer']} ({a['value']:.2f}) gold={g} ({gold[k].get('certainty')})")
    print(f"accuracy {correct}/{total} = {100 * correct / total:.1f}%")
    print("by answer-key certainty:", {k: f"{v[1]}/{v[0]}" for k, v in by_cert.items()})
    print(f"auto-decided {auto}/{total} ({100 * auto / total:.0f}%), accuracy on those {100 * auto_ok / max(auto, 1):.1f}%")
    print("tokens:", {m: runs[m]["input_tokens"] for m in ms})
    print("\n".join(misses))


if __name__ == "__main__":
    main()
