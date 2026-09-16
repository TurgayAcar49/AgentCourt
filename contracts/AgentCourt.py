# v0.3.0
# {
#   "Seq": [
#     { "Depends": "py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng" }
#   ]
# }

import genlayer as gl
from genlayer.types import *
from genlayer.storage import TreeMap
import typing


class AgentCourt(gl.contract.Contract):

    next_agreement_id: u256

    agreement_buyer: TreeMap[str, str]
    agreement_seller: TreeMap[str, str]
    agreement_terms: TreeMap[str, str]
    agreement_amount: TreeMap[str, u256]
    agreement_deadline: TreeMap[str, u256]
    agreement_evidence: TreeMap[str, str]
    agreement_seller_claim: TreeMap[str, str]
    agreement_buyer_claim: TreeMap[str, str]
    agreement_verdict: TreeMap[str, str]
    agreement_completion: TreeMap[str, u256]
    agreement_confidence: TreeMap[str, u256]
    agreement_evidence_summary: TreeMap[str, str]
    agreement_reasoning: TreeMap[str, str]
    agreement_status: TreeMap[str, str]
    agreement_settled: TreeMap[str, bool]

    STATUS_CREATED = "CREATED"
    STATUS_FUNDED = "FUNDED"
    STATUS_DELIVERED = "DELIVERED"
    STATUS_DISPUTED = "DISPUTED"
    STATUS_ADJUDICATING = "ADJUDICATING"
    STATUS_RESOLVED = "RESOLVED"
    STATUS_SETTLED = "SETTLED"

    VERDICT_PENDING = "PENDING"
    VERDICT_FULFILLED = "FULFILLED"
    VERDICT_PARTIAL = "PARTIALLY_FULFILLED"
    VERDICT_NOT_FULFILLED = "NOT_FULFILLED"
    VERDICT_UNDETERMINED = "UNDETERMINED"

    def __init__(self):
        self.next_agreement_id = 1

    def _key(self, agreement_id: int) -> str:
        return str(agreement_id)

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

        agreement_id = self.next_agreement_id
        key = self._key(agreement_id)

        self.agreement_buyer[key] = str(gl.message.sender_address)
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

        self.next_agreement_id = agreement_id + 1

        return agreement_id

    @gl.public.write
    def fund_agreement(self, agreement_id: int) -> None:

        key = self._key(agreement_id)

        if key not in self.agreement_status:
            raise gl.vm.UserError("AGREEMENT_NOT_FOUND")

        if self.agreement_status[key] != self.STATUS_CREATED:
            raise gl.vm.UserError("INVALID_STATUS")

        if str(gl.message.sender_address) != self.agreement_buyer[key]:
            raise gl.vm.UserError("ONLY_BUYER")

        self.agreement_status[key] = self.STATUS_FUNDED

    @gl.public.write
    def submit_delivery(
        self,
        agreement_id: int,
        evidence: str,
        seller_claim: str,
    ) -> None:

        key = self._key(agreement_id)

        if key not in self.agreement_status:
            raise gl.vm.UserError("AGREEMENT_NOT_FOUND")

        if self.agreement_status[key] != self.STATUS_FUNDED:
            raise gl.vm.UserError("INVALID_STATUS")

        if str(gl.message.sender_address) != self.agreement_seller[key]:
            raise gl.vm.UserError("ONLY_SELLER")

        if not evidence:
            raise gl.vm.UserError("INVALID_EVIDENCE")

        self.agreement_evidence[key] = evidence
        self.agreement_seller_claim[key] = seller_claim
        self.agreement_status[key] = self.STATUS_DELIVERED

    @gl.public.write
    def open_dispute(
        self,
        agreement_id: int,
        buyer_claim: str,
    ) -> None:

        key = self._key(agreement_id)

        if key not in self.agreement_status:
            raise gl.vm.UserError("AGREEMENT_NOT_FOUND")

        if self.agreement_status[key] != self.STATUS_DELIVERED:
            raise gl.vm.UserError("INVALID_STATUS")

        if str(gl.message.sender_address) != self.agreement_buyer[key]:
            raise gl.vm.UserError("ONLY_BUYER")

        if not buyer_claim:
            raise gl.vm.UserError("INVALID_BUYER_CLAIM")

        self.agreement_buyer_claim[key] = buyer_claim
        self.agreement_status[key] = self.STATUS_DISPUTED

    @gl.public.write
    def adjudicate(self, agreement_id: int) -> None:

        key = self._key(agreement_id)

        if key not in self.agreement_status:
            raise gl.vm.UserError("AGREEMENT_NOT_FOUND")

        if self.agreement_status[key] != self.STATUS_DISPUTED:
            raise gl.vm.UserError("INVALID_STATUS")

        terms = self.agreement_terms[key]
        evidence = self.agreement_evidence[key]
        seller_claim = self.agreement_seller_claim[key]
        buyer_claim = self.agreement_buyer_claim[key]

        prompt = f"""
You are an impartial adjudicator for an agent-to-agent commerce agreement.

Determine whether the seller fulfilled the agreement.

IMPORTANT RULES:
1. Use ONLY the agreement terms, delivery evidence, seller claim, and buyer claim.
2. Do NOT invent facts.
3. Do NOT assume missing evidence proves fulfillment.
4. If the evidence is insufficient or contradictory, use UNDETERMINED.
5. completion_percent must be between 0 and 100.
6. The smart contract will calculate settlement amounts deterministically.
7. Do not calculate or recommend monetary payouts.

AGREEMENT TERMS:
{terms}

DELIVERY EVIDENCE:
{evidence}

SELLER CLAIM:
{seller_claim}

BUYER CLAIM:
{buyer_claim}

Return JSON with exactly these fields:

{{
  "verdict": "FULFILLED | PARTIALLY_FULFILLED | NOT_FULFILLED | UNDETERMINED",
  "completion_percent": 0,
  "confidence": 0,
  "evidence_summary": "...",
  "reasoning": "..."
}}
"""

        def leader_fn():
            return gl.nondet.exec_prompt(
                prompt,
                response_format="json",
            )

        def validator_fn(result):

            if isinstance(result, gl.vm.Return):
                result = result.calldata

            if not isinstance(result, dict):
                return False

            verdict = result.get("verdict")
            completion = result.get("completion_percent")
            confidence = result.get("confidence")
            evidence_summary = result.get("evidence_summary")
            reasoning = result.get("reasoning")

            allowed_verdicts = {
                self.VERDICT_FULFILLED,
                self.VERDICT_PARTIAL,
                self.VERDICT_NOT_FULFILLED,
                self.VERDICT_UNDETERMINED,
            }

            if verdict not in allowed_verdicts:
                return False

            if not isinstance(completion, int):
                return False

            if completion < 0 or completion > 100:
                return False

            if not isinstance(confidence, int):
                return False

            if confidence < 0 or confidence > 100:
                return False

            if not isinstance(evidence_summary, str):
                return False

            if not isinstance(reasoning, str):
                return False

            return True

        self.agreement_status[key] = self.STATUS_ADJUDICATING

        result = gl.vm.run_nondet_default(
            leader_fn,
            validator_fn,
        )

        if isinstance(result, gl.vm.Return):
            result = result.calldata

        self.agreement_verdict[key] = result["verdict"]
        self.agreement_completion[key] = result["completion_percent"]
        self.agreement_confidence[key] = result["confidence"]
        self.agreement_evidence_summary[key] = result["evidence_summary"]
        self.agreement_reasoning[key] = result["reasoning"]

        self.agreement_status[key] = self.STATUS_RESOLVED

    @gl.public.write
    def settle(self, agreement_id: int) -> dict[str, typing.Any]:

        key = self._key(agreement_id)

        if key not in self.agreement_status:
            raise gl.vm.UserError("AGREEMENT_NOT_FOUND")

        if self.agreement_status[key] != self.STATUS_RESOLVED:
            raise gl.vm.UserError("NOT_RESOLVED")

        if self.agreement_settled[key]:
            raise gl.vm.UserError("ALREADY_SETTLED")

        amount = self.agreement_amount[key]
        completion = self.agreement_completion[key]

        seller_amount = amount * completion // 100
        buyer_refund = amount - seller_amount

        self.agreement_settled[key] = True
        self.agreement_status[key] = self.STATUS_SETTLED

        return {
            "agreement_id": agreement_id,
            "verdict": self.agreement_verdict[key],
            "completion_percent": completion,
            "seller_amount": seller_amount,
            "buyer_refund": buyer_refund,
        }

    @gl.public.view
    def get_agreement(self, agreement_id: int) -> dict[str, typing.Any]:

        key = self._key(agreement_id)

        if key not in self.agreement_status:
            raise gl.vm.UserError("AGREEMENT_NOT_FOUND")

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
