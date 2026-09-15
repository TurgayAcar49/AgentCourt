from genlayer import *
import typing
from dataclasses import dataclass


@allow_storage
@dataclass
class Agreement:
    buyer: str
    seller: str
    terms: str
    amount: bigint
    deadline: bigint
    evidence: str
    seller_claim: str
    buyer_claim: str
    verdict: str
    completion_percent: bigint
    confidence: bigint
    evidence_summary: str
    reasoning: str
    status: str
    settled: bool


class AgentCourt(gl.Contract):

    # ---------------------------------------------------------
    # Persistent storage
    # ---------------------------------------------------------

    next_agreement_id: bigint
    agreements: TreeMap[str, Agreement]

    # ---------------------------------------------------------
    # Agreement status
    # ---------------------------------------------------------

    STATUS_CREATED = "CREATED"
    STATUS_FUNDED = "FUNDED"
    STATUS_DELIVERED = "DELIVERED"
    STATUS_DISPUTED = "DISPUTED"
    STATUS_ADJUDICATING = "ADJUDICATING"
    STATUS_RESOLVED = "RESOLVED"
    STATUS_SETTLED = "SETTLED"

    # ---------------------------------------------------------
    # Verdicts
    # ---------------------------------------------------------

    VERDICT_PENDING = "PENDING"
    VERDICT_FULFILLED = "FULFILLED"
    VERDICT_PARTIAL = "PARTIALLY_FULFILLED"
    VERDICT_NOT_FULFILLED = "NOT_FULFILLED"
    VERDICT_UNDETERMINED = "UNDETERMINED"

    def __init__(self):
        self.next_agreement_id = 1

    # =========================================================
    # CREATE AGREEMENT
    # =========================================================

    @gl.public.write
    def create_agreement(
        self,
        seller: str,
        terms: str,
        amount: int,
        deadline: int,
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
        self.next_agreement_id += 1

        self.agreements[str(agreement_id)] = Agreement(
            buyer=str(gl.message.sender_address).lower(),
            seller=seller,
            terms=terms,
            amount=amount,
            deadline=deadline,
            evidence="",
            seller_claim="",
            buyer_claim="",
            verdict=self.VERDICT_PENDING,
            completion_percent=0,
            confidence=0,
            evidence_summary="",
            reasoning="",
            status=self.STATUS_CREATED,
            settled=False,
        )

        return agreement_id

    # =========================================================
    # FUND AGREEMENT
    # =========================================================

    @gl.public.write
    def fund_agreement(self, agreement_id: int) -> None:

        agreement = self._get_agreement(agreement_id)

        if agreement.status != self.STATUS_CREATED:
            raise gl.vm.UserError("INVALID_STATUS")

        sender = str(gl.message.sender_address).lower()

        if sender != agreement.buyer.lower():
            raise gl.vm.UserError("ONLY_BUYER")

        agreement.status = self.STATUS_FUNDED
        self.agreements[str(agreement_id)] = agreement

    # =========================================================
    # SUBMIT DELIVERY
    # =========================================================

    @gl.public.write
    def submit_delivery(
        self,
        agreement_id: int,
        evidence: str,
        seller_claim: str,
    ) -> None:

        agreement = self._get_agreement(agreement_id)

        if agreement.status != self.STATUS_FUNDED:
            raise gl.vm.UserError("INVALID_STATUS")

        sender = str(gl.message.sender_address).lower()

        if sender != agreement.seller.lower():
            raise gl.vm.UserError("ONLY_SELLER")

        if not evidence:
            raise gl.vm.UserError("MISSING_EVIDENCE")

        agreement.evidence = evidence
        agreement.seller_claim = seller_claim
        agreement.status = self.STATUS_DELIVERED

        self.agreements[str(agreement_id)] = agreement

    # =========================================================
    # OPEN DISPUTE
    # =========================================================

    @gl.public.write
    def open_dispute(
        self,
        agreement_id: int,
        buyer_claim: str,
    ) -> None:

        agreement = self._get_agreement(agreement_id)

        if agreement.status != self.STATUS_DELIVERED:
            raise gl.vm.UserError("INVALID_STATUS")

        sender = str(gl.message.sender_address).lower()

        if sender != agreement.buyer.lower():
            raise gl.vm.UserError("ONLY_BUYER")

        if not buyer_claim:
            raise gl.vm.UserError("MISSING_BUYER_CLAIM")

        agreement.buyer_claim = buyer_claim
        agreement.status = self.STATUS_DISPUTED

        self.agreements[str(agreement_id)] = agreement

    # =========================================================
    # GENLAYER ADJUDICATION
    # =========================================================

    @gl.public.write
    def adjudicate(self, agreement_id: int) -> typing.Any:

        agreement = self._get_agreement(agreement_id)

        if agreement.status != self.STATUS_DISPUTED:
            raise gl.vm.UserError("INVALID_STATUS")

        agreement.status = self.STATUS_ADJUDICATING
        self.agreements[str(agreement_id)] = agreement

        # Extract storage values into normal memory before entering
        # the nondeterministic execution.
        terms = agreement.terms
        seller_claim = agreement.seller_claim
        buyer_claim = agreement.buyer_claim
        evidence = agreement.evidence

        def leader_fn():

            prompt = f"""
You are the decentralized adjudicator for an agent-to-agent
commerce agreement.

Determine whether the seller fulfilled the contractual obligations.

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
    "verdict": "FULFILLED | PARTIALLY_FULFILLED | NOT_FULFILLED | UNDETERMINED",
    "completion_percent": 0,
    "confidence": 0,
    "evidence_summary": "...",
    "reasoning": "..."
}}

Rules:

- FULFILLED means the evidence supports complete fulfillment.
- PARTIALLY_FULFILLED means the evidence supports incomplete but
  meaningful fulfillment.
- NOT_FULFILLED means the evidence supports failure to fulfill.
- UNDETERMINED means the evidence is insufficient or contradictory.
- completion_percent must be between 0 and 100.
- confidence must be between 0 and 100.
- Never invent evidence.
"""

            return gl.nondet.exec_prompt(
                prompt,
                response_format="json",
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
                str,
            ):
                return False

            if not isinstance(
                data.get("reasoning", ""),
                str,
            ):
                return False

            return True

        result = gl.vm.run_nondet(
            leader_fn,
            validator_fn,
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

        agreement.verdict = verdict
        agreement.completion_percent = completion
        agreement.confidence = confidence
        agreement.evidence_summary = str(
            result.get("evidence_summary", "")
        )
        agreement.reasoning = str(
            result.get("reasoning", "")
        )
        agreement.status = self.STATUS_RESOLVED

        self.agreements[str(agreement_id)] = agreement

        return result

    # =========================================================
    # SETTLEMENT
    # =========================================================

    @gl.public.write
    def settle(self, agreement_id: int) -> typing.Any:

        agreement = self._get_agreement(agreement_id)

        if agreement.settled:
            raise gl.vm.UserError("ALREADY_SETTLED")

        if agreement.status != self.STATUS_RESOLVED:
            raise gl.vm.UserError("NOT_RESOLVED")

        completion = int(agreement.completion_percent)
        amount = int(agreement.amount)

        seller_amount = amount * completion // 100
        buyer_refund = amount - seller_amount

        agreement.settled = True
        agreement.status = self.STATUS_SETTLED

        self.agreements[str(agreement_id)] = agreement

        return {
            "seller_amount": seller_amount,
            "buyer_refund": buyer_refund,
            "verdict": agreement.verdict,
        }

    # =========================================================
    # VIEW
    # =========================================================

    @gl.public.view
    def get_agreement(self, agreement_id: int) -> dict:
        agreement = self._get_agreement(agreement_id)

        return {
            "buyer": agreement.buyer,
            "seller": agreement.seller,
            "terms": agreement.terms,
            "amount": int(agreement.amount),
            "deadline": int(agreement.deadline),
            "evidence": agreement.evidence,
            "seller_claim": agreement.seller_claim,
            "buyer_claim": agreement.buyer_claim,
            "verdict": agreement.verdict,
            "completion_percent": int(agreement.completion_percent),
            "confidence": int(agreement.confidence),
            "evidence_summary": agreement.evidence_summary,
            "reasoning": agreement.reasoning,
            "status": agreement.status,
            "settled": agreement.settled,
        }

    # =========================================================
    # INTERNAL HELPERS
    # =========================================================

    def _get_agreement(self, agreement_id: int) -> Agreement:

        key = str(agreement_id)

        if key not in self.agreements:
            raise gl.vm.UserError("AGREEMENT_NOT_FOUND")

        return self.agreements[key]
