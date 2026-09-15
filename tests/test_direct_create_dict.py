def test_direct_create_agreement_with_storage(
    direct_vm,
    direct_deploy,
    direct_alice,
    direct_bob,
):
    court = direct_deploy("contracts/AgentCourt.py")

    buyer = "0x" + direct_alice.hex()
    seller = "0x" + direct_bob.hex()

    direct_vm.sender = direct_alice

    agreement_id = court.create_agreement(
        seller,
        "Seller must deliver the agreed digital service.",
        1000,
        9999999999,
    )

    assert agreement_id == 1

    agreement = court.get_agreement(agreement_id)

    assert agreement["buyer"].lower() == buyer.lower()
    assert agreement["seller"].lower() == seller.lower()
    assert agreement["amount"] == 1000
    assert agreement["status"] == court.STATUS_CREATED
