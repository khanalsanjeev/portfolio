# Sanjeev Khanal — Portfolio (GitHub Pages + Cloudflare)

Static personal site. Deploy to GitHub Pages, front it with Cloudflare.

## Deploy to GitHub Pages

1. Push this folder to a GitHub repo.
2. Repo → **Settings → Pages → Build and deployment**:
   - Source: **Deploy from a branch**
   - Branch: `main` / `(root)`
   - Save. GitHub will give you the `https://<username>.github.io/<repo>/` URL.
3. The `CNAME` file in this repo already says `sanjeevkhanal.com.np`, so once DNS points here, GitHub serves the custom domain.
4. `.nojekyll` is included so GitHub does not run the Jekyll build (keeps the raw files + CNAME intact).

## Cloudflare DNS

If your `sanjeevkhanal.com.np` zone is in Cloudflare:

1. **DNS → Records** — add (or set) the root record:
   - Type `CNAME`, Name `@`, Target `<username>.github.io`, **Proxy status: Proxied** (orange cloud). Cloudflare flattens CNAME @ records automatically.
   - (Optional) Type `CNAME`, Name `www`, Target `sanjeevkhanal.com.np`, Proxied.
2. **SSL/TLS → Overview**: set mode to **Full (strict)** so the Cloudflare→GitHub Pages hop is encrypted over HTTPS.
3. Wait for propagation; then `https://sanjeevkhanal.com.np` should resolve.

## Cloudflare caching (fixes the PageSpeed cache warnings)

GitHub Pages sends `Cache-Control: max-age=600` — that's the 10-minute TTL PageSpeed flagged. Cloudflare sits in front, so fix it with Cache Rules:

**Caching → Cache Rules → Create rule** with these settings:

| Setting | Value |
|---|---|
| **Expression** | `(http.host eq "sanjeevkhanal.com.np" and any(http.request.uri.path ends_with ".jpg"))` |
| **Cache status** | Eligible for cache |
| **Edge TTL** | 1 month |
| **Browser TTL** | 2 months |

Create **four rules** total, one per file type:
- `.jpg` and `.png` → Edge TTL 1 month (images rarely change)
- `.svg` (favicon) → Edge TTL 1 month
- `.css` / `.js` → Edge TTL 1 day (safe if you edit styles)
- HTML (`/`) → Edge TTL **no-cache** (so your edits go live instantly; HTML is tiny)

## Cloudflare performance toggles (no-config)

These are already improving this site with zero setup:
- **Brotli compression** — on by default for proxied content (your HTML/CSS come down compressed).
- **HTTP/3** — on by default for proxied domains.
- **Auto Minify** — optional: **Speed → Optimization → Content Optimization**; enable HTML/CSS/JS minification.

## Notes

- The site inlines its CSS (no separate `styles.css` request) and loads Google Fonts asynchronously, so GitHub Pages + Cloudflare needs no special header config.
- `robots.txt` and `sitemap.xml` already point at `https://sanjeevkhanal.com.np/`.
- `sanjeev.png` (991 KB) is unused after image optimization — delete it from the repo before pushing to keep the repo lean.