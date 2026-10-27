# Auth0 Tenant Setup (SETUP-06, #45)

How to create the team-owned Auth0 tenant that replaces the Spring 2026 team's tenant, per [ADR-002](../decisions/ADR-002-auth.md). One person does steps 1 to 6 once. Everyone does step 7.

## Before you start

The code reads two custom token claims with a fixed prefix: `https://backend-api-capstone/email` and `https://backend-api-capstone/roles` (`backend/user/authentication.py`, `frontend/src/router/index.js`, and others). Use that exact string as the API identifier below so no code changes are needed.

## Steps

1. **Create the tenant.** Sign up at auth0.com with a team-owned account. Region US. Name it something like `capstone-design-f26`. Development environment is fine.
2. **Create the API.** Applications > APIs > Create API.
   - Name: `Capstone Design Manager API`
   - Identifier: `https://backend-api-capstone/` (exactly, with the trailing slash)
   - Signing algorithm: RS256
3. **Create the application.** Applications > Applications > Create Application > Single Page Web Application.
   - Allowed Callback URLs: `http://localhost:5173`
   - Allowed Logout URLs: `http://localhost:5173`
   - Allowed Web Origins: `http://localhost:5173`
   - Save. Copy the **Domain** and **Client ID**.
   - Then open Applications > APIs > Capstone Design Manager API > **Application Access** and authorize this application for **User Access**. New tenants block it by default, and login fails with "Client ... is not authorized to access resource server".
4. **Add the claims Action.** Actions > Library > Create Action > Build from scratch. Trigger: Login / Post Login. Paste the code below, Deploy, then add it to the Post Login flow under Actions > Triggers.

   ```js
   // Interim until #43 moves roles into our database (ADR-002).
   // Roles come only from Auth0 role assignment or the email domain, never from the client.
   exports.onExecutePostLogin = async (event, api) => {
     const ns = 'https://backend-api-capstone/';
     const email = event.user.email || '';
     if (!event.user.email_verified) {
       return api.access.deny('Please verify your email before logging in.');
     }
     let roles = event.authorization?.roles || [];
     if (roles.length === 0) {
       roles = [email.toLowerCase().endsWith('@crimson.ua.edu') ? 'student' : 'sponsor'];
     }
     for (const t of [api.idToken, api.accessToken]) {
       t.setCustomClaim(ns + 'email', email);
       t.setCustomClaim(ns + 'roles', roles);
     }
   };
   ```
5. **Create the admin role.** User Management > Roles > Create Role named `admin`. Assign it to the sponsor and to one teammate for testing.
6. **Add the sponsor as a tenant admin.** Settings > Tenant Members > Invite. Role: Admin. Invite Dr. Anderson Herzog's UA email, so the tenant does not depend on a student account after the semester.
7. **Point your local copy at it.** Put the Domain and Client ID in your git-ignored files, then restart the stack:
   - `.env.dev`: `AUTH0_DOMAIN`, `AUTH0_CLIENT_ID`
   - `frontend/.env.dev.local`: `VITE_AUTH0_DOMAIN`, `VITE_AUTH0_CLIENT_ID`

   ```
   docker compose -f docker-compose.dev.yml down && docker compose -f docker-compose.dev.yml up --build
   ```
   Log in at http://localhost:5173 and comment "logged in on mine" on #45.

## Notes

- The domain and client ID are not secrets for a single-page app, but keep them out of `.env.example` anyway so each environment stays explicit.
- When the app is hosted (#52), add the hosted URL to the callback, logout, and web origin lists.
- The email-domain fallback in the Action is temporary. #43 replaces it with a lookup in our Student table.
