# AgentCourt ⚖️

### The dispute layer for autonomous commerce.

**AgentCourt** is an agent-to-agent commerce protocol prototype designed to resolve disputes between autonomous agents using **GenLayer adjudication** and deterministic settlement logic.

As autonomous agents begin to negotiate, purchase services, deliver work, and exchange value with less human intervention, a critical question emerges:

> **What happens when two autonomous agents disagree about whether an agreement was fulfilled?**

AgentCourt explores a programmable dispute-resolution layer for that problem.

---

## 🚀 Why AgentCourt Exists

Autonomous commerce introduces a problem that traditional deterministic smart contracts do not easily solve: **judging whether a real-world or semi-structured deliverable actually satisfies an agreement.**

For example:

> A buyer agent requests a research report. A seller agent submits the result. The buyer claims that important requirements are missing. Who determines how much of the agreement was actually fulfilled?

AgentCourt separates this problem into two layers:

```text
GenLayer → evaluates the dispute
Smart Contract → applies the resulting settlement logic
```

The core principle is simple:

> **GenLayer decides.**
> **The smart contract executes.**

---

## 🔄 Core Flow

```text
Agreement
    ↓
Funding State
    ↓
Seller Delivery
    ↓
Evidence Submission
    ↓
Dispute
    ↓
GenLayer Adjudication
    ↓
Deterministic Settlement
    ↓
Verification
```

The protocol turns a potentially subjective dispute into a structured onchain workflow.

---

## 🧩 How AgentCourt Works

### 1. Agreement

A buyer and seller establish an agreement containing:

- seller
- terms
- amount
- deadline

The agreement becomes the reference point for evaluating delivery.

### 2. Funding State

The buyer moves the agreement into the `FUNDED` state before delivery.

**Important MVP scope:** the current prototype records this funding state but does **not** custody or transfer USDC/tokens. Production asset custody and payment rails are future work.

### 3. Delivery

The seller submits the completed work together with supporting evidence.

### 4. Dispute

If the buyer believes the delivery does not satisfy the agreement, the buyer can open a dispute and provide a claim explaining the disagreement.

### 5. GenLayer Adjudication

AgentCourt sends the relevant agreement terms, delivery information, claims, and evidence to **GenLayer** for adjudication.

The adjudication produces a structured result containing:

- verdict
- completion percentage
- confidence
- evidence summary
- reasoning

Supported verdicts:

| Verdict | Meaning |
|---|---|
| `FULFILLED` | The agreement was fulfilled |
| `PARTIALLY_FULFILLED` | Part of the agreement was fulfilled |
| `NOT_FULFILLED` | The agreement was not fulfilled |
| `UNDETERMINED` | Available evidence is insufficient to determine fulfillment |

### 6. Deterministic Settlement

The adjudication result is converted into deterministic settlement accounting.

For a completion percentage of `70%`:

```text
Agreement Amount: 100

Seller Allocation: 70
Buyer Refund:      30
```

The current MVP **calculates and records these settlement values**; it does not execute token transfers.

This separates:

**Adjudication → Decision**

from

**Settlement → Deterministic Execution Logic**

### 7. Verification

After settlement, the agreement retains its resulting state and adjudication information so the outcome can be inspected.

---

## 🧠 Why GenLayer?

The difficult part of autonomous commerce is not always moving assets. The difficult part can be determining whether an offchain or semi-structured outcome satisfies an agreement.

Traditional deterministic code can enforce explicit rules, but it is poorly suited to questions such as:

- Was the requested work actually completed?
- Does the delivered result satisfy the agreement?
- How much of the work was completed?
- Is the submitted evidence sufficient?

AgentCourt delegates this evidence-based adjudication problem to GenLayer and uses the resulting structured decision in its settlement logic.

---

## 🏗️ Architecture

```text
                  AUTONOMOUS COMMERCE
                         │
                         ▼
                ┌──────────────────┐
                │     Agreement    │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │  Funding State   │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │ Seller Delivery  │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │     Evidence     │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │     Dispute      │
                └────────┬─────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │      GenLayer       │
              │     Adjudication    │
              └──────────┬───────────┘
                         │
                  Structured Verdict
                         │
                         ▼
              ┌──────────────────────┐
              │ Deterministic        │
              │ Settlement Logic     │
              └──────────┬───────────┘
                         │
                         ▼
                     Resolution
```

---

## 📋 Agreement Lifecycle

```text
CREATED
   ↓
FUNDED
   ↓
DELIVERED
   ↓
DISPUTED
   ↓
ADJUDICATING
   ↓
RESOLVED
   ↓
SETTLED
```

Each state makes the dispute process explicit and auditable.

---

## ⚖️ Adjudication Model

The adjudication result is structured and validated rather than accepted as arbitrary free-form output.

Conceptual result:

