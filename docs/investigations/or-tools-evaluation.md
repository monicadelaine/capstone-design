# OR-Tools CP-SAT Evaluation (SPIKE-03, #44)

**Date:** 2026-10-25 · **Author:** Margulan Baizhakyp · **Timebox:** one day
**Question:** Can Google OR-Tools CP-SAT propose student-project assignments for the admin to approve, as the sponsor asked on 9/22?
**Answer:** Yes. Recommend proceeding with OR-Tools for the proposed-assignment feature (#51).

## What was built

`docs/investigations/or-tools/assign.py`, a standalone script (no Django) that generates sample ranked preferences, solves the assignment, and prints the result. It includes a self-check that runs first: a tiny case with a known optimum and an infeasible case that must raise an error.

```
pip install ortools
python docs/investigations/or-tools/assign.py          # 20 students, 5 projects
python docs/investigations/or-tools/assign.py 100 25   # a full cohort
```

## Constraint model

| Part | Definition |
|---|---|
| Variables | One yes/no variable per student-project pair: "student s is on project p" |
| Each student | Exactly one project |
| Each project | Exactly 4 students (team size) |
| Objective | Minimise total cost: first choice 0, second 1, third 3, unranked 10 |

The cost weights are a judgment call. Making "unranked" expensive means the solver only puts a student on a project they did not rank when there is no other way to fill every team.

## Results

Sample data is skewed toward a few popular projects, which is the hard case. Run on a MacBook, OR-Tools 9.15, 8 workers.

| Students / projects | Status | Solve time | 1st choice | 2nd | 3rd | Unranked |
|---|---|---|---|---|---|---|
| 20 / 5 | Optimal | 0.006 s | 16 | 3 | 1 | 0 |
| 100 / 25 | Optimal | 0.07 s | 62 | 22 | 9 | 7 |
| 200 / 50 | Optimal | 0.3 s | 130 | 43 | 11 | 16 |

"Optimal" means the solver proved no better assignment exists, out of roughly 10^123 possible ones for 100 students. Speed is not a concern at our size.

## Mapping onto our models

- **Input:** `Preference` rows for the semester (student, project, rank 1 to 3). `Project` rows that are active this semester.
- **Output:** one `Assignment` row per student (semester, student, project). The `Assignment` id is built from student and semester, so the database already enforces one project per student per semester.
- **Approval:** the solver should write a proposal, not `Assignment` rows directly. The admin reviews and edits, then approves, and only approval creates the rows. That needs either a status on `Assignment` or a separate proposal table. To decide in #51.
- **Where it runs:** a Django management command or an admin-only endpoint. A cohort solves in under a second, so a normal request is fine. No background worker needed.

## What the real feature needs from the sponsor

| Input | Current state | Effect on the model |
|---|---|---|
| Ranking rule | Model stores top 3; sponsor not yet answered | With only 3 ranks and popular projects, 7 of 100 students got an unranked project. Ranking more projects (or all) gives the solver more room. |
| Teammate requests or avoids | Not in the data model; sponsor not yet answered | Adds "same project" or "different project" constraints. CP-SAT handles these directly. |
| Team size | Assumed 4 from her example | One number per project; could vary per project with a new `Project` field. |
| Uneven numbers | Not handled | If students do not divide evenly by 4, project capacity must be a range (for example 3 to 5) instead of exactly 4. Otherwise the solver reports no solution. |

## Risks

- **Dependency size:** the `ortools` wheel is large (about 25 MB). Acceptable for the backend image.
- **Infeasible input:** too few project seats makes the model unsolvable. The script raises an error instead of returning a partial answer. The feature must show the admin a clear message.
- **Fairness:** minimising total cost can leave one student much worse off than everyone else. If the sponsor cares, add a cap on the worst rank any student gets.

## Recommendation

Proceed with OR-Tools CP-SAT for #51. Before #51 starts, get the sponsor's answers on the ranking rule and teammate preferences, and decide how proposals are stored before approval.
