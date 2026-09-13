import pytest


def addresses(direct_alice, direct_bob, direct_charlie):
    return (
        "0x" + direct_alice.hex(),
        "0x" + direct_bob.hex(),
        "0x" + direct_charlie.hex(),
    )


def create_court(direct_deploy):
    return direct_deploy("contracts/AgentCourt.py")


def test_create_rejects_invalid_inputs(
    direct_vm,
    direct_deploy,
    direct_alice,
    direct_bob,
):
    court = create_court(direct_deploy)

    direct_vm.sender = direct_alice

    seller = "0x" + direct_bob.hex()

    with pytest.raises(Exception, match="INVALID_SELLER"):
        court.create_agreement(
            "",
            "Valid terms",
            1000,
            9999999999,
        )

    with pytest.raises(Exception, match="INVALID_TERMS"):
        court.create_agreement(
            seller,
            "",
            1000,
            9999999999,
        )

    with pytest.raises(Exception, match="INVALID_AMOUNT"):
        court.create_agreement(
            seller,
            "Valid terms",
            0,
            9999999999,
        )

    with pytest.raises(Exception, match="INVALID_DEADLINE"):
        court.create_agreement(
            seller,
            "Valid terms",
            1000,
            0,
        )


def test_fund_only_buyer(
    direct_vm,
    direct_deploy,
    direct_alice,
    direct_bob,
    direct_charlie,
):
    court = create_court(direct_deploy)

    buyer, seller, charlie = addresses(
        direct_alice,
        direct_bob,
        direct_charlie,
    )

    direct_vm.sender = direct_alice

    agreement_id = court.create_agreement(
        seller,
        "Seller must deliver the agreed digital service.",
        1000,
        9999999999,
    )

    direct_vm.sender = direct_charlie

    with pytest.raises(Exception, match="ONLY_BUYER"):
        court.fund_agreement(agreement_id)


def test_delivery_only_seller(
    direct_vm,
    direct_deploy,
    direct_alice,
    direct_bob,
    direct_charlie,
):
    court = create_court(direct_deploy)

    buyer, seller, charlie = addresses(
        direct_alice,
        direct_bob,
        direct_charlie,
    )

    direct_vm.sender = direct_alice

    agreement_id = court.create_agreement(
        seller,
        "Seller must deliver the agreed digital service.",
        1000,
        9999999999,
    )

    court.fund_agreement(agreement_id)

    direct_vm.sender = direct_charlie

    with pytest.raises(Exception, match="ONLY_SELLER"):
        court.submit_delivery(
            agreement_id,
            "Evidence",
            "Seller claim",
        )


def test_delivery_requires_evidence(
    direct_vm,
    direct_deploy,
    direct_alice,
    direct_bob,
):
    court = create_court(direct_deploy)

    buyer, seller, _ = addresses(
        direct_alice,
        direct_bob,
        direct_bob,
    )

    direct_vm.sender = direct_alice

    agreement_id = court.create_agreement(
        seller,
        "Seller must deliver the agreed digital service.",
        1000,
        9999999999,
    )

    court.fund_agreement(agreement_id)

    direct_vm.sender = direct_bob

    with pytest.raises(Exception, match="MISSING_EVIDENCE"):
        court.submit_delivery(
            agreement_id,
            "",
            "Seller claim",
        )


def test_dispute_only_buyer(
    direct_vm,
    direct_deploy,
    direct_alice,
    direct_bob,
    direct_charlie,
):
    court = create_court(direct_deploy)

    buyer, seller, charlie = addresses(
        direct_alice,
        direct_bob,
        direct_charlie,
    )

    direct_vm.sender = direct_alice

    agreement_id = court.create_agreement(
        seller,
        "Seller must deliver the agreed digital service.",
        1000,
        9999999999,
    )

    court.fund_agreement(agreement_id)

    direct_vm.sender = direct_bob

    court.submit_delivery(
        agreement_id,
        "Delivery evidence",
        "Seller claim",
    )

    direct_vm.sender = direct_charlie

    with pytest.raises(Exception, match="ONLY_BUYER"):
        court.open_dispute(
            agreement_id,
            "Invalid dispute attempt",
        )


