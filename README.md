# Webnovel Emailer

A small Python + GitHub Actions project for turning **public-domain or otherwise authorized serial fiction** into low-noise email reading batches.

## What it does

- Discovers chapter links from a configured source page.
- Extracts chapter titles and, when explicitly authorized, chapter text.
- Remembers reading progress in `data/state.json`.
- Sends a configurable number of chapters in **one email per run** so your inbox does not get flooded.
- Runs manually or on a schedule with GitHub Actions.
- Includes a GitHub Pages setup helper in `docs/` that generates a safe configuration file without collecting passwords.

## Important content-use rule

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
batch renderer ---> Gmail SMTP ---> one digest email
      ^
      |
GitHub Actions schedule / manual run
```

## Quick start

1. Copy `config.example.yaml` to `config.yaml`.
2. Set your source URL, CSS selectors, recipient email, batch size, and delivery mode.
3. In GitHub go to **Settings → Secrets and variables → Actions** and add:
   - `GMAIL_ADDRESS`
   - `GMAIL_APP_PASSWORD`
4. Run **Actions → Deliver reading batch → Run workflow**.
5. Optional: enable GitHub Pages using the `docs/` folder for the configuration helper.

Google currently requires 2-Step Verification before an App Password can be created for eligible accounts. Never commit the App Password to the repository.

## Configuration

```yaml
source:
  index_url: "https://example.org/book/"
  chapter_link_selector: "a.chapter-link"
  chapter_title_selector: "h1"
  chapter_body_selector: "article.chapter"
  allowed_domain: "example.org"

delivery:
  recipient: "you@example.com"
  chapters_per_email: 3
  delivery_mode: "links_only" # links_only | full_text
  rights_confirmed: false
  subject_prefix: "Reading batch"

schedule:
  enabled: true
```

## GitHub Pages helper

`docs/index.html` is a static setup helper. It does **not** collect or store Gmail credentials. It generates a `config.yaml` you can download and place in the repository.

## Project structure

```text
.github/workflows/deliver.yml
config.example.yaml
data/state.json
docs/
src/
tests/
requirements.txt
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp config.example.yaml config.yaml
python -m src.main --config config.yaml --dry-run
```

Run tests:

```bash
pytest -q
```

## Security

- Gmail credentials live only in GitHub Actions secrets.
- The Pages helper never asks for an App Password.
- The workflow gets only the permissions it needs.
- `config.yaml` may contain a recipient address, so use a private repository if you do not want that address public.

## Portfolio angle

This repository demonstrates web parsing, stateful automation, SMTP integration, GitHub Actions, static front-end configuration, testing, and safe credential handling in one compact project.

## License

Code in this repository is MIT licensed. Content retrieved from third-party sources remains subject to the source material's rights and terms.
