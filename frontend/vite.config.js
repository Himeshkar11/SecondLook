import { defineConfig } from 'vite';

export default defineConfig({
  envDir: '..',
  server: {
    host: '0.0.0.0',
    port: 5173,
  },
});
