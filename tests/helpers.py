import datetime

START = "2026-01-01T00:00:00Z"
START_TS = int(
    datetime.datetime.fromisoformat(START.replace("Z", "+00:00")).timestamp()
)
DAY = 24 * 60 * 60
DEADLINE = START_TS + 7 * DAY

ADJUDICATOR_PROMPT = r"decentralized adjudicator"


def iso(ts: int) -> str:
    return (
        datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def address(account) -> str:
    if hasattr(account, "as_hex"):
        return account.as_hex
    return "0x" + account.hex()


def ruling(verdict, completion, confidence=90, summary="summary", reasoning="reasoning"):
    return {
        "verdict": verdict,
        "completion_percent": completion,
        "confidence": confidence,
        "evidence_summary": summary,
        "reasoning": reasoning,
    }


def deploy(direct_vm, direct_deploy):
    direct_vm.warp(START)
    return direct_deploy("contracts/AgentCourt.py")


def delivered_agreement(
    direct_vm,
    court,
    buyer,
    seller,
    evidence="Delivery evidence: completed service output.",
    terms="Seller must deliver the agreed digital service.",
    amount=1000,
):
    direct_vm.sender = buyer
    agreement_id = court.create_agreement(address(seller), terms, amount, DEADLINE)
    court.fund_agreement(agreement_id)

    direct_vm.sender = seller
    court.submit_delivery(
        agreement_id,
        evidence,
        "The service was completed according to the agreement.",
    )

    return agreement_id


def disputed_agreement(direct_vm, court, buyer, seller, **kwargs):
    agreement_id = delivered_agreement(direct_vm, court, buyer, seller, **kwargs)

    direct_vm.sender = buyer
    court.open_dispute(
        agreement_id,
        "The delivered result does not fully satisfy the agreement.",
    )

    return agreement_id
