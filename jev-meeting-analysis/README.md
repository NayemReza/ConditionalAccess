# JEV meeting analysis

Scores Fireflies meeting transcripts with TypeSafe **Jev** (called through the Composio CLI). One call per meeting, or one per window for long meetings, answers 15 typed questions about the meeting: what kind of meeting it was, decisions, owners, work for the focus person (Nayem Reza), blockers, deadline pressure, security, spend and vendors.

## Quick start

```bash
# one-off setup: Composio CLI with the Jev toolkit connected
curl -fsSL https://composio.dev/install | sh -s -- 0.4.1   # pin a version if GitHub API lookup is blocked
composio login

python3 analyze.py data/<meeting>.txt data/<meeting>.meta.json   # human-readable
python3 analyze.py data/<meeting>.txt --json                     # machine-readable
python3 evaluate.py                                              # accuracy vs answer keys in data/
```

- **Transcript format:** the first line is `Meeting: <title> (<YYYY-MM-DD>)`, then one line per sentence: `[mm:ss] Speaker Name: text`.
- **Optional `.meta.json`:** `{"date", "organiser", "attendees", "focus_person"}`.
- **`data/` is git-ignored.** Transcripts and answer keys contain verbatim meeting content and stay local.

## Files

| File | What it is |
|---|---|
| `analyze.py` | The pipeline: compress → structured state → window if long → Jev → combine → flag answers for review |
| `evaluate.py` | Scores the pipeline against answer keys (`data/gold_<meeting>.json`) |
| `questions/meeting_questions.json` | The final question set (v9) |
| `questions/history/` | Every question version tried (v2–v9) |
| `label_spec.md` | What each field is meant to mean; used to write the answer keys |
| `typesafe_docs_notes.md` | Notes from TypeSafe's Jev documentation on writing questions |

## How the pipeline works

1. **Compress the transcript.** Consecutive lines from the same speaker are merged. This uses about 30% fewer tokens with the same accuracy.
2. **Build a structured state.** Jev receives `meeting`, `meeting_date`, `focus_person`, `organiser`, `attendees`, `speaker_stats` (each speaker's share of lines) and `transcript`.
3. **Window long meetings.** Above about 20k tokens, the transcript is split into 16k-token windows, one call per window in parallel. Code combines the answers:
   - yes/no: yes if any window says yes
   - interaction: mean across windows
   - deadline risk: highest across windows
   - meeting type: probabilities averaged across windows
4. **Flag close calls for review.** Yes/no answers within 0.1 of 0.5, scores within 0.1 of the midpoint between two levels, and meeting-type answers below 0.6 probability are flagged `review` rather than decided.

## Results (September 2026, jev-1.13.0)

The answer keys were written by Claude subagents that read each full transcript. They have not been checked by a person yet.

- **Scope:** 8 meetings, 120 answers.
- **Overall:** **93–95%** across repeat runs. Answers that sit at about 0.5 can flip between runs.
- **By answer-key certainty:** 64–65 of 65 correct where the answer key was sure. Most misses are on labels the answer key itself marked low or medium certainty.
- **Review band:** about 88% of answers are decided automatically, with about 95% accuracy on those.
- **Cost:** 3k–33k input tokens per meeting at $0.042 per million tokens, which is under $0.002 per meeting.

What each change was worth:

| Change | Effect |
|---|---|
| Summary instead of the full transcript | Worse. The summaries inflate or omit things, for example team-time percentages turning into "budget" |
| Structured state (date, focus person, speaker shares) | Biggest single gain: 76% → 89% on the tuning set |
| Criteria that describe both the yes and no ends; score levels that describe situations | +5–8% |
| Compressed transcript | Same accuracy, 30% fewer tokens |
| 16k-token windows for long meetings | 80% → 93% on a 25k-word meeting (8k and 12k windows scored lower) |
| Attendee list, glossary, per-question `instructions`, `jev-preview` | No gain, or slightly worse |

**Independent check.** Two meetings were never used for tuning: All Hands (10 Sep) and Blocker removal (1 Sep). Their answer keys were written from the full transcripts and 4 judgement calls were confirmed by the user.
- **Score:** **27/30 = 90.0%**.
- **Misses:**
  - Two of the user's judgement calls: a SOC 2 thank-you, which Jev counted as security work, and a small "I'll ask Global Relay" follow-up, which Jev did not count as a decision.
  - `clear_owners` on a meeting with many owners.

Caveats:
- Only 8 meetings were used, so one answer is worth about 1%.
- The final wording was partly tuned on the test meetings.
- Before trusting the numbers, validate on 5–10 new meetings whose answer keys you have checked yourself.

## Known weak spots

- **Hedged language sits near 0.5.** Examples: whether "in a few days" counts as a deadline, or whether an idea was only floated or an existing plan was changed.
- **Ownership when the focus person is absent.** Whether work that depends on Nayem counts as theirs when they were not in the meeting.
- **Very long meetings** (over 20k tokens) are less reliable, even with windows.
