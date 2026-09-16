# AgentCourt ⚖️

### The dispute layer for autonomous commerce.

**AgentCourt** is an agent-to-agent commerce protocol designed to resolve disputes between autonomous agents using **GenLayer adjudication** and deterministic smart-contract settlement.

As autonomous agents begin to negotiate, purchase services, deliver work, and exchange value without direct human intervention, a critical question emerges:

> **What happens when two autonomous agents disagree about whether an agreement was fulfilled?**

AgentCourt provides a structured dispute-resolution layer for this problem.

---

## 🚀 The Core Idea

Traditional smart contracts are good at executing predefined rules.

But autonomous commerce often involves questions that are difficult to express as deterministic code:

* Was the requested work actually completed?
* Does the delivered result satisfy the agreement?
* How much of the work was completed?
* Is the submitted evidence sufficient?
* Should the seller receive the full amount, a partial amount, or nothing?

AgentCourt uses **GenLayer** to adjudicate these evidence-based disputes.

The core principle is simple:

> **GenLayer decides.**
> **The smart contract executes the decision.**

---

## 🔄 Core Flow

```text
Agreement
    ↓
Funding
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

* seller
* terms
* amount
* deadline

The agreement becomes the reference point for evaluating delivery.

---

### 2. Funding

The agreement is funded before the seller completes the work.

This creates a committed economic context for the transaction.

---

### 3. Delivery

The seller submits the completed work together with supporting evidence.

The evidence can be used by the adjudication process to determine whether the agreed requirements were satisfied.

---

### 4. Dispute

If the buyer believes the delivery does not satisfy the agreement, the buyer can open a dispute and provide a claim explaining the disagreement.

---

### 5. GenLayer Adjudication

AgentCourt sends the relevant agreement terms, delivery information, claims, and evidence to **GenLayer** for adjudication.

The adjudication produces a structured verdict containing:

* verdict
* completion percentage
* confidence
* evidence summary
* reasoning

The supported verdicts are:

| Verdict               | Meaning                                                         |
| --------------------- | --------------------------------------------------------------- |
| `FULFILLED`           | The agreement was fulfilled                                     |
| `PARTIALLY_FULFILLED` | Part of the agreement was fulfilled                             |
| `NOT_FULFILLED`       | The agreement was not fulfilled                                 |
| `UNDETERMINED`        | The available evidence is insufficient to determine fulfillment |

---

### 6. Deterministic Settlement

The adjudication result is converted into a deterministic settlement.

For a completion percentage of `70%`:

```text
Agreement Amount: 100

Seller:          70
Buyer Refund:    30
```

The smart contract applies the resulting completion percentage according to the settlement logic.

This separates:

**Adjudication → Decision**

from

**Settlement → Execution**

---

### 7. Verification

After settlement, the agreement retains its resulting state and adjudication information, allowing the outcome to be inspected and verified.

---

## 🧠 Why GenLayer?

The difficult part of autonomous commerce is not always moving assets.

The difficult part is determining whether an offchain or semi-structured outcome satisfies an agreement.

For example:

```text
Buyer Agent:
"Deliver a market research report containing
20 companies and a competitive analysis."

Seller Agent:
"Work completed."

Buyer Agent:
"The report only contains 12 companies
and is missing the competitive analysis."

Dispute:
"What percentage of the agreement was fulfilled?"
```

A traditional deterministic contract cannot easily interpret the quality and completeness of the submitted evidence.

AgentCourt delegates this adjudication problem to GenLayer and uses the resulting structured decision for settlement.

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
                │     Funding      │
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
              │  GenLayer            │
              │  Adjudication        │
              └──────────┬───────────┘
                         │
                  Structured Verdict
                         │
                         ▼
              ┌──────────────────────┐
              │ Deterministic        │
              │ Settlement           │
              └──────────┬───────────┘
                         │
                         ▼
                     Resolution
```

---

## 📋 Agreement Lifecycle

An agreement moves through explicit protocol states:

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

This lifecycle makes the dispute process explicit and auditable.

---

## ⚖️ Adjudication Model

The adjudication result is structured rather than returned as an unvalidated free-form response.

Conceptually:

```json
{
  "verdict": "PARTIALLY_FULFILLED",
  "completion": 70,
  "confidence": 85,
  "evidence_summary": "...",
  "reasoning": "..."
}
```

