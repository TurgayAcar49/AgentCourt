from gltest.direct import create_address


def test_direct_basic_storage(direct_vm, direct_deploy, direct_alice):
    court = direct_deploy("contracts/AgentCourt.py")

    direct_vm.sender = direct_alice

    # Constructor-created scalar state
    assert court.next_agreement_id == 1

    # Read the TreeMap object itself without writing into it.
    assert court.agreements is not None
