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

Note the Node version: wrangler 4 wants Node 22. On Node 20, pin it:

```bash
npx wrangler@3 pages deploy build/site --project-name asset-researcher
```

### Making it private, which is the default you probably want

A `*.pages.dev` URL is public and indexable the moment it exists. A demo
sent to a handful of named people should not be either, and the fix is
Cloudflare Access, which is free for up to 50 users and sits in front of
the site as a real identity check rather than a shared secret.

In the Cloudflare dashboard: **Zero Trust → Access → Applications → Add
an application → Self-hosted**. Point it at the Pages hostname, then add
one policy:

- Action: **Allow**
- Include: **Emails** (list the addresses) or **Emails ending in** (a
  company domain)

Leave the identity provider as the built-in **One-time PIN**. A recipient
opens the link, types their email, receives a six-digit code, and is in.
No account to create, nothing for them to install, and you can revoke an
address later without moving the site.

Two things worth knowing before you rely on it:

- **Add the policy before you share the link, not after.** Between
  deploying and attaching the policy the site is open, and that window is
  long enough to be indexed.
- **Access protects the hostname, not the files.** Anything that is also
  committed to a public branch is still public through that branch. Keep
  generated notes out of the repository; `build/` is gitignored for this
  reason.

GitHub Pages is the wrong host for a private demo. Pages on a private
repository is a paid feature, and on a public repository the published
branch is readable by anyone regardless of the Pages setting. Deleting
the branch does not unpublish the site either: the last deployment keeps
serving until Pages is set to **None** in the repository settings.

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

### Keeping the live tool private

**Cloudflare Access cannot protect this one.** Access works by sitting in
front of a hostname that routes through Cloudflare, and a
`*.streamlit.app` address does not. Two options that do work:

**Streamlit's own viewer list**, which is the simple answer. In the app's
settings, set it to private and add viewer emails. The cost is that a
viewer needs a Google account and has to sign in with it, which is a
larger ask of a busy reader than a six-digit code.

**A Cloudflare Tunnel from your own machine**, which keeps everything on
one access model. Run the app locally, expose it through a tunnel, and
put the same Access policy in front of the tunnel hostname that guards
the notes:

```bash
streamlit run app.py --server.port 8501 &
npx wrangler@3 tunnel --url http://localhost:8501
```

Same one-time-PIN flow as the notes, no Google account, no secrets on
anyone else's infrastructure, and the API key never leaves your machine.
The cost is that the link only works while your machine is awake, which
makes it right for a scheduled call and wrong for "have a look whenever".

**Whichever you pick, the spend caps still matter.** Private means the
people who can reach it are named, not that they cannot spend your
balance: each report is a real API call against your key. Keep a separate
key on anything deployed, and read the section below.

### Before you make that link public

The spend caps in `asset_researcher/config/settings.yaml` are the only
thing between a public URL and your API balance:

```yaml
hosting:
  spend_cap_daily_usd: 10
  spend_cap_session_usd: 3
```

**Neither cap is as strong as it looks, and the daily one is the weaker.**
It is backed by `data/spend.json`, a file on local disk. Streamlit
Community Cloud has an ephemeral filesystem, so that file goes with the
container: the counter resets on every restart, redeploy and wake from
sleep. It bounds a stretch of continuous uptime, not a calendar day. The
per-session cap lives in Streamlit's session state, so it resets when a
visitor reloads the page.

Read together, that means **a determined visitor can spend more than
either number**, and the real bound on your exposure is the credit
balance on the key itself. At about $1.30 a report:

- Set the caps below the balance, not at it. A cap above what the account
  holds is not a cap; it just means the key runs dry and everyone after
  that meets an authentication error instead of a budget message.
- Put a separate key on the deployment, not the one you develop with, and
  fund it with only what you are willing to lose.
- Anthropic's console has its own spend limits. That one is enforced
  server-side and is the only hard stop in this list.

If the link is going somewhere genuinely public rather than to a handful
of named people, lead with the static sample and keep the live tool for
people you can name.

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
