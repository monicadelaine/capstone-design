# ADR-004: Assign teams with a constraint solver, and do not store proposals

**Status:** Accepted
**Date:** 2026-10-27 (recorded 2026-11-21 from PRs #65, #95, #97 and #114)
**Deciders:** Gaurav Shrivastava (implementation), Margulan Baizhakyp (the [OR-Tools evaluation](../investigations/or-tools-evaluation.md)); the approach follows the sponsor's request to treat assignment as a constraint problem

## Context

The previous version had no matching: the instructor assigned each student by hand in Django admin. The sponsor asked for assignment to be solved as a constraint problem with OR-Tools, and for the instructor to review and edit the result before it becomes final. Team size, the ranking rule, and teammate requests were open questions when the work started.

Two decisions were needed: how to compute an assignment, and where a proposal lives between "the solver produced it" and "the instructor approved it".

## Options considered

How to compute it:

1. **Google OR-Tools CP-SAT.** Tradeoff: a large dependency, but it proves its answer is the best one, solves 200 students in well under a second, and takes new rules as constraints.
2. **A hand-written algorithm** (greedy, or a stable-matching variant). Tradeoff: no dependency, but no guarantee of the best answer, and each new rule (team size ranges, per-project limits, fairness) becomes new code paths.

Where a proposal lives:

1. **A status column on `Assignment`, or a separate proposal table.** Tradeoff: a proposal can be reopened later, but it needs a migration, cleanup of abandoned proposals, and care that students never see unapproved rows.
2. **Nowhere in the database.** The proposal page carries the proposal in a signed token; approving verifies the signature and writes the rows. Tradeoff: no schema change and nothing to clean up, but a proposal expires after an hour.

## Decision

CP-SAT for the computation, and a signed token for the proposal.

The solver gives every student exactly one project, keeps each team within the size limits, and minimises a cost based on each student's ranking. Proposals are signed with Django's signing framework, so they cannot be altered between review and approval, and approval is the only step that writes `Assignment` rows. Proposing again takes seconds, which makes the one-hour limit acceptable.

Where the sponsor's answers were open, the choice became a setting: team size and its minimum are set on the semester with an optional per-project maximum (#68), the instructor can move students before approving (#69), and a fairness limit and a side-by-side comparison of team sizes are optional (#107).

## Consequences

- Students and sponsors can never see an unapproved assignment, because none exists in the database.
- A proposal left open for more than an hour, or made before `SECRET_KEY` changes, has to be proposed again.
- Teammate requests (#75) would be added as "same project" and "different project" constraints; the solver supports both directly. The work is in the data model and the ranking form.
- The cost weights (first choice 0, second 1, third 3, unranked 10) are a judgment and live in one place, `backend/project/assignment.py`.
- The backend image is large, about 840 MB, mostly this library.
