import path from "path"
import { fileURLToPath } from "url"
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// Web-only build config (no Chrome extension plugin)
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: {
    outDir: "dist-web",
    assetsDir: "assets",
    rollupOptions: {
      input: {
        main: 'index.html',
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})