AgentCourt validates the returned values before accepting the adjudication result.

The completion value is constrained to a percentage between `0` and `100`.

---

## 🔐 Smart Contract Operations

The AgentCourt contract exposes the core protocol operations:

```text
create_agreement(...)
fund_agreement(...)
submit_delivery(...)
open_dispute(...)
adjudicate(...)
settle(...)
get_agreement(...)
```

These operations represent the complete agreement lifecycle from creation to resolution.

---

## 💡 Example Use Case

Imagine two autonomous agents:

### Buyer Agent

Requests:

> "Create a competitive analysis of 20 companies and deliver the final report before the deadline."

### Seller Agent

Accepts the agreement and submits the report.

### Dispute

The buyer claims that:

* only 14 companies were analyzed
* several required sections are missing

The seller claims:

> "The requested research was substantially completed."

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

GenLayer evaluates the dispute and returns a structured adjudication.

For example:

```text
Verdict: PARTIALLY_FULFILLED
Completion: 70%
```

The settlement layer then applies the resulting percentage deterministically.

---

## 🌐 GenLayer Integration

AgentCourt uses GenLayer's nondeterministic execution capability for dispute adjudication.

The adjudication process is designed around:

```text
Evidence
   ↓
GenLayer Evaluation
   ↓
Structured Verdict
   ↓
Validation
   ↓
Settlement
```

This is the key architectural distinction of AgentCourt:

**The contract does not attempt to determine subjective fulfillment itself.**

Instead:

**GenLayer evaluates the dispute.**

Then:

**The contract executes the resulting settlement logic.**

---

## 📍 Deployment

AgentCourt is deployed on **GenLayer Studio Next / Studio Dev**.

| Property      | Value                                                                |
| ------------- | -------------------------------------------------------------------- |
| Network       | GenLayer Studio Dev                                                  |
| Chain ID      | `61997`                                                              |
| RPC           | `https://studio-dev.genlayer.com/api`                                |
| Contract      | `0x0C7609876C68418E3A949da0FCaDEd265c79d7ce`                         |
| Deployment Tx | `0x1794c95d3f2c5e93924735a7630e602e9f5444bbfc0566dbd0e26861450d5a1a` |

### Contract Explorer

[View AgentCourt Contract on GenLayer Explorer](https://explorer-studio-dev.genlayer.com/address/0x0C7609876C68418E3A949da0FCaDEd265c79d7ce?utm_source=chatgpt.com)

---

## 🧪 Project Status

**MVP — AgentCourt V0.1**

The current implementation demonstrates the complete conceptual dispute lifecycle:

```text
Agreement
→ Funding
→ Delivery
→ Evidence
→ Dispute
→ Adjudication
→ Resolution
→ Settlement
```

The project is focused on demonstrating the core architecture for dispute resolution in autonomous commerce.

---

## 🛣️ Roadmap

Future versions can extend AgentCourt with:

* richer evidence formats
* more sophisticated agreement templates
* agent identity and reputation
* multi-party agreements
* automated dispute triggering
* additional settlement mechanisms
* reusable adjudication policies
* integrations with agent marketplaces
* production-grade asset custody and payment rails

---

## 🎯 Why AgentCourt?

Autonomous agents can already perform increasingly complex actions.

The next challenge is **trust between agents**.

When agents negotiate and transact independently, a complete commerce stack needs more than:

```text
Discovery
+
Payment
+
Execution
```

It also needs:

```text
Agreement
+
Evidence
+
Dispute Resolution
+
Settlement
```

AgentCourt explores this missing layer.

### The vision

> **Autonomous commerce needs autonomous dispute resolution.**

AgentCourt is an attempt to build that layer using GenLayer.

---

## 📁 Repository

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

[AgentCourt Repository](https://github.com/TurgayAcar49/AgentCourt?utm_source=chatgpt.com)

**GenLayer Explorer**

[AgentCourt Contract](https://explorer-studio-dev.genlayer.com/address/0x0C7609876C68418E3A949da0FCaDEd265c79d7ce?utm_source=chatgpt.com)

---

## ⚖️ Core Principle

```text
GenLayer decides.

The smart contract executes.

AgentCourt connects the two.
```

### AgentCourt

**The dispute layer for autonomous commerce.**
