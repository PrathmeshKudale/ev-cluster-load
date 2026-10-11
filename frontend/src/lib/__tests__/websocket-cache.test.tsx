import React from 'react'
import { render, screen, act, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useForecast, patchForecastCache, queryKeys } from '../queries'

const TestForecastComponent: React.FC = () => {
  const { data, isLoading } = useForecast()

  if (isLoading) return <div>Loading forecast...</div>
  if (!data) return <div>No forecast</div>

  return (
    <div>
      <div data-testid="p50-val">{data.p50[0]}</div>
      <div data-testid="p90-val">{data.p90[0]}</div>
      <div data-testid="model-ver">{data.model_version}</div>
    </div>
  )
}

describe('F3: WebSocket cache update without refetch', () => {
  it('updates the forecast cache directly when receiving a WebSocket patch', async () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    })

    // Pre-populate query cache with initial data
    queryClient.setQueryData(queryKeys.forecast(), {
      hours: [0, 1, 2],
      p10: [20.0, 22.0, 25.0],
      p50: [45.0, 48.0, 50.0],
      p90: [75.0, 78.0, 80.0],
      warn: 80.0,
      critical: 90.0,
      model_version: 'v1_initial',
    })

    // Track if refetch queryFn is called
    const querySpy = vi.spyOn(queryClient, 'fetchQuery')

    render(
      <QueryClientProvider client={queryClient}>
        <TestForecastComponent />
      </QueryClientProvider>
    )

    // Verify initial values
    expect(screen.getByTestId('p50-val')).toHaveTextContent('45')
    expect(screen.getByTestId('p90-val')).toHaveTextContent('75')

    // Simulate WebSocket message arrival: patch forecast cache directly
    act(() => {
      patchForecastCache(queryClient, {
        p50: [62.5, 48.0, 50.0],
        p90: [88.1, 78.0, 80.0],
      })
    })

    // Verify the component re-rendered with new values immediately without refetch
    await waitFor(() => {
      expect(screen.getByTestId('p50-val')).toHaveTextContent('62.5')
      expect(screen.getByTestId('p90-val')).toHaveTextContent('88.1')
    })

    // Assert fetchQuery was NOT triggered (no network refetch occurred)
    expect(querySpy).not.toHaveBeenCalled()
  })
})
