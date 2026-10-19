# portfolio

A TanStack Start portfolio laid out as a stack of file-folder sheets. Each route is a sheet; the active one expands and the rest collapse to labelled strips.

```bash
pnpm install
pnpm dev
```

Content lives in `src/content.ts`. Sheet colors are set in `src/components/site-shell.tsx`. Routes are under `src/routes`; TanStack Router updates `src/route-tree.gen.ts` for you.

Build the production app with:

```bash
pnpm build
```
