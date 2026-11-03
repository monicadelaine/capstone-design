import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'

const mocks = vi.hoisted(() => ({ auth0: null }))

vi.mock('../main', async () => {
  const { ref } = await import('vue')
  mocks.auth0 = {
    isAuthenticated: ref(false),
    isLoading: ref(false),
    user: ref(null),
    loginWithRedirect: vi.fn(),
    getAccessTokenSilently: vi.fn().mockResolvedValue('token'),
  }
  return { auth0: mocks.auth0 }
})
vi.mock('../services/api', () => ({ default: { setToken: vi.fn(), getProfile: vi.fn() } }))

const { default: router } = await import('./index.js')

describe('router guard', () => {
  beforeEach(async () => {
    mocks.auth0.isAuthenticated.value = false
    mocks.auth0.user.value = null
    await router.replace('/').catch(() => {})
  })

  it('shows the no-role error instead of redirecting forever when a logged-in user has no role', async () => {
    mocks.auth0.isAuthenticated.value = true
    mocks.auth0.user.value = { email: 'someone@example.com' } // token carried no roles claim

    const failure = await router.push('/?login=1')

    expect(failure).toBeUndefined()
    expect(router.currentRoute.value.path).toBe('/')
    expect(router.currentRoute.value.query.error).toBe('no_role')
  })

  it('sends a user without a role away from protected pages to the no-role error', async () => {
    mocks.auth0.isAuthenticated.value = true
    mocks.auth0.user.value = { email: 'someone@example.com' }

    await router.push('/student')

    expect(router.currentRoute.value.fullPath).toBe('/?error=no_role')
  })
})
