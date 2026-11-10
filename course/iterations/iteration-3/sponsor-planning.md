# Iteration 3: Sponsor Planning Record

**Sponsor:** Dr. Monica Anderson Herzog
**Planning date:** 2026-11-10 (late: Iteration 3 began after the 10/27 review)
**Iteration 3 due:** to fill in
**Status:** approved by the team 2026-11-10; not yet confirmed with the sponsor

## Iteration 3 Goal

One full semester runs on the deployed site without Django admin: the instructor imports students and approves projects, students rank, the solver proposes teams that the instructor can adjust and approve, and students and sponsors see their teams. The handoff docs let the next team deploy and continue.

## Questions for the sponsor (#81)

To raise in person at the next sponsor meeting. First asked 9/22.

| Question | Why it matters | Blocks |
|---|---|---|
| Ranking rule: 5 high / 5 medium / 5 low, top 3, or other? | Validation in #50 and the solver input | #50 (built on 5/5/5) |
| Should students be able to request or avoid teammates? | Data model and solver constraints | #75 |
| Is team size always 4, or set per project? | Solver capacity | #68, #69 |

## Iteration 3 plan

### Committed

| # | Owner | Item | Status 11/10 |
|---|---|---|---|
| #50 | Jayden | Ranking deadline and rule enforced server-side | Done |
| #54 | Jayden | Student notification emails | Done (PR #86) |
| #66 | Jayden | Import students from a Blackboard CSV | Todo |
| #70 | Jayden | Students see their project and teammates | Todo |
| #71 | Jayden | Sponsors see their assigned students | Todo |
| #72 | Jayden | Sponsor attachments | In Progress |
| #73 | Jayden | Admin sponsor emails | In Progress (PR #90) |
| #82 | Jayden | User guide | Todo |
| #69 | Gaurav | Adjust a proposal before approving | Todo (committed in #89) |
| #68 | Gaurav | Team size and project capacity | Todo; needs #81 |
| #67 | Gaurav | Approve pending projects into a semester | Todo |
| #58 | Noland | Deployed site on the team Auth0 tenant | Todo |
| #52 | Noland | Hosting and staging instance | Todo |
| #83 | Noland | Deployment guide and handoff | Todo |
| #77 | Margulan | Roles assigned on the server | Todo |
| #57 | Margulan | Feedback and attachment endpoints by role | Todo; pairs with #72 |
| #81 | Margulan | Sponsor answers recorded | Todo |
| #84 | Margulan | This record and the plan snapshot | In progress |
| #45 | Margulan | Teammates confirmed on the team Auth0 tenant (carried) | In Progress |

### Stretch, or remaining backlog at handoff

#78 JWKS caching and DEBUG panel, #80 end-to-end semester test, #74 automatic project status, #76 resend verification, #75 teammate requests (needs #81), #79 duplicate project names.

Jayden holds 8 of the committed items. Rebalance at the next stand-up if Gaurav or Noland can take #70 or #71.

## Decisions and follow-ups

- Iteration 2's retrospective action was to plan Iteration 3 in its first week. This record was written 2026-11-10, two weeks in. Work started anyway: #50, #54, and PR #90 came from Issues already on the board.
- Plan snapshot: capture board view "04 - Iteration 3 Plan" as `planning.png` once owners are confirmed.
