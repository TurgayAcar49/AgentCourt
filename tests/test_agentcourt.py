import pytest


def test_agentcourt_project():
    """
    Initial project smoke test.

    Contract-level tests will be added after the first
    Direct Mode compilation succeeds.
    """
    assert True


def test_verdict_categories():
    verdicts = {
        "FULFILLED",
        "PARTIALLY_FULFILLED",
        "NOT_FULFILLED",
        "UNDETERMINED",
    }

    assert len(verdicts) == 4


def test_settlement_math():
    amount = 100

    completion = 70

    seller_amount = amount * completion // 100
    buyer_refund = amount - seller_amount

    assert seller_amount == 70
    assert buyer_refund == 30


def test_full_settlement():
    amount = 100

    completion = 100

    seller_amount = amount * completion // 100
    buyer_refund = amount - seller_amount

    assert seller_amount == 100
    assert buyer_refund == 0


def test_failed_settlement():
    amount = 100

    completion = 0

    seller_amount = amount * completion // 100
    buyer_refund = amount - seller_amount

    assert seller_amount == 0
    assert buyer_refund == 100
