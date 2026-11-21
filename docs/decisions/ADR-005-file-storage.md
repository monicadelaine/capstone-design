# ADR-005: Store uploads in Google Cloud Storage and serve them through Django

**Status:** Accepted
**Date:** 2026-11-11 (recorded 2026-11-21 from the [file hosting investigation](../investigations/file-hosting.md) and PRs #93 and #108)
**Deciders:** Jayden White (investigation and implementation); Noland Miller (permission rules)

## Context

Sponsors attach files to a project: pdf, docx, pptx, png, jpg, or zip, up to 25 MB. Students need to download them. The site runs on one VM whose containers are rebuilt on every deployment, so anything written inside a container is lost. Sponsor material should not be public.

## Options considered

Where files live:

1. **A folder or volume on the VM.** Tradeoff: free and simple, but the files are lost with the VM unless the disk is backed up.
2. **Google Cloud Storage.** Tradeoff: one bucket to create and permission, but it is in the same project as the VM, needs no key file there, and its free tier covers a class.
3. **Another object store** (Amazon S3, Cloudflare R2, Backblaze B2). Tradeoff: comparable cost, but a second vendor account to hand over.
4. **Self-hosted MinIO in production.** Tradeoff: it is what development uses, but the community edition was archived in April 2026 and no longer receives security updates.

How files are served:

1. **Django checks permission and streams the file.** Tradeoff: every download passes through a worker, but the bucket stays private and nothing needs to sign URLs.
2. **Django checks permission and redirects to a short-lived signed URL.** Tradeoff: downloads bypass the application, but signing needs extra service-account setup on the VM.
3. **A public bucket.** Ruled out: anyone with a link could read sponsor files.

## Decision

Google Cloud Storage in production, selected by setting `GS_BUCKET_NAME`, with downloads streamed through Django after a permission check. Development keeps MinIO so that no developer needs cloud credentials. Where the files are stored is decided in settings, not in the model.

Files are stored under a random name with the original name kept in the database, and are always sent as a download, never displayed in the page.

## Consequences

- **The bucket has to be configured.** Without `GS_BUCKET_NAME`, production falls back to a folder inside the container and uploads are lost on the next deployment. See [configuration](../deployment-guide/configuration.md#uploaded-files).
- At two gunicorn workers, a few simultaneous large downloads could tie the site up. Signed URLs (option 2) are the next step if that is ever observed.
- Replacing MinIO in development with local file storage is a [recommendation](../recommendations/README.md), not yet done.
- Files are checked by extension and size only. Content checks and virus scanning were considered out of proportion for the allowed types.
