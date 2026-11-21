# Iteration 3 Review

**Date:** 2026-11-20
**Presenters:** Margulan Baizhakyp, Gaurav Shrivastava, Jayden White, Noland Miller ([slides](../../presentations/iteration-3-final.pdf))

> Written 2026-11-21 from the repository record: Issues, pull requests, CI, and the tag `iteration-3-submission` (commit `6513bcf`, 2026-11-20). Teammates: correct anything that is wrong before this merges.

## Iteration Goal

One full semester runs on the deployed site without Django admin: the instructor imports students and approves projects, students rank, the solver proposes teams that the instructor can adjust and approve, and students and sponsors see their teams. The handoff docs let the next team deploy and continue.

**Result:** the workflow is complete on `main` and was demonstrated. Three parts of the goal were not met at the tag:

| Part of the goal | Result |
|---|---|
| The full semester workflow | **Met.** Every step works on `main`: submit, review, import, rank, propose, adjust, approve, see teams |
| "On the deployed site" | **Not met.** The live site was last built on 2026-10-27 and has none of this iteration's work. #52 and #58 are open |
| "Without Django admin" | **Not met as written.** The instructor's tools were built as Django admin pages and actions. Students and sponsors use the Vue app |
| Handoff docs | **Partly met.** The user guide is merged (PR #112). The development guide, deployment guide, recommendations, security assessment and FAQ were opened as pull requests on 11/20 and 11/21 and are awaiting review |

Plan and open sponsor questions: [sponsor-planning.md](sponsor-planning.md).

## Plan vs. actual

19 Issues committed. **12 done, 7 open** at the tag. An Issue counts as done here only when it is closed, which is the team's [Definition of Done](../../../docs/definition-of-done.md). The slides shown on 11/20 counted all 19 as delivered; the seven below were in progress, not finished.

| # | Owner | Item | Result | Evidence |
|---|---|---|---|---|
| #50 | Jayden | Ranking deadline and rule enforced server-side | Done | PR #86, merged 11/03 |
| #54 | Jayden | Student notification emails | Done | PR #86 |
| #66 | Jayden | Import students from a Blackboard CSV | Done | PR #101, merged 11/20 |
| #70 | Jayden | Students see their project and teammates | Done | PR #102, merged 11/20 |
| #71 | Jayden | Sponsors see their assigned students | Done | PR #102 |
| #72 | Jayden | Sponsor attachments | Done | PR #93, merged 11/12 |
| #73 | Jayden | Admin sponsor emails | Done | PR #90, merged 11/12 |
| #82 | Jayden | User guide | Done | PR #112, merged 11/20 |
| #69 | Gaurav | Adjust a proposal before approving | Done | PR #95, merged 11/17 |
| #68 | Gaurav | Team size and project capacity | Done | PR #97, merged 11/17 |
| #67 | Gaurav | Approve pending projects into a semester | Done | PR #96, merged 11/17 |
| #57 | Margulan | Feedback and attachment endpoints by role | Done | PR #108, written by Noland, merged 11/20 |
| #58 | Noland | Deployed site on the team Auth0 tenant | **Open** | No comment or PR on the Issue |
| #52 | Noland | Hosting and staging instance | **Open** | The site has been live since 10/27 (PR #59). The hosting investigation and decision record the Issue asks for are not written, and the site was not redeployed this iteration |
| #83 | Noland | Deployment guide and handoff | **Open** | `docs/deployment-guide/` was a placeholder at the tag. PRs #115 and #117, by Gaurav, opened 11/20 and 11/21, awaiting review. Nobody has redeployed from the guide |
| #77 | Margulan | Roles assigned on the server | **Open** | No PR. PR #118 (open) closes one part: the API no longer lets a student token add itself to the roster |
| #81 | Margulan | Sponsor answers recorded | **Open** | No answers recorded on the Issue |
| #84 | Margulan | Sponsor planning record and plan snapshot | **Open** | The record exists and was approved by the team on 11/10. Not confirmed with the sponsor; no plan snapshot; the due date is blank |
| #45 | Margulan | Teammates confirmed on the team Auth0 tenant (carried) | **Open** | No teammate has confirmed a login on the Issue; sponsor invite not recorded |

Stretch items:

| # | Item | Result | Evidence |
|---|---|---|---|
| #78 | Key caching and the debug panel | Done | PR #105, Noland, merged 11/17 |
| #80 | End-to-end test of a full semester | **Open** | No such test is in the repository. The slides listed it as delivered |
| #74, #75, #76, #79 | Automatic project status, teammate requests, resend verification, duplicate names | Open, unassigned | Handed off as backlog |

Added during the iteration:

| # | Owner | Item | Evidence |
|---|---|---|---|
| — | Margulan | Login hang when a user has no role | PR #60, merged 11/03 |
| — | Noland | Token validation hardening; admin-only writes to student and sponsor records | PRs #98, #99, merged 11/14 and 11/17 |
| — | Gaurav | Fixes from the reviews of #95 to #97 | PR #106, merged 11/17 |
| #107 | Gaurav | Fairness limit for proposals; side-by-side team-size comparison | PR #114, open |
| #109 | Gaurav | Development guide: architecture, flows, adding a feature, conventions | PR #113, open, reviewed by Noland 11/21 |
| #110 | Margulan | FAQ | PR #120 by Gaurav, open |
| — | Gaurav | Security assessment, and two defects it found | PRs #119, #116, #118, open |

**Who did the work.** Jayden held 8 of the 19 committed items and closed all 8. #57 was assigned to Margulan and implemented by Noland. The drafts for #83 and #110 were written by Gaurav after the tag, because neither had been started; their owners are asked to review and correct them.

## What was demonstrated

A live demo followed the slides, along the six steps they show: a sponsor submits a project, the instructor reviews it, a student ranks 5 high, 5 medium and 5 low, the solver proposes teams, the instructor adjusts and approves, and students and sponsors see their teams.

**Presenters to confirm:** whether the demo ran on a local stack or the live site (the live site did not have this iteration's work), and anything that was shown beyond those steps. No demo script was committed for this iteration.

## Quality and testing results

| Measure | Iteration 2 | Iteration 3 (at the tag) |
|---|---|---|
| Backend tests passing | 258 | 469 |
| Frontend tests passing | 28 | 75 |
| CI on every push and PR | yes | yes, green on `main` |
| Pull requests merged in the window (10/28 to 11/20) | | 14 |
| ...of which reviewed or merged by someone other than the author | | 7 |

- The practice from Iteration 2 continued: tests for a fix are run against the old code first to show they fail there.
- Reviews of #95, #96 and #97 by Jayden produced a follow-up PR (#106).
- Still open from Iteration 2: CI runs the backend on SQLite, not PostgreSQL; no browser tests.
- Found after the tag, while writing the handoff docs: a first deployment from `main` failed on a new server (fixed in PR #115); a sponsor's name was shown unescaped in the admin (PR #116); a student token could add itself to the roster (PR #118). `npm audit` reports 21 advisories and `pip-audit` 3; neither is addressed yet.

## Sponsor feedback

None recorded this iteration. The three questions first asked on 9/22 (ranking rule, team size, teammate requests) are still unanswered (#81). The team built 5/5/5 ranking as the rule and made team size a setting, so the first two can be changed without code; teammate requests (#75) were not built.

## Backlog changes

- New: #107 (fairness and comparison), #109 (development guide), #110 (FAQ).
- Handed off unassigned: #74, #75, #76, #79, #80.
- From the security assessment (PR #119): limit who can read the roster, upgrade the flagged dependencies, switch on secure cookies. Not yet Issues.
- From the deployment guide (PR #115): nightly database backup, a storage bucket for uploads, and the reminder schedule on the server. Not yet Issues.

## Stand-ups

Eleven in the window: [#85](https://github.com/monicadelaine/capstone-design/issues/85) 10/28, [#87](https://github.com/monicadelaine/capstone-design/issues/87) 10/31, [#88](https://github.com/monicadelaine/capstone-design/issues/88) 11/02, [#89](https://github.com/monicadelaine/capstone-design/issues/89) 11/03, [#91](https://github.com/monicadelaine/capstone-design/issues/91) 11/05, [#92](https://github.com/monicadelaine/capstone-design/issues/92) 11/10, [#94](https://github.com/monicadelaine/capstone-design/issues/94) 11/12, [#100](https://github.com/monicadelaine/capstone-design/issues/100) 11/14, [#103](https://github.com/monicadelaine/capstone-design/issues/103) and [#104](https://github.com/monicadelaine/capstone-design/issues/104) 11/17, [#111](https://github.com/monicadelaine/capstone-design/issues/111) 11/19.

All four members commented on seven of them (#89 to #104). The first three had two or three members; #111 had two as of 11/21. Full list: [course/README.md](../../README.md#stand-ups).

## AI use

AI assistance was used materially by the team this iteration, for code, tests, reviews and documentation. Each pull request and Issue carries its own note on what was assisted and how it was verified. The common checks were: new tests run against the old code to confirm they fail, the full suites in CI, and, for the guides, commands run and links checked by script. This review and the retrospective were drafted with AI assistance from the repository record and checked against it.
