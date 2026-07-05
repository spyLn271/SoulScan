import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In dev, the SPA and the API share an origin: Vite proxies every `/api/*`
// request to the Rust (axum) backend, so there are no CORS hoops and the
// frontend code can just call `/api/...`. Point your axum routes under `/api`.
// `ws: true` lets a future WebSocket feed (live opportunities) proxy too.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:3000',
        changeOrigin: true,
        ws: true,
      },
      // order-book WebSocket feed (`.route("/ws", ...)`), mounted at root
      '/ws': {
        target: 'http://127.0.0.1:3000',
        changeOrigin: true,
        ws: true,
      },
    },
  },
})
