import pytest

from helpers import (
    ADJUDICATOR_PROMPT,
    DAY,
    DEADLINE,
    START_TS,
    address,
    delivered_agreement,
    deploy,
    disputed_agreement,
    iso,
    ruling,
)


@pytest.fixture
def court(direct_vm, direct_deploy):
    return deploy(direct_vm, direct_deploy)


# ---------------------------------------------------------
# Agreement creation
# ---------------------------------------------------------


def test_seller_address_is_normalized(direct_vm, court, direct_alice, direct_bob):
    direct_vm.sender = direct_alice
    agreement_id = court.create_agreement(
        "  " + address(direct_bob).upper().replace("0X", "0x") + " ",
        "Terms",
        1000,
        DEADLINE,
    )

    assert court.get_agreement(agreement_id)["seller"] == address(direct_bob).lower()


@pytest.mark.parametrize(
    "seller",
    ["not-an-address", "0x1234", "0x" + "g" * 40],
)
def test_malformed_seller_rejected(direct_vm, court, direct_alice, seller):
    direct_vm.sender = direct_alice

    with pytest.raises(Exception, match="INVALID_SELLER"):
        court.create_agreement(seller, "Terms", 1000, DEADLINE)


def test_buyer_cannot_be_seller(direct_vm, court, direct_alice):
    direct_vm.sender = direct_alice

    with pytest.raises(Exception, match="SELLER_IS_BUYER"):
        court.create_agreement(address(direct_alice), "Terms", 1000, DEADLINE)


def test_deadline_must_be_in_future(direct_vm, court, direct_alice, direct_bob):
    direct_vm.sender = direct_alice

    with pytest.raises(Exception, match="DEADLINE_IN_PAST"):
        court.create_agreement(address(direct_bob), "Terms", 1000, START_TS)


def test_oversized_inputs_rejected(direct_vm, court, direct_alice, direct_bob):
    direct_vm.sender = direct_alice

    with pytest.raises(Exception, match="TERMS_TOO_LONG"):
        court.create_agreement(address(direct_bob), "t" * 4001, 1000, DEADLINE)

    agreement_id = court.create_agreement(address(direct_bob), "Terms", 1000, DEADLINE)
    court.fund_agreement(agreement_id)

    direct_vm.sender = direct_bob

    with pytest.raises(Exception, match="EVIDENCE_TOO_LONG"):
        court.submit_delivery(agreement_id, "e" * 4001, "Claim")

    with pytest.raises(Exception, match="CLAIM_TOO_LONG"):
        court.submit_delivery(agreement_id, "Evidence", "c" * 2001)


def test_agreement_count(direct_vm, court, direct_alice, direct_bob):
    assert court.get_agreement_count() == 0

    direct_vm.sender = direct_alice
    court.create_agreement(address(direct_bob), "Terms", 1000, DEADLINE)
    court.create_agreement(address(direct_bob), "Terms", 2000, DEADLINE)

    assert court.get_agreement_count() == 2


# ---------------------------------------------------------
# Happy path without a dispute
# ---------------------------------------------------------


def test_buyer_accepts_delivery(direct_vm, court, direct_alice, direct_bob):
    agreement_id = delivered_agreement(direct_vm, court, direct_alice, direct_bob)

    direct_vm.sender = direct_alice
    court.accept_delivery(agreement_id)

    agreement = court.get_agreement(agreement_id)
    assert agreement["status"] == "RESOLVED"
    assert agreement["verdict"] == "FULFILLED"
    assert agreement["completion_percent"] == 100
    assert agreement["resolution"] == "ACCEPTED_BY_BUYER"

    settlement = court.settle(agreement_id)
    assert settlement["seller_amount"] == 1000
    assert settlement["buyer_refund"] == 0


def test_only_buyer_accepts_delivery(direct_vm, court, direct_alice, direct_bob):
    agreement_id = delivered_agreement(direct_vm, court, direct_alice, direct_bob)

    with pytest.raises(Exception, match="ONLY_BUYER"):
        court.accept_delivery(agreement_id)


def test_accepted_delivery_cannot_be_disputed(direct_vm, court, direct_alice, direct_bob):
    agreement_id = delivered_agreement(direct_vm, court, direct_alice, direct_bob)

    direct_vm.sender = direct_alice
    court.accept_delivery(agreement_id)

    with pytest.raises(Exception, match="INVALID_STATUS"):
        court.open_dispute(agreement_id, "Changed my mind.")


# ---------------------------------------------------------
# Dispute window
# ---------------------------------------------------------


def test_seller_finalizes_after_silent_dispute_window(direct_vm, court, direct_alice, direct_bob):
    agreement_id = delivered_agreement(direct_vm, court, direct_alice, direct_bob)

    with pytest.raises(Exception, match="DISPUTE_WINDOW_OPEN"):
        court.finalize_undisputed(agreement_id)

    direct_vm.warp(iso(START_TS + 3 * DAY + 1))
    court.finalize_undisputed(agreement_id)

    agreement = court.get_agreement(agreement_id)
    assert agreement["verdict"] == "FULFILLED"
    assert agreement["resolution"] == "DISPUTE_WINDOW_EXPIRED"
    assert court.settle(agreement_id)["seller_amount"] == 1000


