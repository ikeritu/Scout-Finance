---
name: price-data-source-pilot
description: Use this skill whenever evaluating, researching, or piloting a candidate financial data source for Scout Finance — a provider API (EODHD-style, J-Quants-style), an official exchange endpoint, a government open-data portal, or an identifier-mapping service like OpenFIGI. Trigger on requests like "evalúa esta fuente de datos", "mira si X tiene una API oficial", "pilota esta fuente para precios de Y bolsa", "es viable esta fuente para NUESTRO universo de símbolos bloqueados", or any request to research, test, or validate a candidate source for prices, fundamentals, or identifiers — even if the user doesn't say "pilot" or "skill" explicitly. Covers desk research before touching credentials, fail-closed resolve/download scripts, local validation and aggregate reporting, evidence-classified documentation, and the git safety checklist this project uses before every commit.
---

# Price data source pilot

Scout Finance has run this same evaluation shape a dozen times now (EODHD, Twelve Data, J-Quants, OpenFIGI/Cboe Europe, TWSE, ASX, BVC) and the pattern holds regardless of the provider: some pass, most don't, and the value is in reaching a well-evidenced answer fast without ever risking the project's credentials, its git history, or its licensed data. This skill is the scaffolding for that — not a shortcut around the actual research, which is genuinely different every time.

## Why the shape matters

Every step below exists because skipping it caused a real problem in an earlier pilot this project ran. Fail-closed resolution exists because guessing a symbol match once would poison every price series built on top of it. Atomic writes exist because a plain `open(path, "w")` truncated a real CSV mid-session when an unrelated exception fired partway through. The rate-limit backoff exists because a provider's documented "5/min" produced real 429s at that exact pace. Treat these as load-bearing, not decorative.

## The workflow

Work through these stages in order. Not every pilot needs every stage — a desk-only evaluation (like ruling out ASX) stops at stage 1 if the answer is already clear; a full pilot (like J-Quants) goes all the way through.

### 1. Desk research first — before writing code or touching credentials

Before anything executable: read the provider's actual documentation. Confirm (with citations, not guesses):
- Does this need an account or API key at all? If yes, **you never create the account or enter credentials yourself** — see "Credentials" below.
- What's the real rate limit, and does the free/no-cost tier even cover the market(s) you need? (Twelve Data's free tier looked promising until the docs turned out to gate every non-US exchange behind a paid plan — that's a five-minute finding if you check exchange-by-exchange before writing a line of code.)
- What historical depth does the plan actually offer? Look for the provider's own stated limits, not marketing copy — often the real limit only surfaces when you deliberately request more than allowed and read the error message (EODHD's free plan announces its own 1-year cap *inside* the price response; J-Quants and TWSE both stated their exact boundary date in an error message when asked).
- What does the license say about redistribution, caching, and derived results? Quote it, don't paraphrase from memory.

If the desk research already gives a clear no (official policy requires a paid license, the only public endpoint is confirmed dead, etc.), write that up and stop — you don't need scripts to reach `NO_FREE_SOURCE_FOUND`. See ASX and BVC in this project's history for what that closure looks like.

### 2. Credentials — read this before any pilot that needs one

**Never create an account, register, or enter a password/API-key-request form on the user's behalf**, even if explicitly asked. Tell the user exactly what to do instead: which page to sign up on, and what to name the environment variable once they have the credential (e.g. `SCOUT_FINANCE_<PROVIDER>_API_KEY`). Never let a credential value appear in chat, in a script's stdout, in an error message, or in anything committed to git.

On Windows, a credential the user just set with `[Environment]::SetEnvironmentVariable(...,"User")` won't be visible to a shell process that was already running when they set it. Don't assume it's missing — check the registry-backed value directly and inject it into just the one command that needs it:

```powershell
$env:SCOUT_FINANCE_PROVIDER_API_KEY = [Environment]::GetEnvironmentVariable("SCOUT_FINANCE_PROVIDER_API_KEY","User")
& python scripts\the_script.py ...
Remove-Item Env:\SCOUT_FINANCE_PROVIDER_API_KEY
```

This lets you verify presence (`[bool]$value`, maybe its length) without ever printing the value itself.

### 3. One minimal live probe before committing to a full run

Before writing the real resolve/download scripts, make one or two calls by hand to confirm: auth actually works, the response schema matches what the docs said, and the ticker/identifier convention you expect (e.g. "does our internal ticker map directly to the provider's code, or does it need a suffix/padding?") is correct. This is cheap and it's what catches things like "the master endpoint pads 4-digit codes with a trailing zero" before you've built 40 minutes of pipeline around a wrong assumption.

### 4. Resolve script — fail-closed, no guessing

