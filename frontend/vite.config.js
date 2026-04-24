import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/users': 'http://localhost:8001',
      '/stock': 'http://localhost:8001',
      '/cache': 'http://localhost:8001',
      '/scheduler': 'http://localhost:8001',
    },
  },
})
