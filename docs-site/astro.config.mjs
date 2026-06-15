import { defineConfig } from 'astro/config';
import astroExpressiveCode from 'astro-expressive-code';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://edithatogo.github.io',
  base: '/hathi-nz/',
  integrations: [
    astroExpressiveCode(),
    mdx(),
    sitemap(),
    starlight({
      title: 'Hathi NZ',
      description: 'Legal NZ documentation portal for Hathi NZ.',
      sidebar: [
        { label: 'Start', items: ['index', 'docs-tooling-audit'] },
      ],
    }),
  ],
});