If the pilot needs symbol/entity resolution (mapping an internal ticker or company name to the provider's identifier), the resolver's only job is to say "yes, exact match" or "unresolved" — never "probably." Concretely:

- Match on an **exact** normalized string (or an explicit code lookup), never a fuzzy/similarity score.
- A normalization step (case, punctuation, common legal suffixes like `AG`/`SE`/`PLC`/`INC`/`-REG`) is fine and often necessary — but log what it stripped, and if a specific suffix pattern is blocking real matches, add it deliberately (as happened with `-REG` for J-Quants search) rather than loosening the match criteria in general.
- Zero candidates, multiple distinct candidates, or a call failure all resolve to the same outcome: **unresolved**, with a specific machine-readable reason (`no_exact_normalized_name_match`, `ambiguous_multiple_distinct_companies_matched`, `code_not_found`, etc.) — never a best-guess pick.
- If the provider rate-limits you (HTTP 429 is common even under a documented pace), catch it specifically, sleep, and retry a bounded number of times before giving up on that one item — don't let a transient rate limit produce a false "unresolved."

### 5. Download script — fail-closed, resumable, atomic

- Requires an explicit `--execute` flag in addition to having the credential set — this makes "did I actually authorize a real network pull" a conscious, visible decision every time the script is invoked, not an accident of forgetting to check a flag.
- Resumable: skip any output file that already exists rather than re-fetching it. Real pilots in this project have taken 10–25 minutes; being interruptible and restartable without loss matters.
- **Atomic writes, no exceptions** — write to `<final_path>.tmp` then `Path.replace()` it onto the final path. This applies to every script that writes a file for this pilot, including one-off scratch scripts you write to merge or patch something mid-session — an ad-hoc `open(path, "w")` used to "quickly fix" a CSV is exactly what corrupted one earlier in this project's history, because a `DictWriter` field mismatch threw partway through the write and left a truncated file with no way to tell without reading it.
- Never let a credential or a full URL containing one leak into a failure record, a report, or stdout. Log only structured, non-secret fields: `pilot_id`, `error_type`, `http_status`. If you need to confirm a fix by re-reading provider error text, read it, but don't propagate it verbatim if it could ever contain a token.
- If the provider's TLS setup is broken in a specific but recoverable way (e.g. "Missing Subject Key Identifier" — a real defect in one government exchange's cert chain that curl tolerates but Python's default verifier doesn't), fix it with `ssl.create_default_context(cafile=certifi.where())`. **Never disable certificate verification** to work around this — the certifi fix is the actual fix, not a workaround.
- If a provider has added anti-automation measures (a formerly-open endpoint now needs session cookies, a page hangs indefinitely under a headless browser with no observable data call) — that is a stop sign, not a puzzle. Document it as a confirmed dead end and move on; don't reverse-engineer around it.

### 6. Validator + aggregate report builder

A separate script (not the downloader) that reads the raw files back and: checks required fields are present, checks OHLC coherence where applicable (`High >= Open, Close, Low`; `Low <= Open, Close`), checks volume isn't negative, checks dates are ascending with no duplicates, and — critically — **distinguishes real data rows from anything else the provider might embed**. EODHD's free tier puts a literal English sentence announcing its own plan limit as the final row of every price response; treating that as a data point silently inflated an earlier "observations" count by exactly one row per asset. Look for this kind of thing explicitly rather than assuming every returned row is a real observation.

The report this script builds is aggregate only — session counts, date ranges, percentiles, per-market breakdowns — never row-level licensed prices. That's what goes in git; the raw per-security files stay local (add the raw folder to `.gitignore`) regardless of how open the provider's license is, for consistency with how this project already treats every other pilot's raw data.

Make the report **reproducible**: running the validator twice against the same local files should produce byte-identical output. That's also your QA gate — a resolve/collection QA test can just call this same validator and assert the numbers, rather than duplicating the logic.

### 7. Offline QA — no real network, no real credentials

