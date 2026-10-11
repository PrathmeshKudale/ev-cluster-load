export interface StationEdgeFixture {
  src: string
  dst: string
  distance_km: number
  drive_minutes: number
}

export interface ClusterFixture {
  cluster_id: string
  name: string
  transformer_id: string
  transformer_name: string
  rating_kva: number
  power_factor: number
  stations: Array<{
    id: string
    name: string
    chargers: number
    kw: number
    detour_min: number
    latitude: number
    longitude: number
    active_chargers: number
    current_kw: number
    utilization_rate: number
    status: 'available' | 'busy' | 'full'
  }>
  edges: StationEdgeFixture[]
}

export const clusterFixture: ClusterFixture = {
  cluster_id: 'C1',
  name: 'Metro Central Cluster',
  transformer_id: 'T1',
  transformer_name: 'TX-Metro-100kVA',
  rating_kva: 100.0,
  power_factor: 0.95,
  stations: [
    {
      id: 'S1',
      name: 'Market Road',
      chargers: 8,
      kw: 7.4,
      detour_min: 0.0,
      latitude: 12.9716,
      longitude: 77.5946,
      active_chargers: 4,
      current_kw: 29.6,
      utilization_rate: 0.50,
      status: 'available',
    },
    {
      id: 'S2',
      name: 'Station Plaza',
      chargers: 6,
      kw: 7.4,
      detour_min: 4.0,
      latitude: 12.9815,
      longitude: 77.6083,
      active_chargers: 4,
      current_kw: 22.2,
      utilization_rate: 0.67,
      status: 'available',
    },
    {
      id: 'S3',
      name: 'College Gate',
      chargers: 6,
      kw: 7.4,
      detour_min: 7.0,
      latitude: 12.9611,
      longitude: 77.5855,
      active_chargers: 5,
      current_kw: 14.8,
      utilization_rate: 0.83,
      status: 'busy',
    },
    {
      id: 'S4',
      name: 'Ring Road Hub',
      chargers: 4,
      kw: 7.4,
      detour_min: 10.0,
      latitude: 12.9922,
      longitude: 77.5620,
      active_chargers: 4,
      current_kw: 7.4,
      utilization_rate: 1.00,
      status: 'full',
    },
  ],
  edges: [
    { src: 'S1', dst: 'S2', distance_km: 1.8, drive_minutes: 4.2 },
    { src: 'S1', dst: 'S3', distance_km: 3.2, drive_minutes: 7.1 },
    { src: 'S1', dst: 'S4', distance_km: 4.1, drive_minutes: 9.8 },
    { src: 'S2', dst: 'S1', distance_km: 1.8, drive_minutes: 4.0 },
    { src: 'S2', dst: 'S3', distance_km: 4.5, drive_minutes: 10.2 },
    { src: 'S2', dst: 'S4', distance_km: 3.5, drive_minutes: 8.5 },
    { src: 'S3', dst: 'S1', distance_km: 3.2, drive_minutes: 7.0 },
    { src: 'S3', dst: 'S2', distance_km: 4.5, drive_minutes: 10.0 },
    { src: 'S3', dst: 'S4', distance_km: 5.8, drive_minutes: 13.4 },
    { src: 'S4', dst: 'S1', distance_km: 4.1, drive_minutes: 9.5 },
    { src: 'S4', dst: 'S2', distance_km: 3.5, drive_minutes: 8.2 },
    { src: 'S4', dst: 'S3', distance_km: 5.8, drive_minutes: 13.0 },
  ],
}
