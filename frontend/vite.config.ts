import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vitejs.dev/config/
export default defineConfig({
  server: {
    host: "127.0.0.1",
    port: 3000,
    proxy: {
      '/upload': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/upload/, '/upload'),
      },
      '/retrieve_from_path': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/retrieve_from_path/, '/retrieve_from_path'),
      }
    },

  },
  plugins: [react()],
})
