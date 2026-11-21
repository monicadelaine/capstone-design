# ADR-006: Build the instructor's tools in Django admin

**Status:** Accepted
**Date:** 2026-10-27 (recorded 2026-11-21 from PRs #65, #90, #95, #96, #97 and #101)
**Deciders:** Gaurav Shrivastava and Jayden White, who built the instructor tools

## Context

The instructor needs to review projects, import the roster, set team sizes, propose and adjust teams, approve them, and email sponsors. The previous version already had the instructor working in Django admin, and its Vue app had four admin dashboard buttons that linked to a route that did not exist. There is one instructor and occasionally a TA; there are dozens of students and sponsors.

## Options considered

1. **Django admin pages and actions.** Tradeoff: a plainer interface, but lists, filters, forms, permissions, and import/export come with the framework, so the work goes into the feature and its tests.
2. **An instructor dashboard in the Vue app.** Tradeoff: one consistent interface for all three roles, but every list, form, and permission check has to be built and tested twice, once in the API and once in the screen.

## Decision

Option 1. Each instructor tool is a Django admin action or page: project review (#67), the roster import (#66), team sizes (#68), the proposal page with moves and approval (#51, #69), the team-size comparison (#107), and sponsor emails with a preview (#73). Students and sponsors, who are many and need no training, use the Vue app.

## Consequences

- The instructor logs in with a Django staff account, not through Auth0. Access is controlled with Django's per-model permissions, and each action checks the permission it needs.
- There are two login systems to explain. [Architecture](../development-guide/architecture.md) and the [security assessment](../security/README.md#who-is-who) both describe them.
- Instructor features are tested through the admin's own views, with no browser automation needed.
- A Vue dashboard remains possible later: the project review endpoints already exist in the API. It is listed in the [recommendations](../recommendations/README.md) as something to build only if the sponsor asks.
