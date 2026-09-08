# Recommend Agentic Trust Layer

**A fact-checker for the things you tell your AI agents. It checks a statement against real sources (the web, or your own documents) and tells you whether it holds up, and how sure it is.**

Here's the problem we kept running into. AI answers everything with the same confident
tone, whether it's right or not. Ask a model "how sure are you?" and it says 95% almost
every time. That's fine for a chat. It's not fine when an agent is about to *act* on that
information: write it into a report, put it in a knowledge base, make a decision from it.

So we built the thing that checks first. You give it a statement. It goes and looks, using
real sources fetched right now (never the model's memory), and comes back with three things:

* **Is it true?** A score from 0 to 100.
* **How much should you trust that answer?** A separate confidence number. It drops when
  the sources are thin, out of date, or disagree with each other.
* **Why?** The sources it used and a few sentences of plain-language reasoning.

![A myth goes in, REFUTED comes out with the sources](assets/hero.gif)

You can use it yourself in a web page, plug it into an agent as a tool, or run it over a
whole knowledge base and stamp the files that hold up.

## Try it in two minutes

```bash
git clone https://github.com/recommend-dev/recommend-agentic-trust-layer.git
cd recommend-agentic-trust-layer
pip install -r requirements.txt
cp .env.example .env          # add GEMINI_API_KEY and EXA_API_KEY
python3 server.py             # open http://localhost:8899
```

**Windows, in Git Bash (MINGW64)?** Python buffers stdout there, so the startup banner
(key checks, the URL, the printed demo key) won't show up until the buffer flushes. Run
it unbuffered instead: `python3 -u server.py`.

You need two keys: a free [Gemini](https://aistudio.google.com/apikey) key and an
[Exa](https://exa.ai) key. More keys unlock more sources (see the engineering notes below),
but these two are enough to get going. (Already on Vertex AI? Set
`GOOGLE_APPLICATION_CREDENTIALS` + `GOOGLE_CLOUD_PROJECT` instead of `GEMINI_API_KEY` —
see `.env.example`.)

Type something like *"Humans only use 10% of their brains"* and watch it work.

(This checks one claim at a time. To verify a whole bundle of documents — including
against their own internal citations, not just the web — see
["On a whole knowledge base"](#3-on-a-whole-knowledge-base) below: `python3 okf_server.py`
on a different port, `8898`.)

## What you get back

Here's what it says about *"Sugar makes children hyperactive"*:

```
Verdict:     REFUTED
Truth score: 9 / 100
Confidence:  0.86

3 of 4 evidence sources agree. Lane spread 0.07, consistent.

A 1995 meta-analysis of 23 studies (JAMA) found no effect of sugar on
children's behaviour; the perceived effect is explained by parents'
expectations. Sources: jamanetwork.com, nih.gov, ...
```

The two numbers are independent on purpose. A claim can be clearly false *and* the system
can be very sure about that. Or the evidence can be genuinely split, in which case the
confidence tells you so instead of quietly picking a side.

## How it works, in plain terms

The easiest way to picture it is a small fact-checking desk.

1. **Intake.** The claim gets rewritten into one precise, checkable sentence, split into
   the smaller facts it depends on, and labelled by type (factual, statistical, causal,
   about the future, opinion). One rule here: the claim is never "corrected". If you type
   in a myth, the myth is what gets checked, not its debunking.

2. **Independent researchers.** Several evidence sources go and look at the same time,
   each using only its own tool. We call these *lanes*. There are two different web
   search engines, a live Google index, and, when the claim calls for it, scientific
   literature or a prediction market. Which lanes run depends on the kind of claim. A
   study can settle "does X cause Y"; a news article can't.

3. **A judge for each lane.** Each lane's findings get their own verdict, made only from
   the text that lane actually fetched. The judge is told to say "not enough evidence"
   rather than guess.

4. **Opposing counsel.** Every verdict is then attacked. Does the evidence really cover
   this time period, this population, this exact wording? A verdict that breaks keeps
   only about half its weight.

5. **Adding it up.** The verdicts are combined, weighted by how strong their evidence was.
   If the lanes disagree, confidence goes down. If a lane came back empty, confidence
   also goes down, because silence isn't coverage.

6. **One last check that can only go down.** A final pass looks for overconfidence. It's
   allowed to lower the confidence and never to raise it.

7. **Readout.** Two or three sentences on what the evidence showed, plus the sources.

A few things it refuses to do, on purpose. It won't give a factual verdict on a claim about
the future (you get a lean with capped confidence instead). It won't let a prediction
market decide anything on its own, because that's belief, not fact. And it won't stamp
something it couldn't check.

## Three ways to use it

### 1. Yourself, in the browser

`python3 server.py` and open http://localhost:8899. Type a claim, watch the lanes land,
read the sources. You can also pin a claim, and it gets re-checked daily so you can see
the score move as the evidence changes.

### 2. From an agent, as an MCP tool

Give your agent a `verify_claim` tool and it stops answering factual questions from memory:

```bash
claude mcp add --transport http recommend-trust \
  http://localhost:8899/mcp \
  --header "Authorization: Bearer <key printed at startup>"
```

The tool returns the verdict, both scores, a per-source breakdown and the sources.
A demo key is generated into `keys.json` the first time you run the server.

### 3. On a whole knowledge base

If your agents write into a shared knowledge base (for example in Google's
[Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf)),
each file can carry a `verified:` field. Today that field is just a name someone typed in.
These tools put an actual check behind it. There are two modes:

**Against the world.** Is what this document says actually true?

```bash
python3 okf_verify.py examples/okf-demo      # --dry to report without writing
```

**Against its own citations.** Does the source this document cites really say this?
No web search here; the evidence is the files and links the document itself points to.
This is the mode for internal material the web has no opinion on: policies, metric
definitions, schema docs.

```bash
python3 okf_adapter.py path/to/bundle        # --dry · reports in <bundle>-reports/
```

In both modes a document only gets the `verified` stamp if every checked claim holds up.
Anything refuted, inconclusive or uncheckable stays unstamped, and the reasons are written
into the file and into the bundle's `log.md`. The demo bundle in `examples/okf-demo` shows
all three outcomes:

| File | Result |
|---|---|
| `market/croatia-context.md` | both claims supported, stamped, with ECB/EU sources |
| `market/kids-snacks-positioning.md` | "sugar causes hyperactivity" refuted, not stamped, refuting studies logged |
| `metrics/activation.md` | internal definition, nothing to check on the web, left alone |

The citation-integrity mode gets its own demo: [`examples/okf-citation-demo`](examples/okf-citation-demo)
plants four errors into an otherwise-correct internal bundle (a wrong formula, a fabricated
policy exemption, a claim re-cited to the wrong source, a policy edited out from under a
downstream claim) and shows the adapter catching all four, with the control concept left
verified and untouched.

There's a drag-and-drop UI for this too: `python3 okf_server.py`, then http://localhost:8898 —
or skip the drag-and-drop and click the built-in "☠️ Poisoned bundle" sample to see this exact
demo run without needing a bundle of your own.

## Running it fully local (llama-swap + SearXNG)

No cloud keys at all: a local model does the judging, a self-hosted SearXNG does the
searching, and an optional Byparr reads the pages that block plain HTTP.

```bash
# .env
LLM_BASE_URL=http://192.168.1.10:8080/v1   # llama-swap (or any OpenAI-compatible server)
LLM_MODEL=qwen3-14b                        # model name from your llama-swap config.yaml
SEARXNG_URL=http://192.168.1.20:8080       # JSON API must be on: search.formats: [html, json]
BYPARR_URL=http://192.168.1.21:8191        # optional, for Cloudflare-walled pages
```

What changes and what doesn't:

* The three web lanes keep their names, ids and weights. Behind them, SearXNG finds the
  pages, the fetcher reads them (plain GET, then Byparr if the site refuses), and for the
  "Grounded Web" and "Deep Research" lanes the local model writes the grounded answer from
  those passages, the way Exa's `/answer` does.
* Research Literature and Prediction Market were keyless already and are untouched.
* Cost is reported as 0. Every check still makes 10–15 model calls (structure, a judge and
  an opposing counsel per lane, review, readout) plus 3–6 for the local grounded answers.
  llama-swap serves one model at a time, so expect one to three minutes per claim.
* Model size matters. Below ~8B parameters the judge and the challenge get noisy and the
  confidence number stops meaning much. A 14B-class model with a 16k context is the
  comfortable floor; some prompts carry 14–16k characters of evidence. For a "thinking"
  model set `LLM_MAX_TOKENS_MULT=3` so the reasoning has room, or disable thinking in
  your llama-swap config.
* SearXNG is keyword search where Exa is neural. The three reformulated queries from the
  intake step compensate in part. Prefer `SEARXNG_ENGINES=google,bing,duckduckgo`.

## Deploying with caddy-gui (systemd + Caddy PaaS)

The repo is ready for [caddy-gui](https://github.com/Emilien-Etadam/caddy-gui): a `Procfile`
gives it the start command, `PORT` / `HOST` / `DATA_DIR` injected by systemd are honoured,
and nothing is written inside the release (keys, tracked claims and logs go to `DATA_DIR`).

1. **New app** → repo `Emilien-Etadam/recommend-agentic-trust-layer`, branch `main`.
   Kind is detected as Python, start command comes from the `Procfile`
   (`python -u server.py`). Pick any free port and a hostname such as `trust.eta.lan`.
2. **Tick "accès réseau sortant"** (outbound network). The check fetches evidence from the
   web and talks to your llama-swap / SearXNG / Byparr LXCs; the default unit denies all
   outbound traffic.
3. **Env** tab → paste your `.env` contents (the local block above, or the cloud keys).
   `DATA_DIR` and `PORT` are already set by the unit, don't add them.
4. **Deploy.** The MCP key is printed once in the deploy log and stored in
   `/var/lib/paas-<id>/keys.json`; `journalctl -u paas-<id>` shows it too.

For the OKF verifier UI, create a second app on the same repo with start command
`python -u okf_server.py` and its own port and hostname.

## Things to know before you rely on it

* **Every check costs real API credit.** There are daily caps built in (`PER_IP_DAY=25`,
  `GLOBAL_DAY=400`). Change them in `.env` before you put this on a public host.
* **A missing key isn't an error.** That source just sits the check out, and confidence
  is a bit lower because of it. The verdict tells you which sources actually ran.
* **It's not a search engine.** One check takes 10 to 20 seconds, because it fetches,
  judges and cross-examines. Use it for the things your agent is about to act on, not for
  every sentence it produces.
* **No framework, no build step.** It's one Python file using the standard library, and
  one HTML file. Read it in an afternoon.

## For engineers

<details>
<summary><b>Evidence lanes: what runs when, and which key it needs</b></summary>

| Lane | Runs when | Weight | Provider | Key |
|---|---|---|---|---|
| Grounded Web | always | 1.15 | Exa `/answer` per query · local: SearXNG + fetch + local LLM answer | `EXA_API_KEY` or `SEARXNG_URL` |
| Semantic Web | always | 0.9 | Exa `/search` · local: SearXNG + page text | `EXA_API_KEY` or `SEARXNG_URL` |
| Live Index | always | 0.85 | SerpAPI (Google + answer box) · local: SearXNG snippets + instant answers | `SERPAPI_API_KEY` or `SEARXNG_URL` |
| Deep Research | `deep=1` checkbox | 1.35 | Exa per sub-claim (~7s) · local: SearXNG per sub-claim; `DEEP_ENGINE=parallel` → Parallel.ai (~70s, better citations) | `EXA_API_KEY` / `SEARXNG_URL` / `PARALLEL_API_KEY` |
| Prediction Market | claim type `predictive` | 1.25 | Polymarket Gamma | none |
| Research Literature | claim type `causal` / `statistical` | 1.4 | OpenAlex + Europe PMC | none |

Weights multiply each lane's own evidence strength (0–1, set by the judge). A lane that the
opposing-counsel pass breaks has its strength multiplied by 0.55. The prediction market is
capped at strength 0.35 regardless.

</details>

<details>
<summary><b>How the two numbers are computed</b></summary>

* **Truth score** = weighted average of each lane's `p_true`, weight = lane weight × evidence strength.
* **Confidence** = evidence mass × (1 − 0.55 × spread) × (0.45 + 0.55 × decisiveness), clamped to [0.05, 0.96], where
  *evidence mass* is total weight divided by the number of lanes *started* (so a silent lane counts against you),
  *spread* is the gap between the most and least supportive lane, and
  *decisiveness* is how far the score sits from 50/50.
* A refuted sub-claim caps the score at 45 and confidence at 0.6. Predictive or opinion claims never get
  SUPPORTED/REFUTED; they get LEANS TRUE/FALSE with confidence capped at 0.45.
* The calibration pass (`calibration_review`) may only lower confidence.

Everything lives in `server.py`, sections numbered 1–5 in the source.

</details>

<details>
<summary><b>Behaviour that took work to get right</b></summary>

* **Unfalsifiable claims never get a factual verdict.** "X is going to attack Y" used to
  return REFUTED at 96%. Absence of reporting about the future is not proof.
* **Intake never corrects the claim.** "Humans use 10% of their brain" once got normalized
  to "no areas of the brain are dormant", every lane supported *that*, and the myth scored
  100/100. There is now a second model call that checks the rewritten claim still points
  the same direction, and falls back to the user's wording if it doesn't.
* **Every prompt knows today's date.** Without it, models guess, and penalise good
  evidence for being "in the future".
* **`(p_true or 0.5)` when every lane said 0.** `0.0` is falsy in Python.

</details>

<details>
<summary><b>OKF stamping details</b></summary>

Stamps are spec-conformant and additive: a `verified: {by: recommend-trust-layer/0.1, at: …}`
event (the *machine-confirmed* trust tier per SPEC §5.3) plus an `x_verification`
extension block with per-claim results and sources. Existing frontmatter is never deleted.

Citation-integrity verdicts (`okf_adapter.py`): `supports` · `contradicts` · `related-only` ·
`no-evidence` · `unverifiable` (unreachable source). A claim can be true and still fail
here: true-but-miscited is an attribution failure. A `supports` verdict whose own reasoning
denies support is downgraded mechanically. Needs only a Gemini key; a 26-concept bundle
cost about $0.02 end to end in our test.

Deprecated concepts and Attested Computations are noted and skipped.

</details>

<details>
<summary><b>Deploying, tests, and the second server</b></summary>

**Reverse proxy.** The front-end derives every path from `location.pathname`, so it works
at `/` locally and under any prefix in production. If your proxy buffers responses (Caddy,
nginx), disable buffering for this route (Caddy: `flush_interval -1`) or SSE will never
stream. Set `HOST=0.0.0.0` to listen beyond localhost. A `Dockerfile` is included for the
OKF UI (Cloud Run ready).

**Tests.** Real-Chrome end-to-end tests; the macOS Chrome path is hardcoded, adjust
`executablePath` for your OS.

```bash
cd tests && npm install
node uitest.js      # UI invariants
node tracktest.js   # tracking flow
node cmptest.js     # compare endpoint
node scaletest.js   # layout at widths
```

**Two servers.** `server.py` (port 8899) is the claim checker and MCP endpoint.
`okf_server.py` (port 8898) is the knowledge-base upload UI. Both read the same `.env`.

**Tracking.** Pinned claims are re-checked every `TRACK_EVERY_H` hours (default 24),
scoped per browser session.

</details>

## Roadmap

* **Pluggable lanes.** Add your own evidence source (Brave Search, an internal corpus,
  BigQuery schema checks) without touching the pipeline.
* **Continuous verification.** Re-run on a schedule and on every knowledge-base change,
  so a stamp ages honestly.

## License

[MIT](LICENSE) · built by [Recommend](https://recommend.studio)
