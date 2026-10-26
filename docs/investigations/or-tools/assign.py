"""SPIKE-03 (#44): assign students to projects with OR-Tools CP-SAT.

Standalone: pip install ortools; python assign.py [students] [projects]
Defaults to the issue's case, 20 students and 5 projects of 4.

Input mirrors our Preference model: each student ranks up to 3 projects (1 = first choice).
Cost: rank 1 -> 0, rank 2 -> 1, rank 3 -> 3, unranked -> 10. Minimised in total.
"""
import random
import sys
import time

from ortools.sat.python import cp_model

COST = {1: 0, 2: 1, 3: 3}
UNRANKED = 10


def sample(n_students, n_projects, seed=495):
    """Ranked preferences skewed toward a few popular projects, like real cohorts."""
    rng = random.Random(seed)
    weights = [n_projects - p for p in range(n_projects)]
    prefs = {}
    for s in range(n_students):
        picks = []
        while len(picks) < 3:
            p = rng.choices(range(n_projects), weights)[0]
            if p not in picks:
                picks.append(p)
        prefs[s] = {p: r + 1 for r, p in enumerate(picks)}
    return prefs


def solve(prefs, n_projects, team_size=4, time_limit=10.0):
    m = cp_model.CpModel()
    students = list(prefs)
    x = {(s, p): m.NewBoolVar(f"x{s}_{p}") for s in students for p in range(n_projects)}
    for s in students:  # every student gets exactly one project
        m.AddExactlyOne(x[s, p] for p in range(n_projects))
    for p in range(n_projects):  # every project gets exactly team_size students
        m.Add(sum(x[s, p] for s in students) == team_size)
    m.Minimize(sum(COST.get(prefs[s].get(p), UNRANKED) * x[s, p] for s in students for p in range(n_projects)))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 8
    t = time.perf_counter()
    status = solver.Solve(m)
    elapsed = time.perf_counter() - t
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"no assignment: {solver.StatusName(status)}")
    result = {s: p for (s, p), v in x.items() if solver.Value(v)}
    return result, solver.StatusName(status), elapsed, int(solver.ObjectiveValue())


def report(prefs, result, n_projects, status, elapsed, cost):
    got = {}
    for s, p in result.items():
        got[prefs[s].get(p, "unranked")] = got.get(prefs[s].get(p, "unranked"), 0) + 1
    print(f"{len(prefs)} students, {n_projects} projects: {status} in {elapsed:.3f}s, total cost {cost}")
    for k in (1, 2, 3, "unranked"):
        print(f"  choice {k}: {got.get(k, 0)}")


def check():
    # Tiny case with a known optimum: two students both want project 0 first.
    prefs = {0: {0: 1, 1: 2}, 1: {0: 1, 1: 2}, 2: {1: 1}, 3: {1: 1}}
    result, status, _, cost = solve(prefs, 2, team_size=2)
    assert status == "OPTIMAL" and cost == 0, (status, cost)
    assert sorted(result.values()) == [0, 0, 1, 1]
    # Infeasible capacity must raise, not return a partial answer.
    try:
        solve({0: {0: 1}}, 1, team_size=2)
        raise AssertionError("expected infeasible")
    except RuntimeError:
        pass


if __name__ == "__main__":
    check()
    n_s = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    n_p = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    prefs = sample(n_s, n_p)
    result, status, elapsed, cost = solve(prefs, n_p)
    report(prefs, result, n_p, status, elapsed, cost)
    if n_s <= 20:
        for p in range(n_p):
            team = [s for s, q in result.items() if q == p]
            print(f"  project {p}: " + ", ".join(f"s{s}(rank {prefs[s].get(p, '-')})" for s in team))
