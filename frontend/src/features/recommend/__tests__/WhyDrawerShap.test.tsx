import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { RecommendationCard } from '../RecommendationCard'
import { recommendationFixture } from '@/fixtures/recommendationFixture'

describe('RecommendationCard Why Drawer with SHAP Explanations', () => {
  it('renders recommendation card with initial metrics', () => {
    const rec = recommendationFixture.top3[0]
    render(<RecommendationCard recommendation={rec} />)

    expect(screen.getByText(rec.station_name)).toBeInTheDocument()
    expect(screen.getByText(/Why this slot\?/i)).toBeInTheDocument()
  })

  it('opens Why Drawer and displays LightGBM TreeExplainer top-3 SHAP attributions', () => {
    const rec = recommendationFixture.top3[0]
    render(<RecommendationCard recommendation={rec} />)

    const whyBtn = screen.getByRole('button', { name: new RegExp(`Open why drawer for ${rec.station_name}`, 'i') })
    fireEvent.click(whyBtn)

    // Verify Why Drawer title
    expect(screen.getByText(new RegExp(`Why ${rec.station_name}\\?`, 'i'))).toBeInTheDocument()

    // Verify SHAP TreeExplainer section
    expect(screen.getByText(/LightGBM TreeExplainer/i)).toBeInTheDocument()

    // Verify all 3 SHAP reasons are visible
    if (rec.shap_reasons) {
      for (const reason of rec.shap_reasons) {
        expect(screen.getByText(reason)).toBeInTheDocument()
      }
    }

    // Verify Multi-Objective formulation & Queue / Detour / Overload Risk factors
    expect(screen.getByText(/Multi-Objective Score Formulation/i)).toBeInTheDocument()
    expect(screen.getByText(/Queue Wait Penalty/i)).toBeInTheDocument()
    expect(screen.getByText(/Detour Distance Penalty/i)).toBeInTheDocument()
    expect(screen.getByText(/Transformer Overload Risk/i)).toBeInTheDocument()
  })
})
