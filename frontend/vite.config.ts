/// <reference types="vitest" />
import path from 'path'
import { fileURLToPath } from 'url'
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vite.dev/config/
export default defineConfig({
  base: process.env.VITE_BASE_PATH || '/',
  plugins: [
    tailwindcss(),
    react(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        // Route-level code splitting: each lazy page gets its own chunk
        manualChunks(id) {
          if (id.includes('node_modules/echarts')) return 'vendor-echarts'
          if (id.includes('node_modules/leaflet')) return 'vendor-leaflet'
          if (id.includes('node_modules/react-dom')) return 'vendor-react'
          if (id.includes('node_modules/@tanstack')) return 'vendor-query'
        },
      },
    },
    // Bundle size budget: warn at 250 kB, error at 500 kB per chunk
    chunkSizeWarningLimit: 250,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test-setup.ts',
    exclude: ['node_modules', 'dist', 'e2e/**'],
    pool: 'threads',
    coverage: {
      provider: 'v8',
      include: [
        'src/hooks/useDownsample.ts',
        'src/hooks/useThrottledWS.ts',
        'src/hooks/useUrlState.ts',
        'src/features/forms/schemas.ts',
      ],
      thresholds: { lines: 70, functions: 70 },
    },
  },
})
