import urllib.request
from pathlib import Path

import pytest

from gltest.accounts import get_default_account
from gltest.contracts.contract_factory import get_contract_factory

LOCALNET_RPC = "http://127.0.0.1:4000/api"


def localnet_available() -> bool:
    try:
        urllib.request.urlopen(LOCALNET_RPC, timeout=2)
    except urllib.error.HTTPError:
        return True
    except Exception:
        return False
    return True


@pytest.mark.skipif(
    not localnet_available(),
    reason=f"GenLayer localnet is not running at {LOCALNET_RPC}",
)
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
