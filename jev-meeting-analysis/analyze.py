"""Analyse a meeting transcript with TypeSafe Jev (via the Composio CLI).

Usage:
    python3 analyze.py data/<meeting>.txt [data/<meeting>.meta.json] [--json]

Transcript format: first line "Meeting: <title> (<date>)", then one line per sentence
"[mm:ss] Speaker Name: text". Optional meta JSON: {"date", "organiser", "attendees", "focus_person"}.

Pipeline (the configuration that scored best in evaluation, see README):
  1. Compress: merge consecutive lines from the same speaker (~30% fewer tokens, same accuracy).
  2. Structured state: meeting, date, focus person, organiser, attendees, speaker line shares.
  3. Long meetings (> LONG_TOKENS): split into WINDOW_TOKENS windows, one call per window in
     parallel, combined in code (any-window-yes for yes/no, mean interaction, max deadline risk).
  4. Answers within REVIEW_BAND of 0.5 are flagged "review" instead of being decided.
"""
import collections
import concurrent.futures as cf
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
QUESTIONS = json.load(open(os.path.join(HERE, "questions", "meeting_questions.json")))
MODEL = os.environ.get("JEV_MODEL", "jev-latest")
LONG_TOKENS = 20000
WINDOW_TOKENS = 16000
REVIEW_BAND = 0.1
MAX_OVER_WINDOWS = {"deadline_risk"}  # score fields combined with max; others use mean


def parse(text):
    lines = text.splitlines()
    rows = []
    for line in lines[1:]:
        m = re.match(r"\[([\d:]+)\] ([^:]+): (.*)", line)
        if m:
            rows.append((m.group(1), m.group(2).strip(), m.group(3)))
    return lines[0], rows


def compress(rows):
    out, prev = [], None
    for t, speaker, text in rows:
        if speaker == prev:
            out[-1] += " " + text
        else:
            out.append(f"[{t}] {speaker}: {text}")
            prev = speaker
    return out


def speaker_stats(rows):
    counts = collections.Counter(s for _, s, _ in rows)
    total = sum(counts.values()) or 1
    return {k: f"{round(100 * v / total)}% of lines" for k, v in counts.most_common()}


def build_states(text, meta):
    title, rows = parse(text)
    date = meta.get("date") or (re.search(r"\((\d{4}-\d{2}-\d{2})\)", title) or [None, None])[1]
    base = {
        "meeting": title,
        "meeting_date": date,
        "focus_person": meta.get("focus_person", "Nayem Reza"),
        "organiser": meta.get("organiser"),
        "attendees": meta.get("attendees"),
        "speaker_stats": speaker_stats(rows),
    }
    lines = compress(rows)
    if sum(len(l) for l in lines) // 4 <= LONG_TOKENS:
        return [dict(base, transcript="\n".join(lines))]
    windows, cur, n = [], [], 0
    for line in lines:
        cur.append(line)
        n += len(line) // 4
        if n >= WINDOW_TOKENS:
            windows.append(cur)
            cur, n = [], 0
    if cur:
        windows.append(cur)
    return [dict(base, transcript="\n".join(w), window=f"part {i + 1} of {len(windows)} of the meeting")
            for i, w in enumerate(windows)]


def call_jev(state, questions=QUESTIONS, model=MODEL):
    req = {"model": model, "state": state, "questions": questions}
    env = dict(os.environ, PATH=os.path.expanduser("~/.local/bin") + ":" + os.environ.get("PATH", ""))
    r = subprocess.run(["composio", "execute", "JEV_EVALUATE_STATE", "-d", json.dumps(req)],
                       capture_output=True, text=True, env=env, timeout=300)
    d = json.loads(r.stdout)
    if not d.get("successful"):
        raise RuntimeError(r.stdout[:600])
    return d["data"]


def combine(results, questions=QUESTIONS):
    """Merge per-window answers into one answer per question."""
    out = {}
    for k, q in questions.items():
        xs = [r["answers"][k] for r in results]
        if q["type"] == "noul":
            v = max(x["noul"] for x in xs)
            out[k] = {"type": "noul", "value": v, "answer": v >= 0.5,
                      "review": abs(v - 0.5) < REVIEW_BAND}
        elif q["type"] == "score":
            v = (max if k in MAX_OVER_WINDOWS else lambda s: sum(s) / len(s))([x["score"] for x in xs])
            out[k] = {"type": "score", "value": v, "answer": int(round(v)),
                      "review": abs(v - round(v)) > 0.5 - REVIEW_BAND,
                      "level": q["criteria"][int(round(v))]}
        else:
            probs = collections.Counter()
            for x in xs:
                for opt, p in x["probabilities"].items():
                    probs[opt] += p / len(xs)
            best, p = probs.most_common(1)[0]
            out[k] = {"type": "choice", "value": round(p, 2), "answer": best, "review": p < 0.6}
    return out


def analyze(text, meta=None, questions=QUESTIONS, model=MODEL):
    states = build_states(text, meta or {})
    with cf.ThreadPoolExecutor(8) as ex:
        results = list(ex.map(lambda s: call_jev(s, questions, model), states))
    return {"windows": len(states),
            "input_tokens": sum(r["usage"]["input_tokens"] for r in results),
            "model": results[0]["model"],
            "answers": combine(results, questions),
            "raw": results}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    text = open(args[0]).read()
    meta = json.load(open(args[1])) if len(args) > 1 else {}
    res = analyze(text, meta)
    if "--json" in sys.argv:
        print(json.dumps({k: v for k, v in res.items() if k != "raw"}, indent=1))
        return
    print(f"{text.splitlines()[0]}  |  windows={res['windows']} tokens={res['input_tokens']} model={res['model']}")
    for k, a in res["answers"].items():
        flag = "  <- review" if a["review"] else ""
        shown = f"{a['answer']} ({a['value']:.2f})" if a["type"] != "score" else f"{a['answer']} ({a['value']:.2f}) {a['level']}"
        print(f"  {k:24} {shown}{flag}")


if __name__ == "__main__":
    main()
