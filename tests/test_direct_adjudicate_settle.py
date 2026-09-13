def test_direct_adjudicate_and_settle(
    direct_vm,
    direct_deploy,
    direct_alice,
    direct_bob,
):
    court = direct_deploy("contracts/AgentCourt.py")

    # Mock the GenLayer LLM response used by adjudicate().
    direct_vm.mock_llm(
        r".*decentralized adjudicator.*",
        {
            "verdict": "PARTIALLY_FULFILLED",
            "completion_percent": 70,
            "confidence": 90,
            "evidence_summary": "The submitted evidence supports substantial but incomplete fulfillment.",
            "reasoning": "The evidence indicates that the service was delivered, but the buyer's dispute identifies an unresolved part of the agreement."
        },
    )

    buyer = "0x" + direct_alice.hex()
    seller = "0x" + direct_bob.hex()

    # CREATE
    direct_vm.sender = direct_alice

    agreement_id = court.create_agreement(
        seller,
        "Seller must deliver the agreed digital service.",
        1000,
        9999999999,
    )

    # FUND
    court.fund_agreement(agreement_id)

    # DELIVER
    direct_vm.sender = direct_bob

    court.submit_delivery(
        agreement_id,
        "Delivery evidence: completed service output.",
        "The service was completed according to the agreement.",
    )

    # DISPUTE
    direct_vm.sender = direct_alice

    court.open_dispute(
        agreement_id,
        "The delivered result does not fully satisfy the agreement.",
    )

    # ADJUDICATE
    result = court.adjudicate(agreement_id)

    assert isinstance(result, dict)

    agreement = court.get_agreement(agreement_id)

    assert agreement["status"] == court.STATUS_RESOLVED
    assert agreement["verdict"] in [
        court.VERDICT_FULFILLED,
        court.VERDICT_PARTIAL,
        court.VERDICT_NOT_FULFILLED,
        court.VERDICT_UNDETERMINED,
    ]

    assert 0 <= agreement["completion_percent"] <= 100
    assert 0 <= agreement["confidence"] <= 100

    # SETTLE
    settlement = court.settle(agreement_id)

    expected_seller = (
        agreement["amount"]
        * agreement["completion_percent"]
        // 100
    )

    expected_refund = agreement["amount"] - expected_seller

    assert settlement["seller_amount"] == expected_seller
    assert settlement["buyer_refund"] == expected_refund
    assert settlement["verdict"] == agreement["verdict"]

    final_agreement = court.get_agreement(agreement_id)

    assert final_agreement["status"] == court.STATUS_SETTLED
    assert final_agreement["settled"] is True
