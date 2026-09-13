import pytest


def test_direct_lifecycle_create_fund_deliver_dispute(
    direct_vm,
    direct_deploy,
    direct_alice,
    direct_bob,
):
    court = direct_deploy("contracts/AgentCourt.py")

    buyer = "0x" + direct_alice.hex()
    seller = "0x" + direct_bob.hex()

    # =========================================================
    # CREATE
    # =========================================================

    direct_vm.sender = direct_alice

    agreement_id = court.create_agreement(
        seller,
        "Seller must deliver the agreed digital service.",
        1000,
        9999999999,
    )

    assert agreement_id == 1

    agreement = court.get_agreement(agreement_id)

    assert agreement["status"] == court.STATUS_CREATED
    assert agreement["buyer"].lower() == buyer.lower()
    assert agreement["seller"].lower() == seller.lower()
    assert agreement["amount"] == 1000

    # =========================================================
    # FUND
    # =========================================================

    direct_vm.sender = direct_alice

    court.fund_agreement(agreement_id)

    agreement = court.get_agreement(agreement_id)

    assert agreement["status"] == court.STATUS_FUNDED

    # =========================================================
    # DELIVERY
    # =========================================================

    direct_vm.sender = direct_bob

    court.submit_delivery(
        agreement_id,
        "https://example.com/delivered-work",
        "The agreed digital service has been delivered.",
    )

    agreement = court.get_agreement(agreement_id)

    assert agreement["status"] == court.STATUS_DELIVERED
    assert agreement["evidence"] == "https://example.com/delivered-work"
    assert agreement["seller_claim"] == (
        "The agreed digital service has been delivered."
    )

    # =========================================================
    # DISPUTE
    # =========================================================

    direct_vm.sender = direct_alice

    court.open_dispute(
        agreement_id,
        "The delivered work does not satisfy the agreed requirements.",
    )

    agreement = court.get_agreement(agreement_id)

    assert agreement["status"] == court.STATUS_DISPUTED
    assert agreement["buyer_claim"] == (
        "The delivered work does not satisfy the agreed requirements."
    )
