# Webnovel Emailer

A Python + GitHub Actions project for turning serial-fiction chapter feeds into **low-noise reading digests**. The project discovers chapter links, remembers delivery progress, batches several chapters into one email, and can send the same reading batch privately to multiple recipients.

## Live setup page

GitHub Pages: `https://marco-yan.github.io/Webnovel-Emailer/`

The setup dashboard uses the project palette:

```css
:root {
  --background: #F7F6F0;
  --text: #171A18;
  --primary: #214E3B;
  --secondary: #82906A;
  --highlight: #C5A46D;
}
```

The Pages interface generates the non-secret GitHub Actions variables. Gmail credentials remain in GitHub Secrets and are never entered into the website.

## What it does

- Discovers chapter links from a configured source/index page.
- Deduplicates discovered chapters and tracks reading-delivery progress in `data/state.json`.
- Sends a configurable number of chapters in **one digest per run**.
- Supports one or many recipients through `RECIPIENT_EMAILS`.
- Sends each recipient a separate email so recipient addresses are not exposed to one another.
- Runs manually in preview/dry-run mode or automatically on GitHub Actions.
- Current scheduled cadence: Monday, Wednesday, and Friday at 12:00 UTC.
- Includes a responsive GitHub Pages configuration dashboard and email preview.
- Supports links-only delivery by default and authorized full-text extraction when explicitly enabled.

## Content-use rule

This project is intentionally **not configured to copy paywalled, copyrighted, or unauthorized third-party novels**. The default delivery mode is `links_only`. Full-text delivery requires both:

1. `delivery_mode: full_text`
2. `rights_confirmed: true`

Use full-text mode only for material you wrote, material in the public domain, or material you have permission to reproduce.

## Architecture

```text
Source index / TOC
      |
      v
chapter discovery ---> dedupe / ordering
      |
      v
extractor (links-only OR authorized full text)
      |
      v
progress state (`data/state.json`)
      |
      v
batch renderer
      |
      v
Gmail SMTP ---> Reader A
           ---> Reader B
           ---> Reader C
      ^
      |
GitHub Actions schedule / manual run
```

## GitHub configuration

### Repository Secrets

Add these under **Settings → Secrets and variables → Actions → Secrets**:

- `GMAIL_ADDRESS`
- `GMAIL_APP_PASSWORD`

Never commit Gmail credentials to the repository.

### Repository Variables

The Pages dashboard generates these under **Settings → Secrets and variables → Actions → Variables**:

- `SOURCE_INDEX_URL`
- `SOURCE_ALLOWED_DOMAIN`
- `RECIPIENT_EMAILS`
- `CHAPTERS_PER_EMAIL`
- `DELIVERY_MODE`
- `RIGHTS_CONFIRMED`
- `CHAPTER_LINK_SELECTOR`
- `CHAPTER_TITLE_SELECTOR`
- `CHAPTER_BODY_SELECTOR`

`RECIPIENT_EMAILS` accepts comma-, semicolon-, or newline-separated addresses. The legacy `RECIPIENT_EMAIL` variable is still accepted for backwards compatibility.

## Configuration example

```yaml
source:
  index_url: "https://example.org/book/"
  chapter_link_selector: "a.chapter-link"
  chapter_title_selector: "h1"
  chapter_body_selector: "article.chapter"
  allowed_domain: "example.org"

delivery:
  recipients:
    - "reader.one@example.com"
    - "reader.two@example.com"
  chapters_per_email: 3
  delivery_mode: "links_only"
  rights_confirmed: false
  subject_prefix: "Reading batch"
```

## First run

1. Add the two Gmail repository secrets.
2. Open the GitHub Pages dashboard.
3. Enter the source URL and one or more recipient emails.
4. Generate the repository variables and add them to GitHub.
5. Open **Actions → Deliver reading batch**.
6. Use **Run workflow** with `dry_run=true` to verify chapter discovery without sending email.
7. When the preview is correct, run again with `dry_run=false`.

## Project structure

```text
.github/workflows/deliver.yml
.github/workflows/pages.yml
config.example.yaml
data/state.json
docs/index.html
src/main.py
src/mailer.py
src/scraper.py
tests/
requirements.txt
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp config.example.yaml config.yaml
python -m src.main --config config.yaml --dry-run
```

Run tests:

```bash
pytest -q
```

## Security and privacy

- Gmail credentials live only in GitHub Actions secrets.
- The Pages dashboard never asks for or stores the Gmail App Password.
- Recipient addresses are sent as separate messages rather than one visible group message.
- The workflow restricts chapter traversal to the configured source domain.
- The workflow gets only the repository permissions required to save delivery progress.

## Portfolio angle

This repository demonstrates web parsing, stateful automation, SMTP integration, secrets management, multi-recipient delivery, GitHub Actions scheduling, static front-end configuration, responsive UI work, testing, and deployment through GitHub Pages.

## License

Code in this repository is MIT licensed. Content retrieved from third-party sources remains subject to the source material's rights and terms.
