# Iteration 2 Review

**Date:** 2026-10-27
**Presenters:** to fill in on 10/27

## Iteration Goal

Close the security gaps inherited from v1 so that a student can only see and change their own data, finish the student ranking form, and establish whether Google OR-Tools can drive the assignment feature the sponsor asked for.

**Result:** all three parts met. Two setup items remain open: #12 (teammate sign-offs) and #45 (teammates on the new login tenant).

Plan and open sponsor questions: [sponsor-planning.md](sponsor-planning.md).

## Snapshots

| View | File | Captured |
|---|---|---|
| Iteration 2 plan | [planning.png](planning.png) | 2026-10-25 |
| Iteration 2 results | [results.png](results.png) | 2026-10-26 |
| Product Backlog | [product-backlog.png](product-backlog.png) | 2026-10-26 |
| Team Contributions | [team-contributions.png](team-contributions.png) | 2026-10-26 |
| Engineering & Quality Work | [engineering-quality.png](engineering-quality.png) | 2026-10-26 |

Live board: https://github.com/users/mbaizhakyp/projects/1

## Plan vs. actual

9 Issues planned (7 new, 2 carried from Iteration 1). 5 done, 4 open (one of them, #47, closes when the tag is pushed). Nothing was removed from the plan.

| # | Owner | Item | Result | Evidence |
|---|---|---|---|---|
| #16 | Jayden | Student ranking form (carried) | Done | PR #39, reviewed and merged 10/26 |
| #43 | Noland | Restrict data access by role | Done | PR #55, merged 10/26 |
| #49 | Gaurav | Tests for the role rules | Done | PR #55: 36 tests |
| #44 | Margulan | OR-Tools evaluation spike | Done | [or-tools-evaluation.md](../../../docs/investigations/or-tools-evaluation.md) |
| #46 | Margulan | Sponsor planning record and snapshot | Done | [sponsor-planning.md](sponsor-planning.md) |
| #12 | Noland | Dev environment sign-off (carried) | **Open** | No teammate has posted "runs on mine" yet |
| #45 | Margulan | Team-owned Auth0 tenant | **Open** | Team tenant created 10/26 and verified on one machine (login and saving preferences); teammates' logins and sponsor invite pending |
| #48 | Jayden | Board views and snapshots | **Open** | Snapshots committed; the Team Contributions view is not yet grouped by person |
| #47 | Margulan | This package | Open until the tag is pushed | this folder |

Also added: a `seed_demo` command (PR #56) so any machine can load demo data.

**Who did the work.** #43 and #49 were assigned to Noland and Gaurav but were implemented by Margulan, with AI assistance, on 10/26 so the goal could be demonstrated. Noland and Gaurav are asked to review PR #55. The contribution view shows the Issue owners, not the implementer; the PR shows who wrote it.

## What was demonstrated

Script: [demo-script.md](demo-script.md). The solver assigning 100 students to 25 projects; a student ranking projects; the API refusing another student's data; the test suites.

## Quality and testing results

| Measure | Iteration 1 | Iteration 2 |
|---|---|---|
| Backend tests passing | 188 | 240 |
| Frontend tests passing | 36 | 36 |
| CI on every push and PR | yes | yes, green on `main` |

- The 36 new security tests were run against the old code first: 30 failed, 3 passed (the "allowed" cases). So they detect the holes they target.
- The OR-Tools script has its own self-check (a known-optimum case and an infeasible case).
- Still open: feedback and attachment endpoints accept any logged-in user; CI runs the backend on SQLite, not Postgres; no browser tests.

## Sponsor feedback

No reply yet on the ranking rule or teammate preferences, first asked 9/22. The spike shows why they matter: with only 3 ranks and popular projects, 7 of 100 sample students land on a project they did not rank.

## Backlog changes

- From the spike: before #51, decide how a solver proposal is stored until the admin approves it, and whether team size is exact or a range.
- From #45: the interim Auth0 Action assigns roles by email domain; a roster lookup should replace it.
- From #43: feedback and attachment endpoints need the same treatment: #57, Iteration 3.

## Stand-ups

[#37](https://github.com/monicadelaine/capstone-design/issues/37) 10/06, [#38](https://github.com/monicadelaine/capstone-design/issues/38) 10/08, [#40](https://github.com/monicadelaine/capstone-design/issues/40) 10/13, [#41](https://github.com/monicadelaine/capstone-design/issues/41) 10/15, [#42](https://github.com/monicadelaine/capstone-design/issues/42) 10/20, plus the in-class stand-up on 10/27.

There were no stand-up Issues between 9/24 and 10/06, and none on 10/22.

## AI use

Claude (Claude Code) was used materially in this iteration, directed by Margulan:

| Artifact | How it was verified |
|---|---|
| OR-Tools script and evaluation (#44) | Self-check in the script; runs at three sizes recorded in the report |
| Security rules and tests (PR #55) | Tests fail on the old code and pass on the new; CI green |
| `seed_demo` command (PR #56) | Test runs it twice and checks counts; run against a fresh database |
| Review of PR #39 | Findings checked against the diff and models |
| Auth0 setup guide, testing guide updates, demo script, this review, the retrospective | Checked against the code and the board; commands run where possible |

Each PR and Issue above also carries its own AI note.
