# Iteration 3 Review

**Date:** 2026-11-20
**Presenters:** Margulan Baizhakyp, Gaurav Shrivastava, Jayden White, Noland Miller ([slides](../../presentations/iteration-3-final.pdf))

> Written from the repository record: Issues, pull requests, CI, and the tag `iteration-3-submission` (2026-11-20), updated on 2026-11-21 for the handoff documentation merged that day.

## Iteration Goal

One full semester runs end to end: the instructor imports students and approves projects, students rank, the solver proposes teams that the instructor can adjust and approve, and students and sponsors see their teams. The handoff docs let the next team deploy and continue.

**Result:** the full semester workflow is built, tested, and demonstrated, and the complete handoff documentation set is on `main`.

| Part of the goal | Result |
|---|---|
| The full semester workflow | **Delivered.** Every step works on `main`: submit, review, import, rank, propose, adjust, approve, see teams |
| Tools for the instructor | **Delivered.** Project review, roster import, team sizes, and adjust-and-approve are tested tools in the administration area |
| Screens for students and sponsors | **Delivered.** Ranking, team views, attachments, and notification emails in the Vue app |
| Handoff docs | **Delivered.** User guide, development guide, deployment guide, security assessment, recommendations, and FAQ are all merged |
| The deployed site | Live at https://ua-capstone-design.duckdns.org since 10/27, healthy, with HTTPS. Bringing it up to the latest `main` is the first handoff action, and the deployment guide gives the exact steps |

Plan and sponsor questions: [sponsor-planning.md](sponsor-planning.md).

## Plan vs. actual

19 Issues committed. **12 closed**, and the remaining 7 carry into handoff with the progress shown. Beyond the plan, the team also delivered 1 stretch item and 9 unplanned additions.

| # | Owner | Item | Result | Evidence |
|---|---|---|---|---|
| #50 | Jayden | Ranking deadline and rule enforced server-side | Done | PR #86 |
| #54 | Jayden | Student notification emails | Done | PR #86 |
| #66 | Jayden | Import students from a Blackboard CSV | Done | PR #101, 42 tests |
| #70 | Jayden | Students see their project and teammates | Done | PR #102 |
| #71 | Jayden | Sponsors see their assigned students | Done | PR #102 |
| #72 | Jayden | Sponsor attachments | Done | PR #93 |
| #73 | Jayden | Admin sponsor emails with preview and a send log | Done | PR #90 |
| #82 | Jayden | User guide | Done | PR #112: all three roles, with screenshots |
| #69 | Gaurav | Adjust a proposal before approving | Done | PR #95 |
| #68 | Gaurav | Team size and project capacity | Done | PR #97 |
| #67 | Gaurav | Approve pending projects into a semester | Done | PR #96 |
| #57 | Margulan | Feedback and attachment endpoints by role | Done | PR #108 |
| #83 | Noland | Deployment guide and handoff | Guide and recommendations merged | PRs #115, #117. Remaining: a teammate redeploys from the guide |
| #52 | Noland | Hosting and staging instance | Site live | PR #59. Remaining: the written hosting comparison |
| #58 | Noland | Deployed site on the team Auth0 tenant | Carried to handoff | Steps are in the deployment guide |
| #77 | Margulan | Roles assigned on the server | Partly delivered | PR #118: the API accepts students only from the instructor's roster. Remaining: the Auth0 Action change |
| #81 | Margulan | Sponsor answers recorded | Carried to handoff | Team size and the ranking rule were built as settings, so either answer needs no code change |
| #84 | Margulan | Sponsor planning record | Record written and approved by the team 11/10 | [sponsor-planning.md](sponsor-planning.md) |
| #45 | Margulan | Team-owned Auth0 tenant (carried) | Tenant live and in use | Remaining: teammates' confirmations on the Issue |

Stretch items:

| # | Item | Result | Evidence |
|---|---|---|---|
| #78 | Key caching and removal of the debug panel | Done | PR #105 |
| #74, #75, #76, #79, #80 | Automatic project status, teammate requests, resend verification, duplicate names, end-to-end test | Handed off as a prioritised backlog | [Recommendations](../../../docs/recommendations/README.md) |

Added during the iteration, beyond the plan:

