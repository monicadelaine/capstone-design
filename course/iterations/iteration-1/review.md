# Iteration 1 Review

**Date:** 2026-09-24 (presented in class; written to the repo 2026-10-06)
**Presenters:** Margulan Baizhakyp, Jayden White, Gaurav Shrivastava. Noland Miller absent (ill).

## Iteration Goal

1. The inherited system running on every teammate's machine and in CI.
2. Architecture decisions recorded as ADRs, not just discussed.
3. First sponsor-facing feature demonstrable: project submission.

Sponsor input is recorded in [sponsor-planning.md](sponsor-planning.md): assignment is to be solver-proposed and admin-approved, using Google OR-Tools CP-SAT.

## Plan vs. actual

17 Issues planned, 11 closed, 6 carried forward. Nothing was removed from the plan. Board view: [05 - Iteration 1 Results](https://github.com/users/mbaizhakyp/projects/1/views/6).

| Owner | Done | Incomplete, carried to Iteration 2 |
|---|---|---|
| Noland | #9 stack ADR, #10 auth ADR, #11 data model | #12 dev environment: PR #32 unmerged, teammate sign-offs missing |
| Jayden | #13 board, #14 product backlog, #15 planning snapshot | #16 student ranking form |
| Gaurav | #17 sponsor submits a project, #20 Definition of Done | #18 test baseline, #19 CI green on PRs (PRs #35, #36 in progress at review; #36 merged 9/29) |
| Margulan | #21 README, #22 docs/ structure, #24 sponsor planning record | #23 course/ structure (presentation PDFs), #25 this review and the tag |

## Completed and incomplete work

Evidence: merged PRs #4, #8, #27, #28, #31, #33, #34; seven stand-up Issues with one comment per person; CI green on `main`; `docs/` tree with decisions, development guide, data model, and v1 investigation.

Why the incomplete items were incomplete: the ranking form depended on the stack decision, which landed 9/17; the test baseline and CI work ran into the Postgres and Auth0 env requirements of the inherited suite; the dev environment waits on a one-line permission fix for Mac/Linux; the course folder waited on a PDF export nobody owned.

## What was demonstrated

Live on a laptop: a sponsor logs in and submits a project; the project appears in the list; the Django admin shows the project and its semester; the backend test suite runs green (188 tests).

## Quality and testing results

- 188 backend tests passing, run by GitHub Actions on every push and pull request.
- Definition of Done written at `docs/definition-of-done.md` and linked from the README.
- Known gaps carried from v1 (no role checks on the API, two unauthenticated endpoint groups, browser-only deadline) are documented in ADR-002 and scheduled for Iteration 2.

## Sponsor feedback

From the sponsor's email of 2026-09-22: treat assignment as a constraint-satisfaction problem solved by OR-Tools; the admin approves the result. She asked how many distinct assignments exist for 100 students on 25 projects of 4; we answered about 2.9 × 10^123. She did not comment on the ranking rule or teammate preferences; both are open and must be confirmed before Iteration 2 planning.

## Backlog changes

Added as a result of this iteration: an OR-Tools evaluation spike; a solver-proposed assignment feature; our own Auth0 tenant and removal of the client-side role hint; a role permission class and authentication on the semester and email endpoints; a hosting investigation, since the prior team's cloud deployment no longer exists.

## Late items

The following were not in the repo at the 9/24 deadline and were added 2026-10-06: this review, the retrospective, the presentation PDFs, and the `iteration-1-submission` tag. The tag therefore marks the state on 2026-10-06, not 2026-09-24.
