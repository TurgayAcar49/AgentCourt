def test_agentcourt_direct_deploy(
    direct_vm,
    direct_deploy,
    direct_alice,
    direct_bob,
):
    court = direct_deploy("contracts/AgentCourt.py")

    direct_vm.sender = direct_alice

    buyer_address = "0x" + direct_alice.hex()
    seller_address = "0x" + direct_bob.hex()

    agreement_id = court.create_agreement(
        seller_address,
        "Seller must deliver the agreed digital service.",
        1000,
        9999999999,
    )

    assert agreement_id == 1

    agreement = court.get_agreement(agreement_id)

    assert agreement["buyer"].lower() == buyer_address.lower()
    assert agreement["seller"].lower() == seller_address.lower()
    assert agreement["amount"] == 1000
    assert agreement["status"] == court.STATUS_CREATED
    assert agreement["verdict"] == court.VERDICT_PENDING
