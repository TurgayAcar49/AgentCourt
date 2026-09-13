def test_direct_dict_storage(direct_vm, direct_deploy, direct_alice):
    court = direct_deploy("contracts/AgentCourt.py")

    direct_vm.sender = direct_alice

    # Test a normal Python dict as contract state.
    court.test_dict = {}

    court.test_dict[1] = {
        "amount": 1000,
        "status": "CREATED",
    }

    assert court.test_dict[1]["amount"] == 1000
    assert court.test_dict[1]["status"] == "CREATED"
