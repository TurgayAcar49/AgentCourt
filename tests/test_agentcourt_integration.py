from pathlib import Path

from gltest.accounts import get_default_account
from gltest.contracts.contract_factory import get_contract_factory


def test_agentcourt_localnet_deploy():
    account = get_default_account()

    factory = get_contract_factory(
        contract_file_path=Path("AgentCourt.py")
    )

    contract = factory.deploy(
        account=account,
    )

    assert contract.address is not None
    assert str(contract.address) != ""

    print(f"\nAgentCourt deployed at: {contract.address}")
