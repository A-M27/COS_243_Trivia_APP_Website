import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [svelte()],
  base: "/trivia/",
  server: {
    watch: { usePolling: true, interval: 300 },
    proxy: {
      "/static": "http://127.0.0.1:8000",
    },
  },
  build: { 
    rollupOptions: {
      output: {
        entryFileNames: "assets/trivia.js",
        assetFileNames: "assets/trivia.css",
      },
  },

   }, 
});
