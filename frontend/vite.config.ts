/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The console talks to the FastAPI backend through `/api` (HTTP and WebSocket).
const backend = process.env.CRISIS_BACKEND_URL ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    fs: { allow: ['..'] },
    proxy: {
      '/api': { target: backend, changeOrigin: true, ws: true, rewrite: (path) => path.replace(/^\/api/, '') },
    },
  },
  preview: {
    proxy: {
      '/api': { target: backend, changeOrigin: true, ws: true, rewrite: (path) => path.replace(/^\/api/, '') },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
})
