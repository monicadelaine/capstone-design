# Iteration 3 Retrospective

**Date:** 2026-11-21
**Format:** Keep / Problem / Change / Action

> **Draft.** The facts below are from the repository record. The Keep, Problem and Change points combine that record with the lessons the team presented on 11/20 (slides 9 and 12). They are one teammate's reading until the other three have added to or changed them. This is the last iteration, so the actions are handoff actions.

## Iteration 2 actions: did we do them?

| Action | Owner | Result |
|---|---|---|
| Iteration 3 Issues assigned and on the board by the first stand-up | team | **Late.** The first stand-up was 10/28. The plan was approved and owners assigned on 11/10, two weeks in. Earlier than Iteration 2, which was planned five days before its deadline |
| Review PR #55 and comment on #43 / #49 | Noland, Gaurav | **Not done.** PR #55 has no review or comment |
| Post "runs on mine" on #12 so it can close | all | **Not done.** No comment on #12 since 9/22; it is still open |
| Sponsor answers on the ranking rule and teammate preferences, in person if email stays unanswered | Margulan | **Not done.** #81 has no answers recorded |
| Every teammate logged in on the new Auth0 tenant; sponsor invited (#45) | all; Margulan | **Not recorded.** #45 is open with no teammate confirmations |

None of the five was completed. Four of them were small, and each was owned. That is the first thing to change.

## Keep

- **Small, tested pull requests.** 14 merged in three and a half weeks, CI green on `main` throughout, backend tests from 258 to 469.
- **Proving a test catches the bug.** New tests are run against the old code first.
- **Reviews that find real things.** Jayden's reviews of #95 to #97 led to follow-up PR #106; Noland's review of #113 corrected how the guide described #77.
- **Building the setting, not the assumption.** With the sponsor's questions unanswered, team size became a semester setting and the proposal became editable, so neither answer blocks the product.
- **Asking who may see or change the data in every feature PR.** The attachment, feedback and roster rules all arrived with tests.
- **Stand-ups as Issues.** Eleven in the window, all four members on seven of them. Iteration 2 had gaps of two weeks.

## Problem

- **The plan was two weeks late again**, and most features merged between 11/12 and 11/20. Four pull requests merged on the last day.
- **Seven of the 19 committed Issues were open at the tag**, and the slides reported all 19 as delivered, along with an end-to-end test that does not exist. What we told the instructor and what the repository shows should be the same thing.
- **Deployment did not move.** The live site ran a build from 10/27 for the whole iteration. #52, #58 and #83 had no activity until the day of the review. Nothing we built this iteration has run on the server.
- **The handoff documents were written in the last two days**, by one person, and are unreviewed. Two of them were drafted by someone other than the owner because the Issues had not been started.
- **Half the pull requests were merged by their own author** without a review (7 of 14).
- **Work was uneven.** One member held 8 of the 19 committed items. The plan itself noted this on 11/10 and asked for a rebalance, which did not happen.
- **The sponsor's three questions were never answered.** They were first asked on 9/22 and carried through all three iterations.
- **Retrospective actions were not followed.** See the table above.
- **Writing the security assessment found two defects** that had been in the code since the start of the semester. Nobody had probed the API as an outsider until the last day.

## Change

What we would do differently, for a team starting from here:

- Plan the iteration before its first stand-up, and put a date on the plan. This is the second retrospective to say so.
- Check last retrospective's actions at the first stand-up of the next iteration, by name, not at the next retrospective.
- Report progress from the board: an Issue is done when it is closed. Slides are built from the same list.
- Deploy every time `main` changes. A site that is three weeks behind cannot be demonstrated or tested.
- No self-merges. A pull request open more than two days gets a named reviewer at stand-up, as Iteration 2 already agreed.
- Start each document when its feature merges, not at the end.
- Ask the sponsor in person, in the first week, and write the answer on the Issue.

## Action

This is the final iteration. These are the actions needed for the handoff to be real. Owners follow the Issue assignments; **owners and dates are proposed and need each person's agreement.**

| Action | Owner | Due | Evidence it is done |
|---|---|---|---|
| Review and merge the two security fixes, #116 and #118 | any teammate other than the author | to set | Merged |
| Review and merge the handoff documents: #113, #115, #117, #119, #120 | Noland (#115, #117), Margulan (#119, #120), Jayden (#113) | to set | Merged; `to confirm` rows filled in |
| Redeploy the live site from `main` on the team Auth0 tenant, following the deployment guide, and note what the guide got wrong | Noland, with one other teammate doing the typing | to set | #58 and #83 closed; `/api/v1/health/` and a login checked |
| Record who owns the Google Cloud project, the domain, the Auth0 tenant and the mail account, and add the sponsor to each | Noland, Margulan | to set | The account table in the FAQ has no `to confirm` rows |
| Turn on a nightly database backup and configure the storage bucket | Noland | to set | A dated backup file; an upload survives a redeploy |
| Ask the sponsor the three questions in #81 and record the answers | Margulan | to set | #81 closed |
| Each teammate logs in on the team tenant and posts on #45 and #12 | all | to set | Both closed |
| Decide #107 (PR #114): merge it or hand it off | team | to set | Merged or labelled for handoff |
| Write the end-to-end semester test (#80), or hand it off as open | to assign | to set | Test in CI, or the Issue says it is handed off |
| Correct the plan-versus-actual numbers with the instructor | team | to set | A note to the instructor, or an updated slide |
