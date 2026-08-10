# Recommended Portfolio Updates

## High Priority — Conversion & Credibility Features

### 1. Prominent Call-to-Action Button
- The email link is buried in the contact card. Add a prominent "Work With Me" or "Sponsor a Video" button.
- Place it in the hero area or make it a strong visual element in the contact card.
- Link directly to `mailto:Nilvarcus@gmail.com` so potential collaborators have an obvious next step.

### 2. Sponsorships / Past Brand Work
- Even a simple "Past Collaborations" card with logo names builds massive trust.
- Sponsors want proof you've done this before.
- Only include real collaborations, press coverage, or developer relationships that can be verified.

### 3. Services / Media Kit
- Add a dedicated card explaining what you offer: dedicated videos, Shorts, sponsored segments, and playtest coverage.
- Tie it to a downloadable media kit PDF or Google Doc.
- Include a short inquiry prompt so visitors know what information to send.

---

## Medium Priority — Content & Polish

### 4. Gear / Setup Section
- Small card with PC specs, mic, camera, and editing setup.
- Adds transparency for viewers and creates potential affiliate link opportunities.

### 5. Favicon & Browser Branding
- No `<link rel="icon">` in `<head>`.
- Create a simple logo mark using the status dot or a custom NILVARCUS symbol for the browser icon and bookmarks.

### 6. Open Graph / Meta Description Tags
- Add `og:title`, `og:description`, `og:image`, and a meta description.
- Improves link previews when the portfolio is shared on Discord, X, Bluesky, or other platforms.

### 7. Image `alt` Text
- Replace generic values such as `alt="Video"`, `alt="Thumbnail"`, and `alt="Short"` with meaningful descriptions.
- Improves accessibility and SEO.

### 8. Fix Live Preview Path
- `.vscode/settings.json` references `portfolio.html`, but the actual file is `index.html`.
- Update the setting for consistency.

---

## Low Priority — Nice-to-Have

### 9. Recent Video Freshness
- The five long-form videos are statically pinned. Consider swapping them periodically or fetching the latest uploads.
- Keep the current curated selection if it performs better as a portfolio showcase.

### 10. Fix Threads Link
- `https://www.threads.com/@nilvarcus` → `https://www.threads.net/@nilvarcus`.

---

## Suggested Page Layout

```text
[HERO]          — name + prominent CTA button
[ABOUT]         — existing creator positioning
[SERVICES]      — what you offer + media kit link
[PAST BRANDS]   — verified collaborations or coverage
[CONTACT]       — existing social links and email
[VIDEOS]        — existing
[THUMBNAILS]    — existing
[SHORTS]        — existing
[GEAR]          — optional setup section
[CODE]          — existing
```
