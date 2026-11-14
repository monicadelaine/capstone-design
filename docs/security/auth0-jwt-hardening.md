# Auth0 JWT hardening (Sprint 1)

**Repository:** `monicadelaine/capstone-design`  
**Scope:** `backend/user/authentication.py` only; no production changes.

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

## Next work
- Audit role and object-level permissions for attachments, feedback, and user endpoints.
- Audit token-management requirements and document the intended student invitation flow.
- Review media storage, database backup retention, restoration, and recovery objectives.

**Status:** patch prepared; CI and application tests not yet executed.
