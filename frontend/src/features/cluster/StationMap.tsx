/**
 * StationMap — Leaflet map using OpenStreetMap tiles.
 * Features:
 *   - Lazy-loaded Leaflet + leaflet.markercluster
 *   - Dark theme tile filter via CSS (see index.css)
 *   - Severity-coloured circle markers (green/amber/red)
 *   - Accessible: keyboard navigation, role="application"
 *   - 360px minimum width responsive
 */
import React, { useEffect, useRef } from 'react'

export interface StationMapMarker {
  id: string
  name: string
  latitude: number
  longitude: number
  utilization?: number    // 0–1
  chargers?: number
  queueDepth?: number
}

interface StationMapProps {
  markers: StationMapMarker[]
  selectedStationId?: string
  warnThreshold?: number    // 0–1, default 0.8
  critThreshold?: number    // 0–1, default 0.9
  onMarkerClick?: (id: string) => void
  height?: number
}

function severityHex(util: number, warn: number, crit: number): string {
  if (util >= crit) return '#dc2626'
  if (util >= warn) return '#d97706'
  return '#059669'
}

export const StationMap = React.memo(function StationMap({
  markers,
  selectedStationId,
  warnThreshold = 0.8,
  critThreshold = 0.9,
  onMarkerClick,
  height = 380,
}: StationMapProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<any>(null)
  const clusterGroupRef = useRef<any>(null)

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return

    let map: any
    let L: typeof import('leaflet')

    const init = async () => {
      L = (await import('leaflet')).default

      // Import Leaflet CSS
      await import('leaflet/dist/leaflet.css')

      // Import marker cluster plugin
      await import('leaflet.markercluster')
      await import('leaflet.markercluster/dist/MarkerCluster.css')
      await import('leaflet.markercluster/dist/MarkerCluster.Default.css')

      // Centre on Bengaluru cluster (default) or first marker
      const centre: [number, number] = markers.length > 0
        ? [markers[0].latitude, markers[0].longitude]
        : [12.9716, 77.5946]

      map = L.map(containerRef.current!, {
        center: centre,
        zoom: 13,
        zoomControl: true,
        attributionControl: true,
      })

      // Standard OpenStreetMap tiles
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
      }).addTo(map)

      // Central Substation Transformer T1
      const txLat = 12.9750
      const txLng = 77.5900
      const txIcon = L.divIcon({
        className: '',
        html: `
          <div style="
            width:40px;height:40px;border-radius:8px;
            background:#1e88e5;border:3px solid #ffffff;
            display:flex;flex-direction:column;align-items:center;justify-content:center;
            color:#fff;font-weight:800;font-size:10px;line-height:1.1;
            box-shadow:0 4px 12px rgba(0,0,0,0.5);
            cursor:pointer;
          ">
            <span>TX</span>
            <span style="font-size:8px;font-weight:600">100kVA</span>
          </div>
        `,
        iconSize: [40, 40],
        iconAnchor: [20, 20],
        popupAnchor: [0, -22],
      })

      L.marker([txLat, txLng], { icon: txIcon })
        .bindPopup(`
          <div style="min-width:180px;font-family:sans-serif;color:#0f172a">
            <div style="font-weight:700;font-size:14px;color:#1e88e5;margin-bottom:4px">Substation Transformer T1</div>
            <div style="font-size:12px;color:#475569">Rating: <b>100 kVA (85 kW active)</b></div>
            <div style="font-size:12px;color:#475569">Voltage: <b>11 kV / 415 V 3-Phase</b></div>
            <div style="font-size:12px;color:#059669;margin-top:4px">Serving 4 Radial Charging Hubs</div>
          </div>
        `)
        .addTo(map)

      // Feeder lines from TX to each station
      markers.forEach((m) => {
        L.polyline([[txLat, txLng], [m.latitude, m.longitude]], {
          color: '#1e88e5',
          weight: 2.5,
          dashArray: '6, 6',
          opacity: 0.75,
        }).addTo(map)
      })

      // Marker cluster group for EV charging stations
      const group = (L as any).markerClusterGroup({
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true,
        maxClusterRadius: 50,
      })

      markers.forEach((m) => {
        const util = m.utilization ?? 0
        const color = severityHex(util, warnThreshold, critThreshold)
        const isSelected = m.id === selectedStationId

        const icon = L.divIcon({
          className: '',
          html: `
            <div style="
              width:${isSelected ? '44px' : '38px'};
              height:${isSelected ? '44px' : '38px'};
              border-radius:50%;
              background:${color};
              border:${isSelected ? '4px solid #38bdf8' : '3px solid #ffffff'};
              display:flex;flex-direction:column;align-items:center;justify-content:center;
              color:#fff;font-weight:800;font-size:11px;line-height:1;
              box-shadow:${isSelected ? '0 0 16px #38bdf8, 0 4px 12px rgba(0,0,0,0.5)' : '0 2px 8px rgba(0,0,0,0.4)'};
              cursor:pointer;
              transition:all 0.2s ease;
            ">
              <span>${m.chargers ?? '?'}</span>
              <span style="font-size:8px;font-weight:600">BAY</span>
            </div>
          `,
          iconSize: [isSelected ? 44 : 38, isSelected ? 44 : 38],
          iconAnchor: [isSelected ? 22 : 19, isSelected ? 22 : 19],
          popupAnchor: [0, -22],
        })

        const popupHtml = `
          <div style="min-width:180px;font-family:sans-serif;color:#0f172a">
            <div style="font-weight:700;font-size:14px;margin-bottom:4px;color:#0f172a">${m.name} (${m.id})</div>
            <div style="font-size:12px;color:#475569">Chargers: <b>${m.chargers ?? '—'} Plugs (Type 2 AC)</b></div>
            ${m.utilization !== undefined ? `<div style="font-size:12px;color:#475569">Utilization: <b>${(m.utilization * 100).toFixed(1)}%</b></div>` : ''}
            ${m.queueDepth !== undefined ? `<div style="font-size:12px;color:#475569">Queue: <b>${m.queueDepth} vehicles waiting</b></div>` : ''}
            <div style="font-size:11px;color:#64748b;margin-top:6px">GPS: ${m.latitude.toFixed(4)}°N, ${m.longitude.toFixed(4)}°E</div>
          </div>
        `

        const marker = L.marker([m.latitude, m.longitude], { icon })
          .bindPopup(popupHtml)

        if (onMarkerClick) {
          marker.on('click', () => onMarkerClick(m.id))
        }
        group.addLayer(marker)
      })

      map.addLayer(group)

      // Fit bounds including transformer and stations
      const allCoords: [number, number][] = [[txLat, txLng], ...markers.map(m => [m.latitude, m.longitude] as [number, number])]
      const bounds = L.latLngBounds(allCoords as any)
      map.fitBounds(bounds, { padding: [40, 40] })

      mapRef.current = map
      clusterGroupRef.current = group

      // Invalidate size once rendered in container
      setTimeout(() => {
        if (mapRef.current) {
          mapRef.current.invalidateSize()
        }
      }, 200)
    }

    init()

    return () => {
      if (mapRef.current) {
        mapRef.current.remove()
        mapRef.current = null
        clusterGroupRef.current = null
      }
    }
  }, []) // Only init once

  // Pan / center map if selectedStationId changes
  useEffect(() => {
    if (!mapRef.current || !selectedStationId) return
    const target = markers.find(m => m.id === selectedStationId)
    if (target) {
      mapRef.current.setView([target.latitude, target.longitude], 15, { animate: true })
    }
  }, [selectedStationId, markers])

  return (
    <div
      role="application"
      aria-label="EV charging station map"
      style={{ width: '100%', height, minWidth: 0, borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}
    >
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
    </div>
  )
})
