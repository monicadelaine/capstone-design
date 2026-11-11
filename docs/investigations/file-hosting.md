# File Hosting for Project Attachments (PBI-12, #72)

**Date:** 2026-11-09 · **Author:** Jayden White · **Related:** #72 (PBI-12), #57 (SECURITY-02), stand-up #91
**Question:** Where should sponsor-uploaded project files (pdf, docx, pptx, png, jpg, zip, up to 25 MB) live, and how should students download them, given a single GCP VM running Docker Compose and a Django backend?
**Answer (draft):** Use Google Cloud Storage in production, because the settings and the GCP project already point at it, and keep downloads behind a Django permission check that hands out short-lived signed URLs. Four things in the code had to change first. Three are now fixed on `feature/file-submission-support`: the model hard-wired an S3 backend (`5abde52`), nginx rejected uploads over 1 MB (`client_max_body_size 30m`, `d298d13`), and a second upload with the same filename overwrote the first (random stored names, `0704251`). Downloads are also now always attachments with a safely built filename header (`bfe375d`). One remains: any logged-in user can read or delete any attachment (#57). MinIO should not be used beyond local development.
**Status:** draft, updated 2026-11-11 for the model, nginx, file-name and download-header fixes. Marked **TODO** where a fact could not be checked from the repository (the production environment is not in the repo). Figures marked *verify* come from third-party pages, not the provider.

## What exists today

| Area | Finding | Where |
|---|---|---|
| Model | **Fixed (`5abde52`).** `Attachment.file` had an explicit `storage=S3MediaStorage()`, which ignores the `STORAGES` default, so the Google Cloud Storage block in production settings was never used for attachments, and production has no MinIO or AWS credentials. The explicit storage is removed (state-only migration 0023). Tests cover the field using `default_storage`, a save and delete round trip, and the backend each environment resolves to. Not tested against a real bucket or MinIO. | `backend/project/models.py`, `backend/project/storage.py` |
| Settings | A GCS block exists: `GoogleCloudStorage`, bucket from `GS_BUCKET_NAME`, project `capstone-design-fall-2026`, `querystring_auth=True` (private files, signed URLs). `django-storages[google]` is installed. `DEFAULT_FILE_STORAGE` and `STATICFILES_STORAGE` are not Django settings in 5.2 (checked), so they did nothing; `STORAGES` is now declared for every environment: MinIO in development, GCS in production when `GS_BUCKET_NAME` is set, otherwise local `MEDIA_ROOT` (lost when the container is rebuilt). | `backend/core/settings.py`, `backend/requirements.txt` |
| Dev storage | MinIO, pinned to `RELEASE.2025-09-07` images from quay.io. | `docker-compose.dev.yml` |
| Download | `AttachmentDownloadAPIView` opens the file from storage and streams it through Django. It was displayed inline (`as_attachment=False`); it is now always a download. The admin download view built its header by hand, which a filename containing a quote could break, and rendered some uploaded types inline; both fixed. The download name is the original filename (`Attachment.original_filename`). Gunicorn runs 2 workers with a 60 s timeout. Any authenticated user can download any attachment. | `backend/project/views.py`, `backend/gunicorn.conf.py` |
| Permissions | `AttachmentViewSet` uses only `IsAuthenticated`. A student could create or delete any attachment. #72 requires the owning sponsor and admins only; it depends on #57. | `backend/project/views.py` |
| Upload size | **Fixed.** The nginx config had no `client_max_body_size`, so nginx's default of 1 MB applied. Tested with real nginx in front of a stub backend: the old config returned 413 for 5, 24 and 26 MB bodies; with `client_max_body_size 30m` they all reach the backend and a 31 MB body is still refused. The 25 MB limit itself stays with Django. The VM also has Caddy in front of this nginx (response header `via: 1.1 Caddy`), which only limits request size if `request_body { max_size }` is configured; its Caddyfile is not in the repo. **TODO:** check the Caddyfile on the VM. | `frontend/nginx.conf` |
| Validation | Extension allowlist and a 25 MB check only. No content check, no virus scan. | `backend/project/models.py` |
| File names | **Fixed (`0704251`).** Files were stored as `<project id>/<original filename>`, and django-storages overwrites an existing object of the same name by default for both S3 and GCS (checked), so a second upload with the same name silently replaced the first. Files are now stored as `<project id>/<random hex>.<extension>`, and the uploaded name is kept in `Attachment.original_filename` (migration 0024, read-only in the API) and used for downloads. Tests run against a storage that overwrites like S3 and GCS, since Django's own in-memory storage renames on a collision and hid the problem; four of them fail on the old naming. Existing files keep their old names (none in the dev database; production unknown). | `attachment_upload_path`, `backend/project/models.py`, `backend/project/tests/storages.py` |
| Frontend | No attachment UI exists. | `frontend/src` |

## Requirements

From #72: upload pdf, docx, pptx, png, jpg, zip up to 25 MB; students see and download files (and links) from the project page; only the owning sponsor and admins add or delete. Also needed: private storage, no data loss when the VM is rebuilt, a developer setup that runs without cloud credentials, and a cost near zero for a class project.

## Options

| Option | Fit with our code | Cost (official pages unless marked) | Notes |
|---|---|---|---|
| **A. Docker volume on the VM** | Django `FileSystemStorage`; no new service | Free; uses VM disk | Files are lost with the VM unless the disk is backed up. Serving is done by Django or nginx on the one VM. Simplest, and weakest for durability. |
| **B. Google Cloud Storage** | Already in settings; same project as the VM | Free Tier: 5 GB-months of regional storage in `us-east1`, `us-west1` or `us-central1` only, 5,000 Class A and 50,000 Class B operations, 100 GB North America egress per month; Google can change this with 30 days' notice | Signed URLs need extra setup (see below). Bucket must be in one of the three free US regions. |
| **C. Amazon S3** | `boto3` and an S3 backend already in the code | New accounts get up to $200 in credits and a 6-month free plan; first 100 GB per month of internet egress free; storage rate *verify* (about $0.023 per GB-month) | A second cloud account to manage for no benefit over B. |
| **D. Cloudflare R2** | S3-compatible: the existing S3 backend can point at it with `endpoint_url`, but `S3MediaStorage` currently forces a MinIO-style custom domain, so it needs changes | 10 GB-month, 1M Class A and 10M Class B operations free; then $0.015 per GB-month; no egress fees | Least change to the code. A new vendor account. |
| **E. Backblaze B2** | S3-compatible API *verify* | $6.95 per TB-month; first 10 GB free; egress free up to 3x stored data, then $0.01 per GB; Class A, B and C calls free | Cheap; another vendor account. |
| **F. Self-hosted MinIO** | What dev uses today | Free, AGPLv3 | The community edition is archived, source-only, and no longer maintained (repository archived 2026-04-25). Pinned 2025 images get no security updates. Not for production. |
| **G. Links only** | `Attachment.link` already exists | Free | No upload to host; links break, and students may not have access to a sponsor's Drive or OneDrive. Useful as a complement to a hosted file, not a replacement. |

## How files are served

1. **Django streams the file** (today). Permission is checked on every request, but each download holds one of two workers.
2. **Django checks permission, then redirects to a short-lived signed URL** (recommended). The browser downloads straight from the bucket; the app never carries the bytes. `GS_EXPIRATION` defaults to one day, and v4 signing allows at most 7 days, so set it to minutes.
3. A public bucket is ruled out: it exposes sponsor material to anyone with the link.

Signed URLs with Google Cloud Storage need a service account that can sign. django-storages states that the default Compute Engine service account cannot sign URLs. Options: set `GS_IAM_SIGN_BLOB=True` so signing goes through the IAM SignBlob API using the VM's attached service account (needs the "Service Account Token Creator" role on a dedicated service account; the API has quotas), or mount a key file, which Google discourages. Option 1 avoids storing a key on the VM.

Uploads can stay on the current path (browser to Django to bucket): at 25 MB it needs the nginx limit raised to about 30 MB (done) and a gunicorn timeout that fits the request (60 s today). nginx buffers the whole request body before passing it on, so a slow connection ties up nginx and not a gunicorn worker. Uploading directly to the bucket with a signed upload URL would remove that load but needs bucket CORS rules and a confirmation step, which is more than this feature needs.

## Security practices (OWASP File Upload Cheat Sheet)

| Practice | Today |
|---|---|
| Extension allowlist | Done. |
| Do not trust the client `Content-Type`; check the file signature too | Missing. |
| Generate the stored file name server-side | Done: a random hex name under the project, with only the lowercased extension kept; the original name is stored in the database. |
| Size limits | 25 MB in the serializer and model; nginx allows 30 MB. Caddy's limit **TODO**. |
| Store outside the web root, authenticate every access | Private bucket: yes. Authorization: any logged-in user (#57). |
| Antivirus or sandbox scan | Missing. A small project may reasonably accept this risk for an allowlisted set of types; zip is the highest-risk type on our list (OWASP advises avoiding zip uploads). |
| Serve safely | Done (`bfe375d`): uploaded files are always sent as `Content-Disposition: attachment`, by both the API and the admin download views, with a correctly quoted filename (Django's `content_disposition_header`). `X-Content-Type-Options: nosniff` was already on every response through Django's `SecurityMiddleware` (`SECURE_CONTENT_TYPE_NOSNIFF` defaults to on; checked), so an earlier version of this table was wrong to list it as missing. Trade-off: PDFs and images no longer open in the browser tab; the user downloads them. (Not covered by the OWASP page fetched; standard practice.) |

## Size and cost

Assumption, to confirm with the sponsor: about 40 projects per semester, up to 3 files each, typically 5 MB and never above 25 MB. That is roughly 600 MB typical and 3 GB worst case per semester, with downloads by a few dozen students. Typical use (about 600 MB per semester, kept forever) would take roughly eight semesters to reach B's 5 GB free storage, and D and E have 10 GB; the worst case (3 GB per semester) reaches B's limit in under two. Beyond the free tier, storage at these sizes costs a few cents per month at standard rates (*verify*).

## Recommendation (draft)

1. **Production: Google Cloud Storage with signed URLs** (`GS_IAM_SIGN_BLOB`, dedicated service account, bucket in a free US region, short expiry).
2. **Fix the model**: **done** in `5abde52` (explicit storage removed, `STORAGES` declared per environment, migration 0023, tests).
3. **Development**: either keep MinIO temporarily, or drop it and use `FileSystemStorage` locally (nothing to pull, no archived software). **TODO:** decide with the team.
4. **Before shipping the feature**: nginx `client_max_body_size` (**done**, 30 MB; confirm Caddy), owner-or-admin permissions on `AttachmentViewSet` (after #57), non-overwriting object names (**done**, random names with the original kept in the database), `Content-Disposition: attachment` (**done**; `nosniff` was already global).
5. **Defer**: virus scanning and direct-to-bucket uploads, unless the sponsor asks.

## Open questions

- Who owns the GCP project and billing after the semester, and is `capstone-design-fall-2026` the project to keep?
- Does the production VM already have a bucket and a `GS_BUCKET_NAME`? If not, uploads would be written to container disk. Does the Caddyfile set a request body limit? **TODO:** check the VM, since the production env file and the Caddyfile are not in the repository.
- How long are files kept, and are sponsor files confidential beyond the course?
- Should students be able to download files from every project, or only after assignment?

## Sources

- Google Cloud Free Tier limits: https://docs.cloud.google.com/free/docs/free-cloud-features
- Cloudflare R2 pricing: https://developers.cloudflare.com/r2/pricing/
- Backblaze B2 pricing: https://www.backblaze.com/cloud-storage/pricing
- Amazon S3 pricing: https://aws.amazon.com/s3/pricing/
- MinIO repository status (archived, source-only, AGPLv3): https://github.com/minio/minio
- django-storages, Google Cloud Storage backend (signed URLs, IAM SignBlob): https://django-storages.readthedocs.io/en/1.14.6/backends/gcloud.html
- OWASP File Upload Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
- Caddy `request_body` directive (a limit applies only when `max_size` is set): https://caddyserver.com/docs/caddyfile/directives/request_body

Drafted with Claude Code (first draft), Fact-checking, research, and formatting done my me.
