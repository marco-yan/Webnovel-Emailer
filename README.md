# Webnovel Emailer

Webnovel Emailer turns a web-novel chapter range into clean Gmail reading batches without making the reader touch GitHub, edit YAML, or know CSS selectors.

## End-user flow

1. Paste a novel URL.
2. The app detects the title and chapter count.
3. Choose an inclusive chapter range, such as **30 through 400**.
4. Choose how many chapters should go in each email, such as **10**.
5. Enter one or more recipient email addresses.
6. Press **Send selected chapters**.

For the example above, 371 selected chapters become 38 emails per recipient.

The public web interface deliberately hides developer configuration. GitHub remains the code repository, not the product UI.

## Interface

The UI uses the project palette:

```css
:root {
  --background: #F7F6F0;
  --text: #171A18;
  --primary: #214E3B;
  --secondary: #82906A;
  --highlight: #C5A46D;
}
```

The main screen contains only three steps: novel link, chapter range/batch size, and recipients. Advanced scraper selectors and GitHub variables are no longer part of the reader-facing workflow.

## Web architecture

```text
Browser
  |
  | 1. Paste novel URL
  v
POST /api/novel
  |
  v
Automatic chapter detection
  |
  | title + chapter count
  v
Range picker
  |
  | 2. Select 30-400, batch size 10
  v
POST /api/send
  |
  v
Batch planner
  |
  v
Gmail SMTP
  |----> Reader A
  |----> Reader B
  `----> Reader C
```

The production target is Vercel. `vercel.json` serves the minimal interface and Python API functions from the same application, so end users never need to visit GitHub.

GitHub Pages remains available as a static front-end preview during development.

## Automatic chapter detection

`src/scraper.py` now supports automatic discovery rather than requiring end users to supply CSS selectors.

- LightNovelWorld has a dedicated adapter that reads the reported chapter count and constructs its numbered chapter routes.
- Other sites use generic numbered-chapter link detection.
- Additional source adapters can be added without changing the public UI.

The browser-facing application sends chapter titles and source links. It does not bulk-copy third-party novel prose.

## Multiple recipients

Recipients may be separated by commas, semicolons, or new lines. Duplicate addresses are removed. Each person receives an individual email so recipient addresses are not exposed to one another.

## Safety limits

The web endpoint limits a single request to 50 batch emails and 100 total outbound messages across all recipients. This prevents an accidental chapter selection from flooding an inbox or exhausting Gmail/Vercel execution limits.

## Deployment

### Vercel - intended production deployment

Connect this GitHub repository to a Vercel project and add these environment variables:

- `GMAIL_ADDRESS`
- `GMAIL_APP_PASSWORD`

No reader-facing configuration is required after deployment. The app calls `/api/novel` and `/api/send` behind the scenes.

### GitHub

The repository still contains the older GitHub Actions delivery workflow as a backend/fallback implementation. It is not the intended reader experience.

## Project structure

```text
api/
  novel.py             # detect title + chapter range
  send.py              # send selected range in batches
src/
  scraper.py           # automatic source adapters
  mailer.py            # Gmail SMTP
  web_service.py       # recipients, ranges, batching
  main.py              # legacy CLI / Actions path
docs/
  index.html           # minimal public interface
tests/
vercel.json
requirements.txt
```

## Example

A reader pastes a novel with 500 detected chapters and chooses:

```text
Start chapter:        30
End chapter:          400
Chapters per email:   10
```

The range is inclusive:

```text
400 - 30 + 1 = 371 chapters
ceil(371 / 10) = 38 emails per recipient
```

The last email contains chapter 400 rather than silently dropping the remainder.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q
```

## Security

- Gmail credentials are environment secrets, never browser fields.
- Recipient addresses are not stored by the web API.
- Source traversal is restricted to the novel's own domain.
- Third-party novel text is not reproduced by the public web workflow.

## Portfolio angle

The project demonstrates product simplification, web scraping/adapters, inclusive range logic, batching, multi-recipient email delivery, serverless Python APIs, secret management, automated testing, and deployment architecture while keeping the actual reader experience intentionally simple.

## License

Code in this repository is MIT licensed. Content on third-party source websites remains subject to the source site's rights and terms.
