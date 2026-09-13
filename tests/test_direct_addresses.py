def test_direct_address_representation(
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

    agreement = court.get_agreement(agreement_id)

    print("\n=== ADDRESS DEBUG ===")
    print("direct_alice:", direct_alice)
    print("buyer passed :", buyer)
    print("stored buyer :", agreement["buyer"])
    print()
    print("direct_bob   :", direct_bob)
    print("seller passed:", seller)
    print("stored seller:", agreement["seller"])

    direct_vm.sender = direct_bob

    print()
    print("sender switched to direct_bob")
    print("direct_vm.sender:", direct_vm.sender)

    # Call a temporary view-style check through the contract if possible.
    assert agreement["seller"].lower() == seller.lower()
