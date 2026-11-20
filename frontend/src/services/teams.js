// Groups assignments by project for the sponsor dashboard (#71). The API sends each assignment with the
// student's name and email (student_detail), and only for projects this sponsor owns.
const byName = (a, b) =>
  (a.last_name || '').localeCompare(b.last_name || '') || (a.first_name || '').localeCompare(b.first_name || '')

// { projectId: [{ id, first_name, last_name, email }, ...] } with each team sorted by last name.
export function studentsByProject(assignments) {
  const grouped = {}
  for (const assignment of Array.isArray(assignments) ? assignments : []) {
    const student = assignment.student_detail
    if (!student) continue
    const project = assignment.project && typeof assignment.project === 'object' ? assignment.project.id : assignment.project
    if (!grouped[project]) grouped[project] = []
    grouped[project].push(student)
  }
  for (const team of Object.values(grouped)) team.sort(byName)
  return grouped
}
