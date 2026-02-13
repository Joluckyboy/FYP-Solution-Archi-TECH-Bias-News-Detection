import path from "path"
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

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
