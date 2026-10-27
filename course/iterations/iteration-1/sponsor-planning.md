# Iteration 1: Sponsor Planning Record

**Sponsor:** Dr. Monica Anderson Herzog
**Date:** 2026-09-22, by email
**Attendees:** Margulan Baizhakyp (questions), Dr. Anderson Herzog (answers)

## Iteration 1 Goal

Not stated by the sponsor; no objection to the proposed goal. Proposed: a running, testable baseline of the inherited system on every teammate's machine and in CI, with the architecture decisions recorded and the first sponsor-facing feature (project submission) demonstrable.

## Questions asked and answers

| Question | Answer |
|---|---|
| Ranking rule: 5 high / 5 medium / 5 low, top 3, or other? | No specific preference given. Team decides; confirm with her before building the form. |
| How are assignments decided today, and what beyond rankings matters (majors, skills, prior teams)? | No specific preference given beyond rankings. |
| Should students be able to request or avoid teammates? | No specific preference given. |
| Would a proposed assignment the admin reviews and edits help? | **Yes.** She wants the assignment treated as a constraint-satisfaction problem and solved by a solver with a Python wrapper, suggesting Google OR-Tools CP-SAT (https://developers.google.com/optimization/cp/cp_solver). A cloud-hosted solver is also acceptable. She notes the problem is small even at 100 students and 25 projects. |
| Do sponsors get any say in team selection? | No specific preference given. |
| Continue v1 or replace it? | No objection to continuing v1 (ADR-001). |
| What would make Iteration 1 a success on 9/24? | No specific answer given. |

## Decisions and follow-ups

- **Assignment will be solver-proposed, admin-approved.** The admin reviews and edits the proposal before it is final. This replaces v1's manual row-by-row assignment. Backlog: a SPIKE to evaluate OR-Tools CP-SAT against our data model, then a PBI for the proposed-assignment feature.
- **Her question: how many distinct solutions with 4 students per project?** For 100 students and 25 labeled projects, 100! / (4!)^25 ≈ 2.9 × 10^123. If the teams are unlabeled, divide by 25!: ≈ 1.9 × 10^98. That is the size of the space the solver searches, which is why enumeration is out and a CP solver is the right tool. Answer sent 2026-09-22.
- **Open with her:** the ranking rule (question 1) and whether students can request teammates (question 3), because both change the solver's constraints. Ask again before Iteration 2 planning.
- **Team size:** she used 4 per project as the example. Treat 4 as the default capacity in the data model until told otherwise.
