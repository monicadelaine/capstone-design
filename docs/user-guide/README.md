# User Guide

**Audience:** students, sponsors, and the instructor.

**Status:** placeholder. Filled in as the corresponding work is delivered.

How to log in, submit a project, rank projects, and manage a semester. Written when the features are stable; until then see the v1 user guide in the prior team's repository for the inherited behaviour.

## Instructor: review submitted projects

When a sponsor submits a project it is Pending and students cannot see it. Review it in Django admin (`/admin/`).

1. Go to Projects and choose **Waiting for review** in the Review filter on the right. Each row shows the sponsor and the start of the description; click a project to read all of it.
2. Tick the projects you want to offer, choose **Approve for a semester** from the action menu, and click Go. Pick the semester (the current one is preselected) and confirm. Students in that semester can now see and rank them.
3. Tick the projects you do not want, choose **Reject**, and confirm. They are marked Cancelled and removed from every semester. Students never see them; the sponsor still sees the project, marked Cancelled.

A rejected project can be approved later, which restores it. A project cannot be rejected once students are assigned to it; reassign them first.

## Instructor: propose and approve assignments

Do this after the ranking deadline, in Django admin (`/admin/`).

1. Make sure the semester's projects are on the semester (Projects > select > "Assign to a semester"). Cancelled projects are skipped.
2. Go to Semesters, tick the one semester, choose **Propose assignments** from the action menu, and click Go.
3. Set the team size (default 4) and the minimum team size (default 4). If the number of students does not divide evenly by the team size, lower the minimum, for example to 3.
4. Review the proposal: each project with its students and the rank each student gave it. Students placed on a project they did not rank are shown in red. Projects with no team are listed under the table. Nothing has been saved yet.
5. Click **Approve and save assignments** to create the assignments, or **Discard** to leave everything as it was. Approving replaces the project for any student who already had an assignment that semester. A proposal expires after an hour; run it again if needed.

Only students who submitted preferences for the semester are included.
