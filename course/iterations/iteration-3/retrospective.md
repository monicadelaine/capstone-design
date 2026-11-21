# Iteration 3 Retrospective

**Date:** 2026-11-21
**Format:** Keep / Learned / Action

> Written from the repository record and the lessons the team presented on 11/20. This is the final iteration, so the actions are handoff actions.

## Building on Iteration 2

| What Iteration 2's retrospective raised | What happened in Iteration 3 |
|---|---|
| Plan the iteration earlier | The plan was approved with owners on 11/10, with two and a half weeks of the iteration ahead of it. Iteration 2 was planned five days before its deadline |
| Get pull requests reviewed promptly | #86, #90 and #93 were each reviewed and merged by a teammate. Reviews of #95 to #97 led to follow-up PR #106, and the review of #113 improved the guide |
| An Issue closes only when its PR merges | Followed: every Issue closed this iteration was closed by its merged pull request |
| Hold stand-ups without gaps | Eleven stand-up Issues in three and a half weeks, up from five |
| Move the team to its own Auth0 tenant | The team tenant is live and is the one every development setup and env template uses |

The remaining Iteration 2 items (sponsor answers, teammates' sign-offs on #12 and #45) are in the handoff actions below.

## Keep

- **Small, tested pull requests.** 23 merged in the iteration with CI green on `main` throughout. Backend tests went from 258 to 496 and frontend tests from 28 to 75.
- **Proving a test catches the bug.** New tests are run against the old code first.
- **Reviews that find real things.** Follow-up PR #106 came straight out of review, and so did the correction to the development guide.
- **Building the setting, not the assumption.** Team size became a semester setting and the proposal became editable, so open questions never blocked the product.
- **Security travels with the feature.** Every feature PR asks who may see or change the data, and the attachment, feedback and roster rules all arrived with tests.
- **Finishing with an assessment.** Checking every API endpoint as each kind of user confirmed the access rules and surfaced two issues, both fixed and merged with tests the same day.
- **Documentation that was run, not just written.** The deployment guide was rehearsed against the production stack, including a backup and restore, and the development guide's worked example was built and tested before it was written up.
- **Clear ownership by area.** Student and sponsor features, the instructor and solver flow, security and deployment, and planning and access each had one owner, and each area shipped.

## Learned

Lessons the team would carry into its next project:

- **Plan early.** This iteration's plan came earlier than the last one, and more got done. The next step is a plan before the first stand-up.
- **Deploy continuously.** Features reach users fastest when every merge to `main` goes to the live site. The deployment guide now makes that a short, repeatable procedure.
- **Write each document alongside its feature.** The handoff set came together quickly at the end because the investigations and decision records had been written along the way.
- **Keep formal approvals as the habit.** Reviews caught real issues every time they were used.
- **Ask the sponsor in person, early.** Building settings kept the work moving; a direct answer in the first week would save the next team even that step.
- **Run CI on PostgreSQL** to match production.

## Action

Handoff actions, following the Issue assignments. Owners and dates to be confirmed by each person.

| Action | Owner | Evidence it is done |
|---|---|---|
| Redeploy the live site from `main` on the team Auth0 tenant, following the deployment guide | Noland, with a teammate | #58 and #83 closed; health check and a login confirmed |
| Record who owns the Google Cloud project, the domain, the Auth0 tenant and the mail account, and add the sponsor to each | Noland, Margulan | The account table in the FAQ is complete |
| Turn on the nightly database backup and the storage bucket | Noland | A dated backup file; an upload survives a redeploy |
| Record the sponsor's answers to the three questions in #81 | Margulan | #81 closed |
| Each teammate confirms a login on the team tenant on #45 and #12 | all | Both closed |
| Verify the FAQ answers and close #110 | Margulan | #110 closed |
| Hand off the backlog (#74, #75, #76, #79, #80) with the recommendations page | team | Issues labelled for handoff |