def test_dispute_allowed_until_window_closes(direct_vm, court, direct_alice, direct_bob):
    agreement_id = delivered_agreement(direct_vm, court, direct_alice, direct_bob)

    direct_vm.warp(iso(START_TS + 3 * DAY))
    direct_vm.sender = direct_alice
    court.open_dispute(agreement_id, "Two required sections are missing.")

    assert court.get_agreement(agreement_id)["status"] == "DISPUTED"


def test_dispute_rejected_after_window(direct_vm, court, direct_alice, direct_bob):
    agreement_id = delivered_agreement(direct_vm, court, direct_alice, direct_bob)

    direct_vm.warp(iso(START_TS + 3 * DAY + 1))
    direct_vm.sender = direct_alice

    with pytest.raises(Exception, match="DISPUTE_WINDOW_CLOSED"):
        court.open_dispute(agreement_id, "Too late.")


def test_disputed_agreement_cannot_be_auto_finalized(direct_vm, court, direct_alice, direct_bob):
    agreement_id = disputed_agreement(direct_vm, court, direct_alice, direct_bob)

    direct_vm.warp(iso(START_TS + 30 * DAY))

    with pytest.raises(Exception, match="INVALID_STATUS"):
        court.finalize_undisputed(agreement_id)


# ---------------------------------------------------------
# Delivery deadline
# ---------------------------------------------------------


def test_delivery_rejected_after_deadline(direct_vm, court, direct_alice, direct_bob):
    direct_vm.sender = direct_alice
    agreement_id = court.create_agreement(address(direct_bob), "Terms", 1000, DEADLINE)
    court.fund_agreement(agreement_id)

    direct_vm.warp(iso(DEADLINE + 1))
    direct_vm.sender = direct_bob

    with pytest.raises(Exception, match="DEADLINE_PASSED"):
        court.submit_delivery(agreement_id, "Late evidence", "Late claim")


def test_buyer_reclaims_after_missed_deadline(direct_vm, court, direct_alice, direct_bob):
    direct_vm.sender = direct_alice
    agreement_id = court.create_agreement(address(direct_bob), "Terms", 1000, DEADLINE)
    court.fund_agreement(agreement_id)

    with pytest.raises(Exception, match="DEADLINE_NOT_PASSED"):
        court.reclaim_expired(agreement_id)

    direct_vm.warp(iso(DEADLINE + 1))

    direct_vm.sender = direct_bob
    with pytest.raises(Exception, match="ONLY_BUYER"):
        court.reclaim_expired(agreement_id)

    direct_vm.sender = direct_alice
    court.reclaim_expired(agreement_id)

    agreement = court.get_agreement(agreement_id)
    assert agreement["verdict"] == "NOT_FULFILLED"
    assert agreement["resolution"] == "DELIVERY_DEADLINE_MISSED"

    settlement = court.settle(agreement_id)
    assert settlement["seller_amount"] == 0
    assert settlement["buyer_refund"] == 1000


def test_delivered_agreement_cannot_be_reclaimed(direct_vm, court, direct_alice, direct_bob):
    agreement_id = delivered_agreement(direct_vm, court, direct_alice, direct_bob)

    direct_vm.warp(iso(DEADLINE + 1))
    direct_vm.sender = direct_alice

    with pytest.raises(Exception, match="INVALID_STATUS"):
        court.reclaim_expired(agreement_id)


# ---------------------------------------------------------
# Adjudication access
# ---------------------------------------------------------


def test_only_parties_can_adjudicate(direct_vm, court, direct_alice, direct_bob, direct_charlie):
    agreement_id = disputed_agreement(direct_vm, court, direct_alice, direct_bob)
    direct_vm.mock_llm(ADJUDICATOR_PROMPT, ruling("PARTIALLY_FULFILLED", 70))

    direct_vm.sender = direct_charlie
    with pytest.raises(Exception, match="ONLY_PARTIES"):
        court.adjudicate(agreement_id)

    direct_vm.sender = direct_bob
    assert court.adjudicate(agreement_id)["verdict"] == "PARTIALLY_FULFILLED"


def test_adjudication_cannot_be_repeated(direct_vm, court, direct_alice, direct_bob):
    agreement_id = disputed_agreement(direct_vm, court, direct_alice, direct_bob)
    direct_vm.mock_llm(ADJUDICATOR_PROMPT, ruling("PARTIALLY_FULFILLED", 70))

    court.adjudicate(agreement_id)

    with pytest.raises(Exception, match="INVALID_STATUS"):
        court.adjudicate(agreement_id)
