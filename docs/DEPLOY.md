# Deploying

Two surfaces, because they have different jobs.

**A static sample note.** Pre-rendered, loads instantly, costs nothing to
serve, needs no API key. This is the link that goes in an email.

**The live tool.** Takes a ticker and builds a note in about a minute, and
spends an API call doing it. This is the link for someone who wants to
drive it.

---

## The Cloudflare constraint, stated plainly

**Cloudflare Workers cannot host this application.** Workers is a V8 and
WebAssembly edge runtime; Streamlit is a long-running Python process that
holds a websocket open per visitor. Python Workers exist but will not run
Streamlit, and no amount of configuration changes that.

**Cloudflare Pages can host the static sample**, which is the surface that
matters more for a cold introduction. Use the Cloudflare account you
already have for that, and host the live tool on Streamlit Community
Cloud, which is free and deploys from the same GitHub repository.

---

## 1. The static sample, on Cloudflare Pages

Confirm credentials first; a half-built note is worse than none.

```bash
python scripts/check-credentials.py
```

Generate. One API call per ticker, about $1.30 each, paid once rather than
once per visitor.

```bash
python scripts/publish-sample.py --ticker AAPL --ticker JPM --ticker XOM
```

That writes `build/site/`: one page per ticker plus an index. Three tickers
is a good sample because they exercise three different statement shapes, a
technology filer, a bank and an energy filer, which is itself the point
being demonstrated.

Deploy:

```bash
npx wrangler pages deploy build/site --project-name asset-researcher
```

First run asks you to authenticate and creates the project. You get a
`*.pages.dev` URL immediately, and can attach a custom domain in the
Cloudflare dashboard under Workers and Pages.

To refresh later, re-run both commands. The site is static files; there is
nothing to migrate.

## 2. The live tool, on Streamlit Community Cloud

Push the repository to GitHub, then:

1. Sign in at https://share.streamlit.io with the GitHub account that owns
   the repository.
2. **New app**, pick the repository, branch `main`, main file `app.py`.
3. Open **Advanced settings** and set Python to 3.12.
4. Under **Secrets**, paste:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
FINNHUB_API_KEY = "..."
EDGAR_USER_AGENT = "Asset-Researcher research tool you@yourdomain.com"
```

Streamlit exposes those through `st.secrets` rather than the environment,
and `app.py` bridges them into `os.environ` at startup so the config loader
finds them unchanged.

5. Deploy. The first build installs from `requirements.txt` and takes a few
   minutes.

### Before you make that link public

The spend caps in `asset_researcher/config/settings.yaml` are the only
thing between a public URL and your API balance:

```yaml
hosting:
  spend_cap_daily_usd: 25
  spend_cap_session_usd: 6
```

The daily cap is file-backed and real. The per-session cap resets if a
visitor reloads, so the daily cap is the one that actually binds. At about
$1.30 a report, $25 is roughly nineteen reports a day across everyone.
Lower it if the link goes anywhere you do not control.

Streamlit Community Cloud also sleeps an app after a period of inactivity
and takes thirty seconds or so to wake. That is the strongest argument for
leading with the static sample: a reviewer who clicks a cold link and
watches a spinner forms a view before they see anything.

## 3. Alternatives for the live tool

If Streamlit Cloud's sleep behaviour is not acceptable:

| Host | Notes |
| --- | --- |
| Fly.io | Dockerfile, a shared-cpu-1x instance runs this comfortably, no sleep on a paid plan |
| Render | Connects to GitHub like Streamlit Cloud, free tier also sleeps |
| Railway | Simple, usage-billed |

All three need the same three environment variables and `streamlit run
app.py --server.port $PORT --server.address 0.0.0.0`.

## What is deliberately not deployed

The fixture preview (`scripts/preview.py`) writes files stamped
`FIXTURE-DO-NOT-CIRCULATE`. Those combine real filings with placeholder
prose, so they state things about a real company that are not true. They
exist for front-end work and must never be published. `build/` is
gitignored and `publish-sample.py` writes to a separate directory for that
reason.