def test_dispute_requires_claim(
    direct_vm,
    direct_deploy,
    direct_alice,
    direct_bob,
):
    court = create_court(direct_deploy)

    buyer, seller, _ = addresses(
        direct_alice,
        direct_bob,
        direct_bob,
    )

    direct_vm.sender = direct_alice

    agreement_id = court.create_agreement(
        seller,
        "Seller must deliver the agreed digital service.",
        1000,
        9999999999,
    )

    court.fund_agreement(agreement_id)

    direct_vm.sender = direct_bob

    court.submit_delivery(
        agreement_id,
        "Delivery evidence",
        "Seller claim",
    )

    direct_vm.sender = direct_alice

    with pytest.raises(Exception, match="MISSING_BUYER_CLAIM"):
        court.open_dispute(
            agreement_id,
            "",
        )


def test_invalid_state_transitions(
    direct_vm,
    direct_deploy,
    direct_alice,
    direct_bob,
):
    court = create_court(direct_deploy)

    buyer, seller, _ = addresses(
        direct_alice,
        direct_bob,
        direct_bob,
    )

    direct_vm.sender = direct_alice

    agreement_id = court.create_agreement(
        seller,
        "Seller must deliver the agreed digital service.",
        1000,
        9999999999,
    )

    # Cannot deliver before funding.
    direct_vm.sender = direct_bob

    with pytest.raises(Exception, match="INVALID_STATUS"):
        court.submit_delivery(
            agreement_id,
            "Evidence",
            "Claim",
        )

    # Cannot dispute before delivery.
    direct_vm.sender = direct_alice

    with pytest.raises(Exception, match="INVALID_STATUS"):
        court.open_dispute(
            agreement_id,
            "Dispute",
        )

    # Cannot settle before resolution.
    with pytest.raises(Exception, match="NOT_RESOLVED"):
        court.settle(agreement_id)


def test_unknown_agreement_rejected(
    direct_deploy,
):
    court = create_court(direct_deploy)

    with pytest.raises(Exception, match="AGREEMENT_NOT_FOUND"):
        court.get_agreement(999)

    with pytest.raises(Exception, match="AGREEMENT_NOT_FOUND"):
        court.fund_agreement(999)

    with pytest.raises(Exception, match="AGREEMENT_NOT_FOUND"):
        court.settle(999)


def test_double_settlement_rejected(
    direct_vm,
    direct_deploy,
    direct_alice,
    direct_bob,
):
    court = create_court(direct_deploy)

    buyer, seller, _ = addresses(
        direct_alice,
        direct_bob,
        direct_bob,
    )

    direct_vm.sender = direct_alice

    agreement_id = court.create_agreement(
        seller,
        "Seller must deliver the agreed digital service.",
        1000,
        9999999999,
    )

    court.fund_agreement(agreement_id)

    direct_vm.sender = direct_bob

    court.submit_delivery(
        agreement_id,
        "Delivery evidence",
        "Seller claim",
    )

    direct_vm.sender = direct_alice

    court.open_dispute(
        agreement_id,
        "The delivery is incomplete.",
    )

    direct_vm.mock_llm(
        r".*decentralized adjudicator.*",
        {
            "verdict": "PARTIALLY_FULFILLED",
            "completion_percent": 70,
            "confidence": 90,
            "evidence_summary": "Partial fulfillment.",
            "reasoning": "The evidence supports substantial but incomplete fulfillment.",
        },
    )

    court.adjudicate(agreement_id)

    first_settlement = court.settle(agreement_id)

    assert first_settlement["seller_amount"] == 700
    assert first_settlement["buyer_refund"] == 300

    with pytest.raises(Exception, match="ALREADY_SETTLED"):
        court.settle(agreement_id)
