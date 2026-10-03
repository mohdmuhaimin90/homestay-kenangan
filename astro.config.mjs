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
    // Stamp lastmod so crawlers can tell which pages changed. Static hosts have
    // no per-file mtime, so the build date is the honest signal: every deploy
    // ships the current content.
    sitemap({
      serialize(item) {
        return { ...item, lastmod: new Date().toISOString() };
      },
    }),
  ],
  output: 'static',
  compressHTML: true,
  build: {
    assets: '_assets',
    // Keep the stylesheet external. Inlining pushed the document to ~18 KB and
    // delayed first byte past 500 ms, which cost more than the extra request.
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
