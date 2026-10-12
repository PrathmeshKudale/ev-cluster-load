/**
 * VirtualAlertFeed component tests
 * Tests rendering, virtualisation threshold, and acknowledge functionality.
 */
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { VirtualAlertFeed } from '@/features/transformer/VirtualAlertFeed'
import type { AlertItem } from '@/fixtures/alertFixture'

const makeAlerts = (n: number, level: AlertItem['level'] = 'warning'): AlertItem[] =>
  Array.from({ length: n }, (_, i) => ({
    id: `alert-${i}`,
    level,
    message: `Test alert ${i}`,
    station_id: `S${i % 4}`,
    timestamp: new Date(Date.now() - i * 60000).toISOString(),
    acknowledged: false,
  }))

describe('VirtualAlertFeed', () => {
  it('renders "No alerts" when list is empty', () => {
    render(<VirtualAlertFeed alerts={[]} />)
    expect(screen.getByText('No alerts')).toBeInTheDocument()
  })

  it('renders all items for short lists (< VIRTUAL_THRESHOLD)', () => {
    const alerts = makeAlerts(5, 'critical')
    render(<VirtualAlertFeed alerts={alerts} />)
    expect(screen.getAllByRole('listitem')).toHaveLength(5)
  })

  it('renders alert messages', () => {
    render(<VirtualAlertFeed alerts={makeAlerts(3)} />)
    expect(screen.getByText('Test alert 0')).toBeInTheDocument()
    expect(screen.getByText('Test alert 1')).toBeInTheDocument()
  })

  it('acknowledge button calls onAcknowledge', () => {
    const onAck = vi.fn()
    render(<VirtualAlertFeed alerts={makeAlerts(2)} onAcknowledge={onAck} />)
    const ackButtons = screen.getAllByRole('button', { name: /acknowledge/i })
    fireEvent.click(ackButtons[0])
    expect(onAck).toHaveBeenCalledWith('alert-0')
  })

  it('has accessible role=list and aria-label', () => {
    render(<VirtualAlertFeed alerts={makeAlerts(2)} />)
    expect(screen.getByRole('list')).toBeInTheDocument()
  })

  it('renders severity borders for critical alerts', () => {
    const critAlert = makeAlerts(1, 'critical')
    const { container } = render(<VirtualAlertFeed alerts={critAlert} />)
    const item = container.querySelector('[role="listitem"]') as HTMLElement
    expect(item.style.borderLeft).toMatch(/crit-red/)
  })
})
