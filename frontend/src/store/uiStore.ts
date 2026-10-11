/**
 * Zustand UI Store
 * Holds non-server state: selected station, driver mode, replay speed, persona.
 * All items that should survive page refresh are also mirrored in the URL via
 * useSearchParams (see hooks/useUrlState.ts).
 */
import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

export type DriverMode = 'fastest' | 'balanced' | 'grid_friendly'
export type UserPersona = 'driver' | 'operator'
export type ReplaySpeed = 1 | 10 | 60

interface UIState {
  // Persona
  persona: UserPersona
  setPersona: (p: UserPersona) => void

  // Cluster map selection
  selectedStationId: string
  setSelectedStationId: (id: string) => void

  // Recommendation mode (AHP driver profile)
  driverMode: DriverMode
  setDriverMode: (m: DriverMode) => void

  // Replay playback
  replaySpeed: ReplaySpeed
  setReplaySpeed: (s: ReplaySpeed) => void
  isReplaying: boolean
  setIsReplaying: (v: boolean) => void
  replayStep: number
  setReplayStep: (step: number) => void

  // Auth token (non-sensitive token string, not secret)
  accessToken: string | null
  setAccessToken: (t: string | null) => void
  userRole: 'driver' | 'operator' | 'admin' | 'judge' | null
  setUserRole: (r: 'driver' | 'operator' | 'admin' | 'judge' | null) => void
  username: string | null
  setUsername: (u: string | null) => void
  clusterId: string | null
  setClusterId: (c: string | null) => void

  // Sidebar / mobile nav state
  sidebarOpen: boolean
  setSidebarOpen: (v: boolean) => void

  // Active alert filter
  alertFilter: 'all' | 'active' | 'crit'
  setAlertFilter: (f: 'all' | 'active' | 'crit') => void

  // Global error toast
  toastMessage: { message: string; variant: 'error' | 'success' | 'info' } | null
  showToast: (msg: string, variant?: 'error' | 'success' | 'info') => void
  clearToast: () => void
}

export const useUIStore = create<UIState>()(
  devtools(
    (set) => ({
      persona: 'driver',
      setPersona: (p) => set({ persona: p }),

      selectedStationId: 'S1',
      setSelectedStationId: (id) => set({ selectedStationId: id }),

      driverMode: 'balanced',
      setDriverMode: (m) => set({ driverMode: m }),

      replaySpeed: 1,
      setReplaySpeed: (s) => set({ replaySpeed: s }),
      isReplaying: false,
      setIsReplaying: (v) => set({ isReplaying: v }),
      replayStep: 0,
      setReplayStep: (step) => set({ replayStep: step }),

      accessToken: null,
      setAccessToken: (t) => set({ accessToken: t }),
      userRole: null,
      setUserRole: (r) => set({ userRole: r }),
      username: null,
      setUsername: (u) => set({ username: u }),
      clusterId: null,
      setClusterId: (c) => set({ clusterId: c }),

      sidebarOpen: false,
      setSidebarOpen: (v) => set({ sidebarOpen: v }),

      alertFilter: 'all',
      setAlertFilter: (f) => set({ alertFilter: f }),

      toastMessage: null,
      showToast: (message, variant = 'info') => set({ toastMessage: { message, variant } }),
      clearToast: () => set({ toastMessage: null }),
    }),
    { name: 'ev-cluster-ui' }
  )
)
