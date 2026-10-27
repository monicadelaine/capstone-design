# User Guide

**Audience:** students, sponsors, and the instructor.

**Status:** placeholder. Filled in as the corresponding work is delivered.

How to log in, submit a project, rank projects, and manage a semester. Written when the features are stable; until then see the v1 user guide in the prior team's repository for the inherited behaviour.

## Instructor: propose and approve assignments

Do this after the ranking deadline, in Django admin (`/admin/`).

1. Make sure the semester's projects are on the semester (Projects > select > "Assign to a semester"). Cancelled projects are skipped.
2. Go to Semesters, tick the one semester, choose **Propose assignments** from the action menu, and click Go.
3. Set the team size (default 4) and the minimum team size (default 4). If the number of students does not divide evenly by the team size, lower the minimum, for example to 3.
4. Review the proposal: each project with its students and the rank each student gave it. Students placed on a project they did not rank are shown in red. Projects with no team are listed under the table. Nothing has been saved yet.
5. Click **Approve and save assignments** to create the assignments, or **Discard** to leave everything as it was. Approving replaces the project for any student who already had an assignment that semester. A proposal expires after an hour; run it again if needed.

Only students who submitted preferences for the semester are included.
