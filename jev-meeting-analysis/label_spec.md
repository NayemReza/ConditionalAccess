# Meeting-analysis label spec (the TARGET meaning of each field)
Label every field from the FULL transcript. "Nayem" = Nayem Reza (Voxsmart). Things count even if Nayem was not present / not speaking.
Output JSON: {"field": {"label": <value>, "evidence": "<short quote + [mm:ss]>", "certainty": "high|medium|low"}}

- purpose (one of): recurring_status | project_working_session | proposal_signoff | vendor_or_partner | company_broadcast | planning_or_strategy | other
- interaction (0-3 int): 0 one person talks almost all the time; 1 mostly one presenter with a few questions; 2 balanced back-and-forth; 3 active collaboration/debate
- decision_agreed (bool): participants explicitly agreed a course of action in this meeting (hedged but clear agreements like "probably not this round, let's look next cycle" count)
- plan_changed (bool): an EXISTING plan/date/decision was changed, postponed or cancelled in this meeting (a brand-new plan is not a change)
- clear_owners (bool): by the end, next steps had named owners
- nayem_new_task (bool): Nayem took on or was given a NEW task in this meeting
- nayem_big_deliverable (bool): in THIS meeting's work, Nayem owns a large deliverable (build/launch of a product, site or system). Nayem's unrelated work merely mentioned as background = false
- nayem_due_7_days (bool): a task owned by Nayem has a deadline within 7 days of the meeting date (date, weekday, "today", "Monday"...)
- others_waiting_on_nayem (bool): someone else's next step is explicitly blocked/waiting on Nayem delivering something
- new_blocker (bool): a NEW blocker, first raised in this meeting, that could stop a deliverable or make it miss its deadline. Known/pre-existing issues = false
- known_issue_escalated (bool): an already-known problem was reported as getting worse, overdue, or needing escalation
- deadline_risk (0-3 int): 0 no deadline discussed as at risk; 1 tight but on track; 2 at least one likely to slip; 3 at least one already missed
- security_work (bool): security/compliance WORK discussed in substance (pen testing, audits, ISO/SOC 2 certification, access control, compliance tooling). Passing mentions = false
- company_spend (bool): money Voxsmart spends or would spend discussed (costs, quotes, prices, budgets, contracts, renewals). Team-time percentages and revenue/pipeline figures alone = false
- vendor_next_step (bool): a next step with an EXTERNAL supplier/partner was agreed (call booked, quote/doc requested, list to share)
