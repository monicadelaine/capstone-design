# Iteration 2: Sponsor Planning Record

**Sponsor:** Dr. Monica Anderson Herzog
**Planning date:** 2026-10-22 (late; Iteration 2 is due 2026-10-27)
**Status:** proposed by the team, not yet confirmed with the sponsor

## Iteration 2 Goal (proposed)

Close the security gaps inherited from v1 so that a student can only see and change their own data, finish the student ranking form, and establish whether Google OR-Tools can drive the assignment feature the sponsor asked for.

## What the sponsor asked for (carried from Iteration 1)

- Assignment treated as a constraint-satisfaction problem, proposed by a solver (OR-Tools CP-SAT), approved by the admin. This iteration: the evaluation spike (#44). Next iteration: the feature (#51).

## Questions still open with the sponsor

| Question | Why it matters | Status |
|---|---|---|
| Ranking rule: 5 high / 5 medium / 5 low, top 3, or other? | Defines the ranking form validation and the solver's input | Asked 9/22; no answer. Re-asking this week. |
| Should students be able to request or avoid teammates? | Changes the data model and the solver constraints | Asked 9/22; no answer. Re-asking this week. |
| Team size: is 4 per project the rule or an example? | Solver capacity constraint | Assumed 4 from her example. |

## Iteration 2 plan

| # | Owner | Item |
|---|---|---|
| #43 | Noland | Restrict preference and assignment access to the owning student; role permission class |
| #12 | Noland | Dev environment sign-off (carried) |
| #16 | Jayden | Student ranking form, PR #39 (carried) |
| #48 | Jayden | Board views populated; plan and results snapshots |
| #49 | Gaurav | Tests for role permissions and ownership rules |
| #44 | Margulan | OR-Tools CP-SAT evaluation spike |
| #45 | Margulan | Team-owned Auth0 tenant |
| #46 | Margulan | This record and the planning snapshot |
| #47 | Margulan | Iteration 2 submission package on 10/27 |

Deferred to Iteration 3, already on the board: server-side deadline enforcement (#50), the proposed-assignment feature (#51), hosting and a staging instance (#52), v1 cleanup (#53), student emails (#54).

## Decisions and follow-ups

- Iteration 2 was planned five days before its deadline. The retrospective will record why and the Iteration 3 plan will be made in the first week of the iteration.
