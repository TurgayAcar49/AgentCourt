# AgentCourt ⚖️

### The dispute layer for autonomous commerce.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AgentCourt is a GenLayer Intelligent Contract that resolves disputes between a buyer agent and a seller agent. When the buyer disputes a delivery, GenLayer validators each read the agreement, the evidence and any evidence URL, reach their own verdict, and only accept the leader's ruling if they independently agree. The contract then turns that ruling into deterministic settlement accounting.

> **GenLayer decides. The contract executes.**

---

## Verified on GenLayer Studio

The full lifecycle has been run on chain with real LLM adjudication. Every transaction below finalized with a successful GenVM result and validator agreement.

| | |
|---|---|
| Network | GenLayer Studio Dev, chain ID `61997`, RPC `https://studio-dev.genlayer.com/api` |
| Contract | [`0xa071AB5acedC606F9Fb7557c52803a6Bf4738Bb0`](https://explorer-studio-dev.genlayer.com/address/0xa071AB5acedC606F9Fb7557c52803a6Bf4738Bb0) |
| Deploy transaction | [`0x1b435778…d28debac`](https://explorer-studio-dev.genlayer.com/tx/0x1b435778734e95e29039addd8fd29f70d1092a610e56939564b638c6d28debac) |

| Agreement | Path | Adjudication transaction | On-chain verdict | Settlement |
|---|---|---|---|---|
| #2 Competitive analysis, 14 of 20 companies delivered | dispute → adjudicate → settle | [`0x3b2f5339…b0f1d115`](https://explorer-studio-dev.genlayer.com/tx/0x3b2f5339ea6f6c3bf0880804e1740145e5fbf3e24e86700e48ed50adb0f1d115) | `PARTIALLY_FULFILLED` 70% | seller 700 / refund 300 |
| #3 Pricing page claimed at `https://example.com` | dispute → validators fetch the URL → settle | [`0x01a1864c…cbf7b276`](https://explorer-studio-dev.genlayer.com/tx/0x01a1864c90bf9f17c040b5af7141775b6400d1fbe0b589a6b807628dcbf7b276) | `NOT_FULFILLED` 0% | seller 0 / refund 500 |
| #1 Translation accepted by the buyer | accept → settle | no adjudication needed | `FULFILLED` 100% | seller 200 / refund 0 |

[`demo/RUN.md`](demo/RUN.md) lists every transaction hash of all three agreements, the terms and evidence that were submitted, and the evidence summary and reasoning stored on chain. The raw receipts are in [`demo/runs/`](demo/runs/).

In agreement #3 the seller only submitted a URL. The validators rendered `https://example.com` themselves, found the IANA placeholder page instead of a pricing page, and ruled against the seller:

> The fetched page at https://example.com is the standard IANA example domain placeholder page. It contains no pricing information, no subscription tiers, no tier names (Starter, Growth, Enterprise), and no prices in EUR or any other currency.

> The GenLayer explorer currently labels every call to this contract as `(constructor)` in its Method column. The transactions are the lifecycle calls listed in `demo/RUN.md`.

---

## Lifecycle

```text
                   create_agreement (buyer)
                            │
                   fund_agreement (buyer)
                            │
          ┌─────────────────┴──────────────────┐
          │                                    │
 submit_delivery (seller)            deadline passes without delivery
 before the deadline                           │
          │                          reclaim_expired (buyer)
          │                          → NOT_FULFILLED, 0%
          │
 ┌────────┼──────────────────────────────┐
 │        │                              │
 │  accept_delivery (buyer)     3-day dispute window
 │  → FULFILLED, 100%           passes in silence
 │                                       │
 │                         finalize_undisputed (anyone)
 │                         → FULFILLED, 100%
 │
 open_dispute (buyer, within 3 days of delivery)
          │
 adjudicate (buyer or seller) ── GenLayer consensus
          │
          └──────────────► RESOLVED ──► settle (anyone) ──► SETTLED
```

Every path ends in `RESOLVED` with a verdict and a completion percentage, so an agreement can never get stuck waiting for one party.

| Status | Meaning |
|---|---|
| `CREATED` | Agreement recorded, not yet funded |
| `FUNDED` | Buyer has committed; seller can deliver until the deadline |
| `DELIVERED` | Evidence submitted; the 3-day dispute window is open |
| `DISPUTED` | Buyer disputed the delivery; waiting for adjudication |
| `RESOLVED` | Verdict and completion are final; `resolution` records how |
| `SETTLED` | Settlement accounting has been computed and recorded |

---

## How adjudication works

`adjudicate` runs a single `gl.vm.run_nondet` block.

1. **Leader.** If the evidence contains a URL, the leader renders it with `gl.nondet.web.render`. It builds the prompt and calls `gl.nondet.exec_prompt` with `response_format="json"`.
2. **Validators re-judge.** Each validator renders the URL and runs the prompt on its own model. It accepts the leader's result only if:
   - the leader's ruling is well formed and internally consistent, and
   - the validator reached the **same verdict**, with a **completion percentage within 10 points**.

   A validator never accepts a ruling just because it is valid JSON.
3. **Verdict and completion must agree.** Settlement pays the seller by completion percentage, so the contract derives one from the other:

   | Verdict | Completion used for settlement |
   |---|---|
   | `FULFILLED` | 100 |
   | `PARTIALLY_FULFILLED` | 1–99 (the model's value, clamped) |
   | `NOT_FULFILLED` | 0 |
   | `UNDETERMINED` | 0, so the burden of proof is on the seller |

4. **Party text is fenced.** Terms, claims, evidence and fetched pages sit between `<<<BEGIN …>>>` / `<<<END …>>>` markers. The prompt tells the model to treat everything inside them as data and to ignore any instructions it contains. Input sizes are bounded: terms and evidence 4,000 characters, claims 2,000, fetched page 6,000, stored reasoning 1,000.

Malformed model output (an unknown verdict, out-of-range numbers, missing fields) aborts the transaction, and the agreement stays `DISPUTED`.

---

## Contract interface

| Method | Caller | Effect |
|---|---|---|
| `create_agreement(seller, terms, amount, deadline)` | buyer | Records an agreement. `seller` must be a valid address other than the buyer; `deadline` is a future Unix timestamp. Returns the agreement ID. |
| `fund_agreement(id)` | buyer | `CREATED → FUNDED` |
| `submit_delivery(id, evidence, seller_claim)` | seller | `FUNDED → DELIVERED`, only before the deadline |
| `accept_delivery(id)` | buyer | `DELIVERED → RESOLVED` as `FULFILLED` |
| `finalize_undisputed(id)` | anyone | `DELIVERED → RESOLVED` as `FULFILLED`, after the dispute window |
| `reclaim_expired(id)` | buyer | `FUNDED → RESOLVED` as `NOT_FULFILLED`, after a missed deadline |
| `open_dispute(id, buyer_claim)` | buyer | `DELIVERED → DISPUTED`, within the dispute window |
| `adjudicate(id)` | buyer or seller | `DISPUTED → RESOLVED` through GenLayer consensus |
| `settle(id)` | anyone | `RESOLVED → SETTLED`; returns `seller_amount`, `buyer_refund`, `verdict`, `resolution` |
| `get_agreement(id)` | view | Full agreement state, including the stored ruling |
| `get_agreement_count()` | view | Number of agreements created |

Time checks use the transaction datetime that GenVM exposes to the contract, so every validator evaluates them identically.

---

## Scope of this version

- **No custody.** `fund_agreement` records a state change, and `settle` records how much the seller and buyer are owed. The contract does not hold or transfer GEN or tokens; payment rails would be wired to the settlement result.
- **One evidence URL.** Only the first URL in the evidence is fetched.
- **Single adjudication.** There is no appeal step inside the contract beyond GenLayer's own consensus rotations.

---

## Running locally

### Tests

The tests run in GenLayer's direct mode, with mocked LLM and web responses, against the GenVM v0.6 SDK that Studio uses.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests
```

The first run downloads the GenVM v0.6.0-rc8 runner bundle (about 300 MB) into `~/.cache/gltest-direct`.

The suite covers the full lifecycle and the following:

- validators rejecting a different verdict, a completion outside tolerance, a tampered leader result, or a leader error
- verdict and completion consistency, and malformed model output
- evidence URLs reaching the prompt, unreachable URLs, and fenced party text
- the delivery deadline, the dispute window, buyer acceptance and expiry refunds
- access control and double settlement
- picklability of the `run_nondet` closures

`tests/test_agentcourt_integration.py` deploys to a local GenLayer node at `http://127.0.0.1:4000/api` and is skipped when none is running.

### Run the demo on Studio

Requires Node.js 20 or newer.

```bash
npm install
npm run demo        # deploys a fresh contract and runs all three agreements
npm run report      # rewrites demo/RUN.md from the recorded receipts
```

The demo funds two throwaway accounts through Studio's `sim_fundAccount` and stores their keys in `.demo-accounts.json`, which is git-ignored. Options:

| Variable | Effect |
|---|---|
| `NETWORK=studionet` | Use `https://studio.genlayer.com/api` instead of Studio Dev |
| `CONTRACT_ADDRESS=0x…` | Reuse a deployed contract |
| `SCENARIOS=partial,web,accept` | Run a subset of the agreements |
| `BUYER_PRIVATE_KEY`, `SELLER_PRIVATE_KEY` | Use your own accounts |

The demo uses `genlayer-js` 2.0, which sends the fee distribution that Studio Dev now requires. Each transaction requests 10× Studio's default execution budget, because adjudication renders a web page and runs an LLM on every validator.

---

## Repository structure

```text
contracts/AgentCourt.py   Intelligent Contract
tests/                    direct-mode tests and localnet deploy test
scripts/demo.mjs          end-to-end run on GenLayer Studio
scripts/report.mjs        builds demo/RUN.md from recorded runs
demo/RUN.md               verified on-chain run with all transaction hashes
demo/runs/                raw receipts of each run
```

---

## Roadmap

- Custody and payout of GEN or ERC-20 tokens driven by `settle`
- Multiple evidence URLs and file evidence
- An appeal step with additional evidence for `UNDETERMINED` rulings
- Agent identity and reputation derived from settled agreements

## License

[MIT](LICENSE)
