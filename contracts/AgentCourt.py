# v0.3.0

from genlayer import *
import typing


class AgentCourt(gl.Contract):

    # ---------------------------------------------------------
    # Persistent storage
    # ---------------------------------------------------------

    next_agreement_id: bigint

    agreement_buyer: TreeMap[str, str]
    agreement_seller: TreeMap[str, str]
    agreement_terms: TreeMap[str, str]
    agreement_amount: TreeMap[str, bigint]
    agreement_deadline: TreeMap[str, bigint]
    agreement_evidence: TreeMap[str, str]
    agreement_seller_claim: TreeMap[str, str]
    agreement_buyer_claim: TreeMap[str, str]
    agreement_verdict: TreeMap[str, str]
    agreement_completion: TreeMap[str, bigint]
    agreement_confidence: TreeMap[str, bigint]
    agreement_evidence_summary: TreeMap[str, str]
    agreement_reasoning: TreeMap[str, str]
    agreement_status: TreeMap[str, str]
    agreement_settled: TreeMap[str, bool]

    # ---------------------------------------------------------
    # Status
    # ---------------------------------------------------------

    STATUS_CREATED = "CREATED"
    STATUS_FUNDED = "FUNDED"
    STATUS_DELIVERED = "DELIVERED"
    STATUS_DISPUTED = "DISPUTED"
    STATUS_ADJUDICATING = "ADJUDICATING"
    STATUS_RESOLVED = "RESOLVED"
    STATUS_SETTLED = "SETTLED"

    # ---------------------------------------------------------
    # Verdict
    # ---------------------------------------------------------

    VERDICT_PENDING = "PENDING"
    VERDICT_FULFILLED = "FULFILLED"
    VERDICT_PARTIAL = "PARTIALLY_FULFILLED"
    VERDICT_NOT_FULFILLED = "NOT_FULFILLED"
    VERDICT_UNDETERMINED = "UNDETERMINED"

    def __init__(self):
        self.next_agreement_id = 1

    # ---------------------------------------------------------
    # Create
    # ---------------------------------------------------------

    @gl.public.write
    def create_agreement(
        self,
        seller: str,
        terms: str,
        amount: int,
        deadline: int
    ) -> int:

        if not seller:
            raise gl.vm.UserError("INVALID_SELLER")

        if not terms:
            raise gl.vm.UserError("INVALID_TERMS")

        if amount <= 0:
            raise gl.vm.UserError("INVALID_AMOUNT")

        if deadline <= 0:
            raise gl.vm.UserError("INVALID_DEADLINE")

        agreement_id = int(self.next_agreement_id)
        key = str(agreement_id)

        self.next_agreement_id += 1

        self.agreement_buyer[key] = str(
            gl.message.sender_address
        ).lower()

        self.agreement_seller[key] = seller
        self.agreement_terms[key] = terms
        self.agreement_amount[key] = amount
        self.agreement_deadline[key] = deadline

        self.agreement_evidence[key] = ""
        self.agreement_seller_claim[key] = ""
        self.agreement_buyer_claim[key] = ""

        self.agreement_verdict[key] = self.VERDICT_PENDING
        self.agreement_completion[key] = 0
        self.agreement_confidence[key] = 0

        self.agreement_evidence_summary[key] = ""
        self.agreement_reasoning[key] = ""

        self.agreement_status[key] = self.STATUS_CREATED
        self.agreement_settled[key] = False

        return agreement_id

    # ---------------------------------------------------------
    # Fund
    # ---------------------------------------------------------

    @gl.public.write
    def fund_agreement(self, agreement_id: int) -> None:

        key = self._key(agreement_id)

        status = self.agreement_status[key]

        if status != self.STATUS_CREATED:
            raise gl.vm.UserError("INVALID_STATUS")

        sender = str(gl.message.sender_address).lower()

        if sender != self.agreement_buyer[key].lower():
            raise gl.vm.UserError("ONLY_BUYER")

        self.agreement_status[key] = self.STATUS_FUNDED

    # ---------------------------------------------------------
    # Delivery
    # ---------------------------------------------------------

    @gl.public.write
    def submit_delivery(
        self,
        agreement_id: int,
        evidence: str,
        seller_claim: str
    ) -> None:

        key = self._key(agreement_id)

        if self.agreement_status[key] != self.STATUS_FUNDED:
            raise gl.vm.UserError("INVALID_STATUS")

        sender = str(gl.message.sender_address).lower()

        if sender != self.agreement_seller[key].lower():
            raise gl.vm.UserError("ONLY_SELLER")

        if not evidence:
            raise gl.vm.UserError("MISSING_EVIDENCE")

        self.agreement_evidence[key] = evidence
        self.agreement_seller_claim[key] = seller_claim
        self.agreement_status[key] = self.STATUS_DELIVERED

    # ---------------------------------------------------------
    # Dispute
    # ---------------------------------------------------------

    @gl.public.write
    def open_dispute(
        self,
        agreement_id: int,
        buyer_claim: str
    ) -> None:

        key = self._key(agreement_id)

        if self.agreement_status[key] != self.STATUS_DELIVERED:
            raise gl.vm.UserError("INVALID_STATUS")

        sender = str(gl.message.sender_address).lower()

        if sender != self.agreement_buyer[key].lower():
            raise gl.vm.UserError("ONLY_BUYER")

        if not buyer_claim:
            raise gl.vm.UserError("MISSING_BUYER_CLAIM")

        self.agreement_buyer_claim[key] = buyer_claim
        self.agreement_status[key] = self.STATUS_DISPUTED

    # ---------------------------------------------------------
    # Adjudication
    # ---------------------------------------------------------

    @gl.public.write
    def adjudicate(self, agreement_id: int) -> typing.Any:

        key = self._key(agreement_id)

        if self.agreement_status[key] != self.STATUS_DISPUTED:
            raise gl.vm.UserError("INVALID_STATUS")

        self.agreement_status[key] = self.STATUS_ADJUDICATING

        terms = self.agreement_terms[key]
        seller_claim = self.agreement_seller_claim[key]
        buyer_claim = self.agreement_buyer_claim[key]
        evidence = self.agreement_evidence[key]

        def leader_fn():

            prompt = f"""
You are the decentralized adjudicator for an
agent-to-agent commerce agreement.

Determine whether the seller fulfilled the contractual
obligations.

Do NOT guess.
Use ONLY the agreement terms and submitted evidence.

AGREEMENT TERMS:
{terms}

SELLER CLAIM:
{seller_claim}

BUYER DISPUTE:
{buyer_claim}

EVIDENCE:
{evidence}

Return ONLY valid JSON:

{{
    "verdict":
        "FULFILLED | PARTIALLY_FULFILLED | NOT_FULFILLED | UNDETERMINED",
    "completion_percent": 0,
    "confidence": 0,
    "evidence_summary": "...",
    "reasoning": "..."
}}

Rules:

- FULFILLED means evidence supports complete fulfillment.
- PARTIALLY_FULFILLED means evidence supports incomplete
  but meaningful fulfillment.
- NOT_FULFILLED means evidence supports failure.
- UNDETERMINED means evidence is insufficient or contradictory.
- completion_percent must be 0 to 100.
- confidence must be 0 to 100.
- Never invent evidence.
"""

            return gl.nondet.exec_prompt(
                prompt,
                response_format="json"
            )

        def validator_fn(result):

            if not isinstance(result, gl.vm.Return):
                return False

            data = result.calldata

            if not isinstance(data, dict):
                return False

            verdict = data.get("verdict")

            allowed = [
                self.VERDICT_FULFILLED,
                self.VERDICT_PARTIAL,
                self.VERDICT_NOT_FULFILLED,
                self.VERDICT_UNDETERMINED,
            ]

            if verdict not in allowed:
                return False

            try:
                completion = int(
                    data.get("completion_percent", 0)
                )

                confidence = int(
                    data.get("confidence", 0)
                )

            except (TypeError, ValueError):
                return False

            if completion < 0 or completion > 100:
                return False

            if confidence < 0 or confidence > 100:
                return False

            if not isinstance(
                data.get("evidence_summary", ""),
                str
            ):
                return False

            if not isinstance(
                data.get("reasoning", ""),
                str
            ):
                return False

            return True

        result = gl.vm.run_nondet(
            leader_fn,
            validator_fn
        )

        if not isinstance(result, dict):
            raise gl.vm.UserError("INVALID_ADJUDICATION")

        verdict = result.get("verdict", "")

        allowed = [
            self.VERDICT_FULFILLED,
            self.VERDICT_PARTIAL,
            self.VERDICT_NOT_FULFILLED,
            self.VERDICT_UNDETERMINED,
        ]

        if verdict not in allowed:
            raise gl.vm.UserError("INVALID_VERDICT")

        completion = int(
            result.get("completion_percent", 0)
        )

        confidence = int(
            result.get("confidence", 0)
        )

        if completion < 0 or completion > 100:
            raise gl.vm.UserError("INVALID_COMPLETION")

        if confidence < 0 or confidence > 100:
            raise gl.vm.UserError("INVALID_CONFIDENCE")

        self.agreement_verdict[key] = verdict
        self.agreement_completion[key] = completion
        self.agreement_confidence[key] = confidence

        self.agreement_evidence_summary[key] = str(
            result.get("evidence_summary", "")
        )

        self.agreement_reasoning[key] = str(
            result.get("reasoning", "")
        )

        self.agreement_status[key] = self.STATUS_RESOLVED

        return result

    # ---------------------------------------------------------
    # Settlement
    # ---------------------------------------------------------

    @gl.public.write
    def settle(self, agreement_id: int) -> typing.Any:

        key = self._key(agreement_id)

        if self.agreement_settled[key]:
            raise gl.vm.UserError("ALREADY_SETTLED")

        if self.agreement_status[key] != self.STATUS_RESOLVED:
            raise gl.vm.UserError("NOT_RESOLVED")

        completion = int(
            self.agreement_completion[key]
        )

        amount = int(
            self.agreement_amount[key]
        )

        seller_amount = (
            amount * completion // 100
        )

        buyer_refund = (
            amount - seller_amount
        )

        self.agreement_settled[key] = True
        self.agreement_status[key] = self.STATUS_SETTLED

        return {
            "seller_amount": seller_amount,
            "buyer_refund": buyer_refund,
            "verdict": self.agreement_verdict[key],
        }

    # ---------------------------------------------------------
    # Read
    # ---------------------------------------------------------

    @gl.public.view
    def get_agreement(
        self,
        agreement_id: int
    ) -> dict:

        key = self._key(agreement_id)

        return {
            "agreement_id": agreement_id,
            "buyer": self.agreement_buyer[key],
            "seller": self.agreement_seller[key],
            "terms": self.agreement_terms[key],
            "amount": self.agreement_amount[key],
            "deadline": self.agreement_deadline[key],
            "evidence": self.agreement_evidence[key],
            "seller_claim": self.agreement_seller_claim[key],
            "buyer_claim": self.agreement_buyer_claim[key],
            "verdict": self.agreement_verdict[key],
            "completion_percent": self.agreement_completion[key],
            "confidence": self.agreement_confidence[key],
            "evidence_summary": self.agreement_evidence_summary[key],
            "reasoning": self.agreement_reasoning[key],
            "status": self.agreement_status[key],
            "settled": self.agreement_settled[key],
        }

    # ---------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------

    def _key(self, agreement_id: int) -> str:

        key = str(agreement_id)

        if key not in self.agreement_status:
            raise gl.vm.UserError(
                "AGREEMENT_NOT_FOUND"
            )

        return key
