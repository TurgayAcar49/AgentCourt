def test_direct_basic_storage(direct_vm, direct_deploy, direct_alice):
    court = direct_deploy("contracts/AgentCourt.py")

    direct_vm.sender = direct_alice

    # Constructor-created scalar state
    assert court.next_agreement_id == 1

    # V2 uses separate typed TreeMaps instead of one nested agreements map.
    assert court.agreement_buyer is not None
    assert court.agreement_seller is not None
    assert court.agreement_terms is not None
    assert court.agreement_amount is not None
    assert court.agreement_deadline is not None
    assert court.agreement_evidence is not None
    assert court.agreement_seller_claim is not None
    assert court.agreement_buyer_claim is not None
    assert court.agreement_verdict is not None
    assert court.agreement_completion is not None
    assert court.agreement_confidence is not None
    assert court.agreement_evidence_summary is not None
    assert court.agreement_reasoning is not None
    assert court.agreement_status is not None
    assert court.agreement_settled is not None
