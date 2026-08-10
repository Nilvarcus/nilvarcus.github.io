# AGENTS.md — nilvarcus.github.io

Single-page static portfolio site. No build step, no package manager, no tests, no linters.

## Quickstart

- `index.html` — all page content
- `style.css` — all styling
- Deployed via GitHub Pages from `main` (push → auto-deploy)

## Workflow

```
git add index.html style.css
git commit -m "description"
git push
```

## Quirks

- `.vscode/settings.json` references `portfolio.html` as live preview path, but the actual file is `index.html`.
- `.gitignore` ignores `*.png` except `assets/teleprompter-preview.png`.
- The only asset file tracked is `assets/teleprompter-preview.png`.
