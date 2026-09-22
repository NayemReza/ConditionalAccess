# Jev (jev-1.13) question-writing guide for meeting analysis

Sources: docs.typesafe.ai (llms.txt index; all required pages read in full, rest skimmed), plus the agent SKILL.md on GitHub. Raw and cleaned copies are in `raw/` and `clean/` next to this file.

## 1. Primitive semantics

- **Every question is evaluated independently and in parallel against the same state.** Answers never feed into each other. Batching 13 questions gave the same answers as 13 separate calls (parallel_questions cookbook). Question IDs are *not* sent to the model: "Write the complete question in `instructions`."
- **instructions** = "The question you are asking about the state. This is where your evaluation logic goes." **criteria** = the answer space. Both are sent and both matter. Jaggedness #7: "When the `instructions` and the `criteria` ask for different things, `jev-1.13` might get confused … treat the criteria as an extension of the instruction."
- **Noul** returns `noul` = P(yes), with no separate confidence. `criteria` is optional `{true, false}`, "an optional clarification of what yes and no mean". Docs: "try your questions with and without `criteria` and keep whichever gives better answers." Phrase it so that high means yes ("Is the message free of personal data?" inverts the meaning). SDE cascade: "frame each question so the *escalate* case is the `true` case, and state what `true`/`false` mean." A Noul near 0.5 means an unclear case, not a medium amount. A statement works as well as a question.
- **Score**: ordered levels (2–10). "The model gets the descriptions and nothing else, and each level is judged on its own against the state … doesn't see a level's number or its neighbours." `score` = Σ level×prob. Use it for thresholds and ranking only, never for interpolating magnitudes.
- **Choice**: `choice` = argmax. Probabilities sum to 1 (relative). Up to 255 options, reliable to ~240. Option names *and* descriptions are sent (`null` is fine when the name is self-explanatory). Add `other` / `none of the above`.
- **JSON structure** (primitives/advanced) is allowed in instructions, Choice option values, Score levels and Noul true/false. Field names are free-form: `question`, `focus`, `inspect`, `compare`, `what`, `not_for`, `examples`, `signals`. Use structure "when it helps with clarity" or when "the question needs supporting data" (a record from code referenced by backtick). Use it when neighbouring options or levels get confused: "Give it fields for what the option covers, what belongs to a neighboring option instead, and a few example inputs." Keep the field names the same across options. Examples help only if they resemble real inputs. In the Safari example, a matching example moved confidence from 0.35 to 0.96; an unrelated example changed nothing.

## 2. Documented failure modes (jev-1.13) and workarounds

1. **Literal reading.** "Scoping words, negations, and implied conditions are read at face value." Write the exact condition, put boundary cases in the criteria, or "split it into two literal questions and combine them in code". "When … you find yourself explaining what you really meant, that explanation is the missing half of the instruction."
2. **Math and counting.** "does not count reliably … error grows with the size". Iterate over candidates with one Noul each and sum in code. Pass numbers in semantic form (named buckets).
3. **Date comparison.** Extract the parts with Choice and compare them in code.
4. **Indirection and double negatives.** "Reduce hops; point to the relevant state", naming it by backticked path.
5. **Large state full of irrelevant detail.** "Accuracy falls as the state grows with content unrelated to the decision … Jev suffers from context rot." Filter first, or use a relevance Noul to filter.
6. **Adversarial content in the state.** Be explicit in the criteria and test edge cases.
7. **Contradictory instructions and criteria.** For example, a Noul where true maps to "no".
8. **Structural invariants do not hold.** P(q) and P(not q) summed to 1.19 in their example. Noul thresholds do not transfer to Choice.
9. **Generation.** Select from candidates instead of generating.

## 3. State design

- Use an object with named fields for most requests. Put related material together when the decision compares parts. Keep content separate from questions.
- Point questions at fields: "Does `ticket.messages[0].text` request a refund?"
- Send "only the fields the question needs". The cookbooks trim hard: the section containing the quote (citation check), Item 1 only (SEC filings), one query+passage pair per request (RAG).
- Line-ID tagging ("L052| …") plus a Choice over line IDs locates evidence. Pair it with an "exists" Noul, because Choice always ranks something first.
- A `focus` field is documented, but inside **instructions** (e.g. "Classify the customer's primary request, not every topic mentioned"). No page shows a focus or metadata field in the *state* helping. Budget: 32k tokens for state plus the longest question.

## 4. Accuracy techniques

