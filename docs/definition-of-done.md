# Definition of Done

**Audience:** the Fall 2026 team, Dr. Anderson, and the TA. Adapted from the course Definition of Done slide.

An Issue moves to **Done** on the project board only when every item below is true. This applies to every Issue type: feature, setup, test, documentation, and investigation. If an item does not apply, the pull request says so explicitly rather than leaving it blank.

## The checklist

1. **Acceptance criteria met.** Every bullet under the Issue's *Acceptance Criteria* is satisfied, and the Issue's *Completion Evidence* section links the pull request, commit, or file path that proves it. An Issue with no evidence link is not done.

2. **Changes merged.** The work is on `main`. Code changes get there through a pull request from a feature branch, with the PR template filled in, CI green, and one teammate's review. Documentation-only changes may be committed to `main` directly, as the README describes. Work that only exists on a branch or a laptop is not done.

3. **Tests pass.** The CI check on the pull request is green. New or changed behavior has automated test coverage where it can be tested, and a feature has at least one test that exercises it. If the way tests are run changes, `docs/testing/` is updated to match.

4. **Docs updated.** Any change to setup, user-facing behavior, deployment, or team process is reflected in `docs/` or the README in the same pull request. The PR's *Documentation* section names what changed, or says N/A.

5. **AI use disclosed.** The PR's *AI Assistance* section states what AI produced, what the team reviewed or changed, and how the result was verified. It says "No material AI assistance" when none was used. The same disclosure appears in the stand-up entry for that work.

6. **Demoable.** The result can be shown live from a fresh checkout of `main` on a teammate's machine. For a feature, that means walking through it in the running app. For a document, that means the rendered page reads correctly on GitHub.

## Common ways work looks done but is not

- The Issue was closed from the board without a linked pull request or evidence.
- Tests pass locally but the CI run on the pull request is red or was never triggered.
- Behavior changed but the documentation still describes the old behavior.
- The feature works only with data or configuration that exists on one person's machine.
