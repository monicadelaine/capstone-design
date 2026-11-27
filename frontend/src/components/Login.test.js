import { describe, expect, it } from 'vitest'
import source from './Login.vue?raw'

describe('Signup role security', () => {
  it('does not include client-controlled role scopes', () => {
    expect(source).not.toContain('roleScope')
    expect(source).not.toContain('baseScopes')
    expect(source).not.toContain('role:student')
    expect(source).not.toContain('role:sponsor')
  })

  it('preserves student and sponsor signup', () => {
    expect(source).toContain("handleSignup('student')")
    expect(source).toContain("handleSignup('sponsor')")
    expect(source).toContain("screen_hint: 'signup'")
    expect(source).toContain('loginWithRedirect')

    const signup = source.match(
      /const handleSignup\s*=\s*\(role\)\s*=>\s*\{([\s\S]*?)\n\};/
    )

    expect(signup).not.toBeNull()
    expect(signup[1]).not.toMatch(/\bscope\s*:/)
  })
})
