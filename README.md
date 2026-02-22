# 🔧 Error Fix Engine

> A 100 % automated, zero-cost website that generates and publishes
> developer error-fix guides — powered by Gemini AI, GitHub Actions,
> and GitHub Pages.

---

## What is this?

Developers constantly Google errors like:

- `"OpenAI Error 429 fix"`
- `"Docker exit code 1"`
- `"Kubernetes CrashLoopBackOff"`
- `"Permission denied API error"`

**Error Fix Engine** automatically creates a page for every one of those
searches — without you lifting a finger after the initial setup.

Every night, a GitHub Actions job:
1. Reads `config/errors.yaml` (your list of errors to cover)
2. Sends each new error to Google Gemini and gets a 900–1200 word
   SEO article back
3. Converts the article to HTML and rebuilds the static site
4. Commits the new files and deploys to GitHub Pages

The complete hosting cost is **$0/month** (free GitHub Actions minutes +
free GitHub Pages + free Gemini API tier).

---

## How it earns money

| Channel | How | When |
|---------|-----|------|
| **Google AdSense** | Display ads on every page | After Google approves your site (typically ≥ 20 pages, domain age ≥ 3 months) |
| **Affiliate links** | Cloud provider links in footer & sidebar | Passive – every visitor who signs up earns a commission |
| **Sponsored content** | Paid "fix" guides for devtool companies | Manual negotiation once traffic is established |

Realistic timeline to first revenue: **3–6 months.**

Realistic monthly revenue at 5 000 monthly visitors (RPM $4–8):
**$20–$40 / month from ads alone**, scaling linearly with traffic.

---

## Architecture

```
config/errors.yaml          ← Your error definitions (edit to add more)
    │
    ▼
scripts/run_pipeline.py     ← Orchestrator (runs daily via GitHub Actions)
    │
    ├──► src/generator.py   ← Calls Gemini API → saves Markdown to content/
    │
    └──► src/site_builder.py ← Renders HTML from Markdown + Jinja2 templates
              │
              ▼
          site/             ← Static HTML site (deployed to GitHub Pages)
              ├── index.html
              ├── errors/<slug>.html
              ├── sitemap.xml
              └── robots.txt
```

---

## One-time setup

### Prerequisites

