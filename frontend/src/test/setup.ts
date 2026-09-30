import '@testing-library/jest-dom/vitest'
import { configure } from '@testing-library/react'
import { vi } from 'vitest'

// The console renders many map markers; under parallel CI load the default 1 s
// wait for async UI transitions is occasionally too tight.
configure({ asyncUtilTimeout: 3000 })

vi.mock('maplibre-gl', () => import('./maplibreMock'))
vi.mock('maplibre-gl/dist/maplibre-gl.css', () => ({}))
