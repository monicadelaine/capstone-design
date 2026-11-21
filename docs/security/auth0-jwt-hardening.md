# Auth0 JWT hardening (Sprint 1)

**Status:** merged in PR #98 on 2026-11-14, CI green. Part of the [security assessment](README.md).
**Scope:** `backend/user/authentication.py`.

## Finding
The existing authentication class allowed the JWT `alg` header to select the decoder algorithm and accepted JWTs without a `kid` by selecting the first published key. Both values originate from untrusted token input.

## Change
- Accept only `RS256`, including when invoking `jwt.decode`.
- Require a matching `kid` referencing a published RSA JWK.
- Return a generic API authentication error instead of leaking validator exception details.
- Add tests for unsupported algorithms, missing key IDs, accepted algorithm, and safe errors.

## Verification
From `backend/`, with dependencies and test environment variables configured:

```sh
pytest -q user/tests/test_authentication_security.py
pytest -q
python manage.py check --deploy
```

Review failures before deploying. `check --deploy` may produce expected deployment-specific warnings; evaluate rather than suppress them.

## Since then

The follow-up work listed when this change was made has been done:

- Role and object-level permissions for attachments, feedback, and user records: [attachment and feedback permissions](attachment-feedback-permissions.md) (PR #108) and [user records](user-records.md) (PR #99).
- Signing-key caching and rotation handling: [JWKS cache](jwks-cache-debug-panel.md) (PR #105).
- Media storage, database backup, and restore: [deployment guide](../deployment-guide/operations.md#back-up-the-database).