- A GitHub account (free)
- A Google AI Studio account (free) — [aistudio.google.com](https://aistudio.google.com)

### Step 1 – Fork / clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/error-fix-engine.git
cd error-fix-engine
```

### Step 2 – Get a Gemini API key (free)

1. Go to [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Click **"Create API key"** → copy it

### Step 3 – Add the secret to GitHub

1. Open your repo on GitHub
2. **Settings → Secrets and variables → Actions → New repository secret**
3. Name: `GEMINI_API_KEY`
4. Value: paste your Gemini key
5. Click **Save**

### Step 4 – Enable GitHub Pages

1. **Settings → Pages**
2. **Source** → **GitHub Actions**
3. Save

### Step 5 – Update the base URL

Open `.github/workflows/deploy.yml`.
The `BASE_URL` environment variable is already set dynamically to:

```
https://<your-username>.github.io/error-fix-engine
```

Nothing to change — it uses `${{ github.repository_owner }}` automatically.

### Step 6 – Trigger the first run

Push a small change (or click **Actions → Generate & Deploy → Run workflow**).

The first run will generate all 35 articles and deploy them.
It takes roughly **4–6 minutes** (2-second polite delay between Gemini calls).

---

## Adding more errors (scaling)

Open `config/errors.yaml` and add a new entry:

```yaml
- tool: Stripe
  error_code: "card_declined"
  error_name: "Stripe card_declined error"
  description: "The payment card was declined by the issuer"
  context: API
  tags: [stripe, payments, api]
  related: [openai-401]
```

The next daily run will generate an article for it automatically.
No other changes required.

---

## Adding Google AdSense

1. Sign up at [adsense.google.com](https://adsense.google.com) (needs a
   live site with real content — do this after your first 20 pages are published)
2. Get your publisher script tag (`<script async src="https://pagead2.googlesyndicatio
n.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX"...>`)
3. Open `templates/base.html` and paste it inside the clearly marked
   `<!-- PASTE YOUR GOOGLE ADSENSE SCRIPT TAG HERE -->` comment block
4. Optionally replace the `<div class="ad-slot">` placeholders in
   `templates/error_page.html` and `templates/index.html` with real
   `<ins class="adsbygoogle">` ad units
5. Commit and push — the next deploy will include the ads

---

## Adding affiliate links

Open `templates/base.html`. In the `<footer>` section you will see:

```html
<!-- AFFILIATE LINKS – replace the href values below -->
<a href="#" rel="nofollow sponsored" target="_blank">AWS Free Tier</a>
<a href="#" rel="nofollow sponsored" target="_blank">Google Cloud</a>
<a href="#" rel="nofollow sponsored" target="_blank">DigitalOcean $200 credit</a>
```

Replace each `href="#"` with your affiliate URL:

| Provider | Affiliate programme |
|----------|---------------------|
| AWS | [aws.amazon.com/partners](https://aws.amazon.com/partners) |
| Google Cloud | [cloud.google.com/partners](https://cloud.google.com/partners) |
| DigitalOcean | [digitalocean.com/referral](https://www.digitalocean.com/referral) |
| Vultr | [vultr.com/referral](https://www.vultr.com/referral/) |
| Linode / Akamai | [linode.com/referral](https://www.linode.com/referral) |

You can also add tool-specific affiliate links inside
`templates/error_page.html` in the sidebar CTA card.

---

## Running locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Generate + build (requires GEMINI_API_KEY)
export GEMINI_API_KEY=your_key_here
python -m scripts.run_pipeline

# Build only (no API calls, uses existing Markdown in content/)
python -m scripts.run_pipeline --build-only

# Dry run (see what would be generated, no API calls)
python -m scripts.run_pipeline --dry-run

# Serve the site locally
python -m http.server 8080 --directory site/
# then open http://localhost:8080
```

---

## File structure

```
error-fix-engine/
├── .github/
│   └── workflows/
│       └── deploy.yml          # Daily cron + GitHub Pages deploy
├── config/
│   └── errors.yaml             # 35 error definitions (edit to add more)
├── content/
│   ├── generated.yaml          # Tracks which slugs are already done
│   └── errors/
│       └── <slug>.md           # Generated Markdown articles
├── logs/
│   └── pipeline.jsonl          # Structured JSON log (CI artifacts)
├── scripts/
│   └── run_pipeline.py         # Main orchestrator script
├── site/                       # Built static site (deployed to Pages)
│   ├── index.html
│   ├── sitemap.xml
│   ├── robots.txt
│   ├── assets/style.css
│   └── errors/
│       └── <slug>.html
├── src/
│   ├── config_loader.py        # Loads & validates errors.yaml
│   ├── generator.py            # Gemini API content generation
│   ├── logger.py               # Structured logging (structlog)
│   ├── models.py               # ErrorEntry / GeneratedArticle dataclasses
│   └── site_builder.py         # Markdown → HTML static site builder
├── templates/
│   ├── assets/
│   │   └── style.css           # Source CSS (copied into site/assets/)
│   ├── base.html               # Master layout (AdSense slot here)
│   ├── error_page.html         # Individual error page
│   ├── index.html              # Homepage
│   └── sitemap.xml             # Sitemap template
├── .gitignore
├── pyproject.toml
├── README.md
└── requirements.txt
```

---

## SEO strategy

Every generated page includes:

- **H1** matching the exact Google search query
- **Meta description** and **Open Graph** tags
- **JSON-LD** structured data (`TechArticle` schema)
- **Canonical URL** to avoid duplication
- **Internal links** between related errors
- **`sitemap.xml`** submitted to Google Search Console
- **`robots.txt`** allowing full indexing

Google typically indexes new pages within **1–4 weeks** of the sitemap being
submitted.

---

## Realistic earnings projection

| Monthly visitors | AdSense RPM | Monthly ad revenue |
|-----------------|------------|-------------------|
| 1 000           | $5         | ~$5               |
| 5 000           | $5         | ~$25              |
| 20 000          | $6         | ~$120             |
| 100 000         | $7         | ~$700             |

To grow traffic faster:
- Add **more errors** (`config/errors.yaml` is the only lever you need to pull)
- Submit the sitemap to [Google Search Console](https://search.google.com/search-console)
- Add **long-tail variations** (e.g. `openai-429-python`, `openai-429-node`)

---

## Safety & secrets

- The `GEMINI_API_KEY` is **only ever read from the environment** — it is
  never written to a file, never printed in logs, and never committed
- All API calls are retried up to 4 times with exponential back-off
- If one article fails, the rest of the batch continues
- `[skip ci]` is appended to auto-commits so they don't trigger an
  infinite loop of Actions runs

---

## Licence

MIT — do whatever you like with this.
