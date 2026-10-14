/**
 * screenshot.spec.ts — Playwright visual documentation script.
 *
 * Captures screenshots of all 5 screens × 2 themes × 2 viewports
 * and saves them to docs/img/.
 *
 * Run:  npx playwright test e2e/screenshot.spec.ts
 *
 * Screens captured:
 *   1. /driver            (Driver dashboard)
 *   2. /driver/recommend  (Recommendation flow)
 *   3. /operator          (Operator dashboard)
 *   4. /operator/transformer (Transformer page)
 *   5. /about             (About / methodology)
 *
 * Viewports:
 *   mobile:  390 × 844  (iPhone 14)
 *   desktop: 1280 × 800
 *
 * Themes: dark (default), light (toggle via localStorage)
 */
import process from 'node:process'
import { test, expect } from '@playwright/test'
import path from 'path'
import fs from 'fs'

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:5173'
const DOCS_IMG = path.resolve(__dirname, '../../docs/img')

const SCREENS = [
  { name: 'driver',               path: '/driver',               role: 'driver' },
  { name: 'driver-recommend',     path: '/driver/recommend',     role: 'driver' },
  { name: 'operator',             path: '/operator',             role: 'operator' },
  { name: 'operator-transformer', path: '/operator/transformer', role: 'operator' },
  { name: 'about',                path: '/about',                role: 'driver' },
]

const VIEWPORTS = [
  { name: 'mobile',   width: 390,  height: 844 },
  { name: 'desktop',  width: 1280, height: 800 },
]

const THEMES: Array<{ name: string; class: string }> = [
  { name: 'dark',  class: 'dark' },
  { name: 'light', class: 'light' },
]

/** Quick login via localStorage to avoid the login form in every test. */
async function setAuthAndRole(page: import('@playwright/test').Page, role: 'driver' | 'operator') {
  await page.addInitScript(({ role }) => {
    // Mock the Zustand persisted state
    const state = {
      state: {
        accessToken: 'mock-token-for-screenshots',
        userRole: role,
        username: role,
        persona: role === 'operator' ? 'operator' : 'driver',
      },
      version: 0,
    }
    localStorage.setItem('ev-ui-store', JSON.stringify(state))
  }, { role })
}

test.describe('Documentation screenshots', () => {
  for (const theme of THEMES) {
    for (const viewport of VIEWPORTS) {
      for (const screen of SCREENS) {
        const testName = `${screen.name}--${theme.name}--${viewport.name}`

        test(testName, async ({ page }) => {
          fs.mkdirSync(DOCS_IMG, { recursive: true })

          // Set viewport
          await page.setViewportSize({ width: viewport.width, height: viewport.height })

          // Inject auth before navigation
          await setAuthAndRole(page, screen.role as 'driver' | 'operator')

          // Apply theme
          await page.addInitScript(({ themeClass }) => {
            document.addEventListener('DOMContentLoaded', () => {
              document.documentElement.className = themeClass
              localStorage.setItem('ev-theme', themeClass)
            })
          }, { themeClass: theme.class })

          await page.goto(`${BASE_URL}${screen.path}`, { waitUntil: 'networkidle' })

          // Apply theme class (may have been reset by JS)
          await page.evaluate((cls) => {
            document.documentElement.className = cls
          }, theme.class)

          // Wait for charts to lazy-load
          await page.waitForTimeout(800)

          const filename = `${testName}.png`
          const outPath = path.join(DOCS_IMG, filename)

          await page.screenshot({
            path: outPath,
            fullPage: false,
            animations: 'disabled',
          })

          expect(fs.existsSync(outPath)).toBe(true)
          console.log(`  ✓ Saved: docs/img/${filename}`)
        })
      }
    }
  }
})