| # | Owner | Item | Evidence |
|---|---|---|---|
| — | Margulan | Fix for a login hang when a user has no role | PR #60 |
| — | Noland | Token validation hardening; admin-only writes to student and sponsor records | PRs #98, #99 |
| — | Gaurav | Follow-up fixes from code review | PR #106 |
| #107 | Gaurav | Fairness limit for proposals, and a side-by-side comparison of team-size settings | PR #114, 23 tests |
| #109 | Gaurav | Development guide: architecture, main flows, adding a feature, conventions, with 18 diagrams | PR #113, reviewed by Noland |
| #110 | Gaurav | FAQ: handoff, instructor how-do-I, common errors | PR #120 |
| — | Gaurav | Deployment guide rehearsed against the production stack, with a fix for first-time deployments | PR #115 |
| — | Gaurav | Security assessment, with every API action checked against five kinds of user | PR #119 |
| — | Gaurav | Two security hardening fixes from that assessment | PRs #116, #118 |

**Who did the work.** Jayden delivered all 8 of the student- and sponsor-facing items. Gaurav delivered the instructor and solver flow and the handoff documentation. Noland delivered the security hardening and the live deployment. Margulan delivered the planning records, the team Auth0 tenant, and the login fix.

## What was demonstrated

A live demo of the whole workflow, in six steps: a sponsor submits a project, the instructor reviews it, a student ranks 5 high, 5 medium and 5 low, the solver proposes teams, the instructor adjusts and approves, and students and sponsors see their teams.

## Quality and testing results

| Measure | Iteration 2 | Iteration 3 |
|---|---|---|
| Backend tests passing | 258 | 496 |
| Frontend tests passing | 28 | 75 |
| CI on every push and PR | yes | yes, green on `main` throughout |
| Pull requests merged (10/28 to 11/21) | | 23 |
| Security gaps inherited from the previous version | 8 open at the start of the semester | 7 fixed, 1 mostly fixed |

- Backend tests nearly doubled, and frontend tests more than doubled.
- New tests for a fix are run against the old code first, to prove they catch the problem.
- Code review produced real improvements: reviews of #95 to #97 led to follow-up PR #106, and the review of #113 sharpened the development guide.
- The deployment guide was rehearsed by building the production stack from a clean copy of `main`, including a database backup and restore.
- The [security assessment](../../../docs/security/README.md) records the response of every API endpoint to each kind of user, and the two issues it found were fixed and merged with tests the same day.

## Sponsor feedback

The sponsor's design is the product's workflow: assignment treated as a constraint problem solved with OR-Tools, a proposal the instructor reviews and edits before it is final, and teams of four as the default. Where an answer was still open, the team built the setting rather than the assumption: team size is set per semester with a per-project maximum, and the proposal is editable before approval. The three open questions are recorded in #81 for the handoff.

## Backlog changes

- Closed this iteration: #50, #54, #57, #66 to #73, #78, #82, #107, #109.
- Handed off with priorities and effort estimates in [Recommendations](../../../docs/recommendations/README.md): #74, #75, #76, #79, #80.
- The recommendations page also lists the first five things for the next team to do, and ten options the team considered and decided against, each with its reason.

## Stand-ups

Eleven in the window, up from five in Iteration 2: [#85](https://github.com/monicadelaine/capstone-design/issues/85) 10/28, [#87](https://github.com/monicadelaine/capstone-design/issues/87) 10/31, [#88](https://github.com/monicadelaine/capstone-design/issues/88) 11/02, [#89](https://github.com/monicadelaine/capstone-design/issues/89) 11/03, [#91](https://github.com/monicadelaine/capstone-design/issues/91) 11/05, [#92](https://github.com/monicadelaine/capstone-design/issues/92) 11/10, [#94](https://github.com/monicadelaine/capstone-design/issues/94) 11/12, [#100](https://github.com/monicadelaine/capstone-design/issues/100) 11/14, [#103](https://github.com/monicadelaine/capstone-design/issues/103) and [#104](https://github.com/monicadelaine/capstone-design/issues/104) 11/17, [#111](https://github.com/monicadelaine/capstone-design/issues/111) 11/19. Full list: [course/README.md](../../README.md#stand-ups).

## AI use

AI assistance was used materially by the team this iteration, for code, tests, reviews and documentation. Each pull request and Issue carries its own note on what was assisted and how it was verified. The common checks were: new tests run against the old code to confirm they fail there, the full suites in CI, and, for the guides, commands run and links checked by script. This review and the retrospective were drafted with AI assistance from the repository record and checked against it.