- **Self-consistency** cookbooks measure run-to-run repeatability: mean std 0.010 (Noul) and 0.0098 (Choice). They do **not** test paraphrase ensembles, and repeating a call adds nothing. Their fix is an uncertain band (Noul 0.30–0.70; Choice top probability < 0.60 → review), which raised decision agreement from 90.8% to 99.2%.
- The closest thing to an ensemble: skill_suggestion averages three differently framed gate Nouls, one of them inverted (`1 - p`).
- **Speculative fan-out**: ask everything in one call and ignore irrelevant answers. Per the SKILL.md, "State each speculative premise explicitly" ("If this is a shipping problem…").
- **Composite scoring**: use atomic Scores, normalize each by `len(levels)-1`, then apply weights in code. For "any serious violation" rules, gate with `max` rather than a mean ("instead of being averaged into silence").
- **Confidence** is a summary of the distribution's shape. Thresholds should scale with risk (floor 0.5–0.6; high-stakes >0.85–0.9). SEC case: confidence ≥ 0.9 meant 90% correct, below it 40% correct. Tune on labelled data. Pin `jev-1.13.0` once thresholds are tuned.

## 5. Verbatim good and bad examples

- Good: "Does this message convey urgency?" Bad: "Analyze this message and determine the best course of action".
- Bad: `is_spam: "Is \`message\` spam?"`. Good: six atomic Nouls, e.g. "Does \`message.body\` ask the recipient to provide a password or other login credential?"
- Bad: "Is the customer angry and asking for a refund?" (two conditions). Bad: "Is the message free of personal data?" (inverted).
- Unclear: "Is this candidate strong in Python?" Good: "Does the resume state that the candidate has used Python at work?"
- Bad Score: "Rate severity from 0 to 2" with `["0","1","2"]` → 0.55/conf 0.33. Descriptive levels → 0.0/conf 1.0. "Describe situations, not degrees"; "Moderately severe" is bad.
- Bad: "Which resolution?" (named after the parameter). Write about the idea.
- Good negative boundary, placed in criteria: `false: {what: "Does not ask for a refund or credit", not_for: "A complaint or billing question without a requested remedy", examples: ["Why was I charged twice?"]}`.

## 6. Top 10 recommendations for our meeting questions

1. **Shrink the state per question group.** Split transcripts into time or topic windows (or run a relevance Noul pass first), ask the per-item questions per window, and combine in code with `max` or `any`. 24k tokens of mostly irrelevant talk is exactly failure mode #5.
2. **Structure the state:** `{"meeting": {...}, "known_issues": [...], "lines": [{"id":"L041","t":"12:03","speaker":"Ana","text":"..."}]}`. Refer to `lines` and `known_issues` by backticked path.
3. **New vs already-known blocker:** don't ask the model to infer history. Put prior issues (tracker or previous-meeting notes) in `known_issues`. Ask "Is a blocker raised in `lines`?" separately from "Is it already described in `known_issues`?", or do this per candidate with structured instructions (`{candidate: ..., question: ...}`). Combine in code.
4. **Remove negation clauses from instructions.** Move "X does not count" into `criteria.false` (`what` / `not_for` / `examples`) or a `not_for` field on the option, and keep the instruction a direct positive question. Make sure true is the thing you're flagging.
5. **Hedged decisions:** give the Score a level that describes the hedge as a situation, for example `{"what":"Tentative or conditional decision","examples":["let's go with Postgres unless perf tests fail","I think we're leaning toward…"]}`. Remember each level is judged alone. Alternatively, split into a "decision reached" Noul and a "firmness" Score.
6. **Scope drift:** add `focus: "Judge only work done or decided in this meeting; ignore background or history"` in the instructions. Put background examples on the false side. Or ask "mentioned" and "acted on in this meeting" as two Nouls.
7. **No counting questions.** Ask one Noul per candidate (a line, window or extracted item) and sum in code. Never use Score levels like "1–2 / 3–5 items".
8. **One dimension per Score, one condition per Noul.** Use 3–5 descriptive levels without numbers, taken from real transcript phrasing.
9. **For the Choice,** add a `none_of_the_above` option, use contrastive `what` / `not_for` fields, and add a companion "exists" Noul. To show evidence, a Choice over line IDs works for up to 255 lines per window.
10. **Calibrate instead of ensembling.** Use review bands (Noul 0.3–0.7; Choice or Score confidence < 0.6), tune thresholds on 20–50 hand-labelled meetings, and pin `jev-1.13.0`. Repeat calls add nothing. Paraphrase averaging (with inverted variants flipped as `1 - p`) is undocumented, so test it before relying on it. Keep all 15 questions in one batched call.
