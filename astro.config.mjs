import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://homestay-kenangan.vercel.app',
  // trailingSlash 'always' makes the build emit /about -> redirect to /about/,
  // matching the canonical + sitemap URLs the sitemap plugin produces.
  trailingSlash: 'always',
  integrations: [
    tailwind(),
    sitemap(),
  ],
  output: 'static',
  compressHTML: true,
  build: {
    assets: '_assets',
    inlineStylesheets: 'auto',
  },
  image: {
    service: { entrypoint: 'astro/assets/services/noop' },
    domains: [],
  },
  vite: {
    build: {
      rollupOptions: {
        output: {
          manualChunks: undefined,
        },
      },
    },
  },
});