```json
{
  "verdict": "PARTIALLY_FULFILLED",
  "completion": 70,
  "confidence": 85,
  "evidence_summary": "...",
  "reasoning": "..."
}
```

AgentCourt validates the returned values before accepting the adjudication result. The completion value is constrained to `0–100`.

---

## 🔐 Smart Contract Operations

```text
create_agreement(...)
fund_agreement(...)
submit_delivery(...)
open_dispute(...)
adjudicate(...)
settle(...)
get_agreement(...)
```

These operations represent the agreement lifecycle from creation to resolution.

---

## 💡 Example Use Case

Imagine two autonomous agents:

**Buyer Agent**

> Create a competitive analysis of 20 companies and deliver the final report before the deadline.

**Seller Agent**

Accepts the agreement and submits the report.

**Dispute**

The buyer claims that only 14 companies were analyzed and required sections are missing. The seller claims the research was substantially completed.

AgentCourt collects:

```text
Agreement Terms
       +
Seller Delivery
       +
Evidence
       +
Buyer Claim
       +
Seller Claim
```

GenLayer evaluates the dispute and can return, for example:

```text
Verdict: PARTIALLY_FULFILLED
Completion: 70%
```

The settlement logic then deterministically calculates the corresponding allocation and refund.

---

## 🧪 Tests

The repository includes direct and integration tests covering the core lifecycle and failure paths, including:

- agreement creation and lifecycle transitions
- funding and delivery flow
- dispute handling
- GenLayer adjudication with structured verdict validation
- deterministic settlement calculation
- rejection and invalid-state cases
- deployment/integration smoke testing

The adjudication/settlement tests also exercise a mocked structured GenLayer result such as `PARTIALLY_FULFILLED` at `70%` completion to verify settlement accounting.

---

## 🌐 GenLayer Integration

AgentCourt uses GenLayer's nondeterministic execution capability for dispute adjudication.

Conceptually:

```text
Evidence
   ↓
GenLayer Evaluation
   ↓
Structured Verdict
   ↓
Validation
   ↓
Settlement Logic
```

The contract does not attempt to determine subjective fulfillment itself.

**GenLayer evaluates the dispute.**

**AgentCourt applies the resulting settlement logic.**

---

## 📍 Deployment

AgentCourt is deployed on **GenLayer Studio Dev**.

| Property | Value |
|---|---|
| Network | GenLayer Studio Dev |
| Chain ID | `61997` |
| RPC | `https://studio-dev.genlayer.com/api` |
| Contract | `0x0C7609876C68418E3A949da0FCaDEd265c79d7ce` |
| Deployment Tx | `0x1794c95d3f2c5e93924735a7630e602e9f5444bbfc0566dbd0e26861450d5a1a` |

### Contract Explorer

[View AgentCourt Contract on GenLayer Explorer](https://explorer-studio-dev.genlayer.com/address/0x0C7609876C68418E3A949da0FCaDEd265c79d7ce)

---

## 📊 Project Status

**MVP — AgentCourt V0.1**

The current implementation demonstrates the complete conceptual dispute lifecycle:

```text
Agreement
→ Funding State
→ Delivery
→ Evidence
→ Dispute
→ Adjudication
→ Resolution
→ Settlement Accounting
```

The prototype focuses on the core architecture for dispute resolution in autonomous commerce. Asset custody and actual token movement are intentionally outside the current MVP.

---

## 🛣️ Roadmap

Future versions can extend AgentCourt with:

- production-grade asset custody and payment rails
- richer evidence formats
- more sophisticated agreement templates
- agent identity and reputation
- multi-party agreements
- automated dispute triggering
- additional settlement mechanisms
- reusable adjudication policies
- integrations with agent marketplaces

---

## 🎯 The Bigger Picture

As agents increasingly act on behalf of people and organizations, commerce needs more than discovery, execution, and payment.

It also needs a way to handle disagreements when autonomous parties interpret an agreement differently.

AgentCourt explores that missing layer:

```text
Agent Discovery
      ↓
Agreement
      ↓
Execution
      ↓
Evidence
      ↓
Dispute Resolution
      ↓
Settlement
```

> **Autonomous commerce needs autonomous dispute resolution.**

---

## 📁 Repository Structure

```text
AgentCourt/
├── contracts/
├── tests/
├── gltest.config.yaml
└── README.md
```

The repository contains the smart-contract implementation, test suite, GenLayer configuration, and project documentation.

---

## 🔗 Project Links

**GitHub**

[AgentCourt Repository](https://github.com/TurgayAcar49/AgentCourt)

**GenLayer Explorer**

[AgentCourt Contract](https://explorer-studio-dev.genlayer.com/address/0x0C7609876C68418E3A949da0FCaDEd265c79d7ce)

---

## ⚖️ Core Principle

```text
GenLayer decides.

The smart contract executes the decision logic.

AgentCourt connects the two.
```

### AgentCourt

**The dispute layer for autonomous commerce.**
