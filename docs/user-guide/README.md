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
2. Set the team sizes. Open the semester (Semesters > click it) and set **Team size** (the most students on a project, default 4) and **Minimum team size** (default 4). If the number of students does not divide evenly by the team size, lower the minimum, for example to 3. If one project needs a different maximum, open that project and set its **Max team size**; leave it blank to use the semester's.
3. Go to Semesters, tick the one semester, choose **Propose assignments** from the action menu, and click Go. If the sizes cannot work for the number of students, a message says so and nothing is proposed; change the sizes and try again.
4. Review the proposal: each project with its students and the rank each student gave it. Students placed on a project they did not rank are shown in red. A project with its own maximum is marked "up to N students". Projects with no team are listed under the table. Nothing has been saved yet.
5. To change a team, pick a different project in a student's **Move to** list. The page re-checks right away: the student's rank updates, moved students are highlighted, and any team that is now too big or too small is listed under **Fix these before approving**. Approve stays disabled until every team is within the size limits. Projects with no team are in the list too, so you can start a new team by moving students onto one.
6. Click **Approve and save assignments** to create the assignments, or **Discard** to leave everything as it was. Approving replaces the project for any student who already had an assignment that semester. What you approve is exactly what is on the page, including your moves. A proposal expires after an hour; run it again if needed.

Only students who submitted preferences for the semester are included.

**Approving publishes the assignments.** While you are only proposing or moving students, nothing is saved and nobody else can see it. The moment you approve, each assigned student can see their project, the sponsor's contact details and their teammates' names and emails, and each sponsor sees the students on their own projects, with their names and emails. Nobody sees another team. Assigning a student by hand from the Preferences list, without a proposal, shows them the same way right away.
