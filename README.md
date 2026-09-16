# AgentCourt

### The dispute layer for autonomous commerce.

AgentCourt is an agent-to-agent commerce protocol that combines escrow,
evidence and GenLayer adjudication.

## Core flow

Buyer Agent
→ Agreement
→ Escrow
→ Seller Delivery
→ Evidence
→ Dispute
→ GenLayer Adjudication
→ Deterministic Settlement

## Verdicts

- FULFILLED
- PARTIALLY_FULFILLED
- NOT_FULFILLED
- UNDETERMINED

## Principle

GenLayer decides.

The smart contract executes the decision.

## Architecture

AgentCourt separates subjective dispute resolution from deterministic
settlement.

1. Buyer creates an agreement.
2. Buyer funds the agreement.
3. Seller submits delivery evidence and a claim.
4. Buyer can open a dispute.
5. GenLayer adjudicates using the agreement terms and submitted evidence.
6. The contract stores the verdict, completion percentage, confidence,
   evidence summary and reasoning.
7. Settlement is calculated deterministically by the smart contract.

If evidence is insufficient or contradictory, the adjudicator can return
`UNDETERMINED` instead of guessing.

## Live Studio Deployment

Contract:

`0x1794c95d3f2c5e93924735a7630e602e9f5444bbfc0566dbd0e26861450d5a1a`

### Verified end-to-end flow

| Step | Transaction |
|---|---|
| CREATE | `0x6671ac4f9e5ba1159848722ce539174f868a2f7a247753cd439ec90d2bbd8fc8` |
| FUND | `0x69b64e0220164745bc25e1f6f44811f82f4216bda7a058176444c8e9f5955297` |
| DELIVERY | `0x28f478ae8facc2fdb4109fd0ad27c3350fed5c46318021ee382d42d873e30f27` |
| DISPUTE | `0xb21a93337e624397ea64e9ab9d14104d31e7583382c60c98c881a8133bbb6533` |
| ADJUDICATE | `0x88032f685228889012de86658d2b54cd9ef911d461982feb7b49d226bbba8787` |
| SETTLE | `0x4a814ae0b6d31401b7422dc9b42188176d5cf38c22c31a41fbcace918b3a593c` |

### Adjudication result

- Status: `RESOLVED`
- Verdict: `FULFILLED`
- Completion: `100%`
- Confidence: `100%`
- Settlement: `100`
- Buyer refund: `0`

## Status

MVP — AgentCourt V0.1

Live Studio flow verified end-to-end.