Write tests that mock the network entirely and use an obviously-fake fixture credential (never the real env var's actual value, never even a name that could be mistaken for wanting the real one). Cover at minimum:
- Blocked with no credential set.
- Blocked without `--execute`.
- Resumability: an existing output file means no network call for that item.
- Atomic write: no stray `.tmp` files after a run, and the written file parses as complete JSON.
- Continuation after a simulated HTTP error on one item — the run should finish and report that one failure, not abort.
- No credential or full URL appears anywhere in a failure record or report.
- The resolver's fail-closed logic: exact match resolves, a synthetic ambiguous case (two distinct fixture "companies" with the same normalized name) stays unresolved rather than picking one.

Name these `qa_<pilot>_<thing>.py` and keep them separate from anything that needs the real local licensed data — a second QA script that validates the *real* downloaded collection should print `SKIP` and exit 0 if the raw folder isn't present locally, so it never fails CI over the absence of data nobody has a license to redistribute.

### 8. Document the closure with evidence classified by confidence

See `references/doc-templates.md` for the two-file shape this project uses (`PRICE_PILOT_STATUS_v2_XX.md` + a short `README.md` index) and a worked example. The one rule that matters most: keep **hechos observados** (things you directly observed — a quoted error message, a measured count), **inferencias** (a reasoned conclusion you're drawing from those facts, labeled as such), and **limitaciones no confirmadas** (things you don't know and didn't check) in visibly separate sections. Blurring these is how a coincidence in two test examples (EODHD's `GR` composite code happening to look like it meant "Germany") almost became a stated fact before checking more examples exposed it as wrong.

### 9. Pick a decision status that matches the evidence, not the effort

A clean technical run (0 failures, 0 schema errors) does not automatically mean a source is usable — coverage and matching quality against this project's actual bar are what decide that. Use one of:

| Status | Means |
|---|---|
| `PASS_FOR_NEXT_CONTROLLED_PILOT` | Clears the bar for its actual scope (often a single market, not the whole universe) — not a production promotion. |
| `PARTIAL_PASS_NO_PRODUCTION_PROMOTION` | Some criteria met, others not; more work could plausibly close the gap. Covers two distinct shapes — don't conflate them in the writeup: a real free source that's too *shallow* (SGX's ~22-day rolling window under a non-commercial license) versus entities you could *identify* but can't yet safely *act on* (OpenFIGI naming Cboe Europe companies with no reliable primary-exchange signal — that one's arguably closer to `PARTIAL_IDENTIFICATION_NO_ACTIONABLE_SOURCE` below; pick whichever status name the reader would find less surprising given what actually blocked it). |
| `COMPLETED_NO_PROMOTION` | Pilot executed cleanly but the source fails the bar (e.g. EODHD's ~1-year depth cap). |
| `NO_FREE_SOURCE_FOUND` | Desk research alone answers it — no free/official path exists (e.g. ASX). |
| `PARTIAL_IDENTIFICATION_NO_ACTIONABLE_SOURCE` | You identified the entities but still can't safely act on that (e.g. OpenFIGI naming Cboe Europe companies without a reliable primary-exchange signal). |
| `INCONCLUSIVE_LOW_IMPACT` | Genuinely unresolved, and the scope is small enough that spending more effort isn't justified without the user asking for it. |
| `FAIL` | Clear no. |

This project's current gate reference (from v2.33C) is ≥90% historical coverage, ≥90% symbol-matching accuracy, 0 false matches, and a documented license — check the current source-design doc for whether that's still the live bar before citing it, since it's a project-specific number, not a rule this skill invented.

### 10. Git safety checklist — every single commit, no exceptions

Before staging anything:
1. `git status` — confirm the protected/untracked files this project keeps local-only are still untouched (check the current list; don't assume it hasn't changed).
2. Confirm any new raw-data folder is in `.gitignore` before it's ever created, not after.
3. Stage an **explicit list of files** — never `git add -A` or `git add .`.
4. Run a secret scan on the staged diff: grep for the credential env var name followed by `=`, `api_token=`, `x-api-key`, `bearer `, and any full provider URL that could carry a token as a query param.
5. `git diff --cached --check` for stray whitespace/EOF issues.
6. Show the staged file list before committing.
7. Write a commit message that states the decision and the evidence behind it, not just "add pilot files."

If any of these turns up something wrong, fix it before committing — don't commit and clean up after.

### 11. Update the project's state docs, and remember cross-session

This project keeps ONE running state section at the top of each of `CHANGELOG.md`, `README.md`, and `VERSION.md`, marked with a single HTML comment pair that's stayed named after the *first* pilot that created it (`<!-- SCOUT_FINANCE_V2_33D1_STATE_START/END -->` — don't be misled by the "D1" into thinking each closure gets its own new marker pair). Every closure since then has inserted its own `## v2.XX — ...` subsection **just inside the existing opening marker**, pushing the previous entries down, never creating a second marker pair and never deleting an earlier subsection. Read the current top of each file before editing to confirm you're extending that one block, not starting a new one — the marker name is a historical artifact, not a version-matching requirement.

Then save what you found to the auto-memory system (per this session's own memory instructions) as a `project` memory: what the source is, the decision, the one or two facts a future session would need before re-deriving them (a rate limit that's stricter in practice, a cert quirk, a license restriction, a dead endpoint). This is what actually saves tokens next time — the skill gives you the shape, memory gives you the specific facts you'd otherwise have to rediscover.

## When the user says "keep going" on a data-source thread

Multiple pilots often chain in one sitting (this project ran eight in a row). Before starting the next one, check whether the user actually wants you to pick the next market/provider yourself, or whether a prior closure already flagged an open decision that's theirs to make (e.g. "confirm the license terms before more use," "decide whether to pay for X"). If a memory note or a STATUS.md says a next step needs the user's decision, surface that instead of unilaterally picking a direction — the same restraint that applies to authorizing a paid plan applies to picking which market to chase next when it's genuinely ambiguous.
