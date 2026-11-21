# Auth0 JWKS cache and removal of DEBUG overlay (SECURITY-04 #78)

**Status:** merged in PR #105 on 2026-11-17, closing #78. Part of the [security assessment](README.md).

## Backend
- Cache Auth0's published public signing keys for five minutes using Django's cache.
- Validate the header algorithm and key ID before consulting the remote JWKS endpoint.
- On a missing key ID, refresh the JWKS once, with a 30-second cooldown to limit attacker-triggered fetches.
- Preserve RS256-only decoding and validation of audience and issuer. Fail closed if a matching RSA key is unavailable.
- Do not cache bearer tokens or private keys.

## Frontend
- Remove the on-screen DEBUG overlay and toggle from `frontend/src/App.vue`.
  The overlay previously rendered the Auth0 user object and roles.

## Verification
- `python -m pytest -q user/tests/test_authentication_security.py` from `backend/`
- `python -m pytest -q` from `backend/`
- `npm test -- --run` from `frontend/`
- `git diff --check` and verify the PR file list

## Deployment caveat
The repository does not configure a shared Django cache by default. Django's
local-memory cache works per application process, so different gunicorn workers
may each fetch JWKS once every five minutes. For cross-process caching, configure
an external cache backend (for example Redis) in deployment settings.
A real Auth0 signing-key rotation should be verified in a staging environment.
An unrecognized key may take up to 30 seconds to become accepted during the
refresh cooldown. This is a deliberate balance against repeated network requests.
