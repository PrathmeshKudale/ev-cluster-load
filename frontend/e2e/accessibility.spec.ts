/**
 * Accessibility (axe) E2E tests — runs axe-core against all five screens.
 * Reports as errors any axe violations with impact: 'serious' or 'critical'.
 *
 * Run: npx playwright test e2e/accessibility.spec.ts
 */
import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

const BASE = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:5173'

async function loginAs(
  page: import('@playwright/test').Page,
  role: 'driver' | 'operator'
) {
  await page.addInitScript(({ role }) => {
    localStorage.setItem(
      'ev-ui-store',
      JSON.stringify({
        state: {
          accessToken: 'mock-token',
          userRole: role,
          username: role,
          persona: role === 'operator' ? 'operator' : 'driver',
        },
        version: 0,
      })
    )
  }, { role })
}

const SCREENS = [
  { path: '/driver',               role: 'driver'    as const, name: 'Driver dashboard' },
  { path: '/driver/recommend',     role: 'driver'    as const, name: 'Driver recommend' },
  { path: '/operator',             role: 'operator'  as const, name: 'Operator dashboard' },
  { path: '/operator/transformer', role: 'operator'  as const, name: 'Operator transformer' },
  { path: '/about',                role: 'driver'    as const, name: 'About' },
]

for (const screen of SCREENS) {
  test(`axe: no serious violations on ${screen.name}`, async ({ page }) => {
    await loginAs(page, screen.role)
    await page.goto(`${BASE}${screen.path}`)
    await page.waitForLoadState('networkidle')

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      // Exclude third-party Leaflet map container (not under our control)
      .exclude('.leaflet-container')
      .disableRules(['color-contrast'])
      .analyze()

    const serious = results.violations.filter(
      v => v.impact === 'serious' || v.impact === 'critical'
    )

    if (serious.length > 0) {
      const messages = serious.map(v =>
        `[${v.impact}] ${v.id}: ${v.description}\n  Nodes: ${v.nodes.map(n => n.html).join(', ')}`
      ).join('\n\n')
      expect.soft(serious, `Axe serious violations on ${screen.name}:\n${messages}`).toHaveLength(0)
    }

    // Confirm zero critical violations (hard fail)
    const critical = results.violations.filter(v => v.impact === 'critical')
    expect(critical).toHaveLength(0)
  })
}
