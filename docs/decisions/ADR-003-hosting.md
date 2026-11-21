# ADR-003: Host on one Google Cloud VM with Docker Compose

**Status:** Accepted
**Date:** 2026-10-27 (recorded 2026-11-21 from PR #59 and the [deployment guide](../deployment-guide/README.md))
**Deciders:** Noland Miller, who built it; adopted by the team as the live site

## Context

The previous team's deployment was gone when this team started: its Google Cloud project and domain were under personal accounts. The application is three services (a built Vue app behind nginx, Django under gunicorn, PostgreSQL) that already run together under Docker Compose in development. Traffic is one class: under 100 users, with one busy day when rankings are due. Whoever inherits the site may not be a developer.

## Options considered

Recorded after the fact; these are the realistic alternatives for an application of this shape.

1. **One virtual machine running Docker Compose.** The same shape as development, and the shape the previous team's deployment had. Tradeoff: one machine to patch and back up, and a short outage on every deployment.
2. **A managed container service** (for example Cloud Run with a managed database). Tradeoff: no server to patch and automatic HTTPS, but three services, a database, and file storage each become a separately configured cloud resource, which is more to hand over and more ways for an account to lapse.
3. **A platform-as-a-service** (for example Render or Fly.io). Tradeoff: the least setup, but another vendor account to transfer, and free tiers that sleep or expire.

## Decision

Option 1: a single Google Cloud VM running `docker-compose.prod.yml`, with Caddy in front for HTTPS and a DuckDNS name. It matches the development stack service for service, so a problem on the server can be reproduced on a laptop, and the whole site can be rebuilt from the repository and three settings files.

## Consequences

- Deployment is a few commands on the VM, and is not automatic. See [operations](../deployment-guide/operations.md#deploy-a-new-version).
- Backups, the reminder schedule, and updates to the VM are the host's job; the [deployment guide](../deployment-guide/operations.md) gives the commands.
- Nothing ties the application to Google Cloud except the optional storage bucket ([ADR-005](ADR-005-file-storage.md)), so moving to another host means following [first deployment](../deployment-guide/first-deployment.md) there.
- The account that owns the VM and the domain has to be handed to the instructor. See the [FAQ](../faq/README.md#who-owns-each-account).
