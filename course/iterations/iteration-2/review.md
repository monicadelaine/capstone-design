# Iteration 2 Review

> **DRAFT as of 2026-10-25.** Rows marked "open" are updated on 2026-10-27 after the presentation, then this banner is removed.

**Date:** 2026-10-27
**Presenters:** to fill in on 10/27

## Iteration Goal

Close the security gaps inherited from v1 so that a student can only see and change their own data, finish the student ranking form, and establish whether Google OR-Tools can drive the assignment feature the sponsor asked for.

Plan and open sponsor questions: [sponsor-planning.md](sponsor-planning.md). Planning snapshot: [planning.png](planning.png).

## Plan vs. actual

9 Issues planned (7 new, 2 carried from Iteration 1). Board view: [06 - Iteration 2 Results](https://github.com/users/mbaizhakyp/projects/1/views/7).

| # | Owner | Item | Status 10/25 | Evidence |
|---|---|---|---|---|
| #43 | Noland | Restrict preference and assignment access; role permission class | open | |
| #12 | Noland | Dev environment sign-off (carried) | open: no "runs on mine" comments yet | |
| #16 | Jayden | Student ranking form (carried) | Issue closed 10/08, PR #39 still unreviewed and unmerged | PR #39, CI green |
| #48 | Jayden | Board views; plan and results snapshots | plan snapshot done | [planning.png](planning.png) |
| #49 | Gaurav | Tests for role permissions and ownership | open | |
| #44 | Margulan | OR-Tools CP-SAT evaluation spike | done 10/25 | [or-tools-evaluation.md](../../../docs/investigations/or-tools-evaluation.md) |
| #45 | Margulan | Team-owned Auth0 tenant | setup guide written; tenant not yet created | [auth0-setup.md](../../../docs/development-guide/auth0-setup.md) |
| #46 | Margulan | Sponsor planning record and snapshot | done 10/25 | [sponsor-planning.md](sponsor-planning.md) |
| #47 | Margulan | This package | in progress | |

## What was demonstrated

To fill in on 10/27. Candidates: the OR-Tools script assigning 100 students to 25 projects in under a tenth of a second; the ranking form from PR #39; a student blocked from another student's preferences, if #43 lands.

## Quality and testing results

- OR-Tools spike script carries its own self-check (known-optimum case and an infeasible case).
- Backend suite count and CI status on `main`: to fill in on 10/27.

## Sponsor feedback

No reply yet on the ranking rule or teammate preferences, first asked 9/22. The OR-Tools spike shows why they matter: with only 3 ranks and popular projects, 7 of 100 sample students land on a project they did not rank.

## Backlog changes

- From the spike: before #51, decide how a solver proposal is stored until the admin approves it, and whether team size is exact or a range.
- From #45: the interim Auth0 Action assigns roles by email domain; #43 must replace it with a Student-table lookup.

## Late items

To fill in on 10/27 if anything misses the deadline.
