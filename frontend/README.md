# Frontend (Vue 3 + Vite)

## Unit Testing

The frontend unit tests use:

- `vitest` as the test runner
- `@vue/test-utils` for Vue component tests
- `jsdom` for browser-like DOM behavior in tests

### Test Coverage Added

- Service layer
	- `src/services/api.test.js`
	- Verifies token handling, endpoint calls, URL/query construction, and student data normalization
- Pinia stores
	- `src/stores/projectsStore.test.js`
	- `src/stores/studentStore.test.js`
	- Verifies fetch flows, success/error handling, getters, and state reset behavior
- Components
	- `src/components/ConfirmationModal.test.js`
	- `src/components/EmailForm.test.js`
	- `src/components/SponsorOutreach.test.js`
	- `src/components/ProjectPresentation.test.js`
	- `src/components/Sidebar.test.js`
	- Verifies rendering, user interactions, emitted events, payload generation, and navigation behavior

### Run Tests

From the `frontend` directory:

1. Run all tests once:

	 `npm run test`

2. Run in watch mode:

	 `npm run test:watch`

3. Run coverage:

	 `npm run test:coverage`
