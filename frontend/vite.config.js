import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Requests to /api and /uploads are forwarded to the FastAPI backend,
// so the browser never deals with CORS and phones on the same Wi-Fi work too.
const backend = {
  '/api': { target: 'http://localhost:8000', changeOrigin: true },
  '/uploads': { target: 'http://localhost:8000', changeOrigin: true },
};

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    proxy: backend,
  },
  preview: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    proxy: backend,
  },
});
