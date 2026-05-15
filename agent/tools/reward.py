"""Reward Agent tool — the climax of Rasain: where Web3 meets payment.

Two flows:

  EARN   — a verified report grants Rasain Points (RSN). Once a citizen's
           off-chain balance crosses MINT_THRESHOLD_RSN, the points are minted
           as a real SPL token on Solana (proof of impact).

  REDEEM — "Civic Credit": a citizen spends RSN to offset a government
           retribusi bill. RSN is burned on-chain; the remaining balance
           becomes a DOKU QRIS the citizen pays. Civic engagement literally
           pays down civic obligations.
"""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from agent.config import get_settings
from agent.models import Citizen, Report, Reward, RewardStatus
from agent.store import get_store
from agent.tools.doku import compute_civic_credit, create_retribusi_qris
from agent.tools.solana_token import (
    get_rsn_balance,
    mint_rsn,
    new_citizen_wallet,
)


def _ensure_wallet(citizen: Citizen) -> Citizen:
    """Lazily provision a custodial Solana wallet for a citizen."""
    if not citizen.solana_wallet:
        wallet = new_citizen_wallet()
        citizen.solana_wallet = wallet["address"]
        # Custodial secret stored alongside (hackathon V1; encrypt in prod).
        citizen.solana_wallet_secret = wallet["secret"]
        get_store().upsert_citizen(citizen)
    return citizen


async def earn_reward_for_report(report: Report) -> Reward:
    """Grant RSN for a verified report. Mints on-chain once threshold is crossed.

    Returns the Reward record (status EARNED or MINTED).
    """
    settings = get_settings()
    store = get_store()
    citizen = store.get_citizen(report.citizen_id)
    if citizen is None:
        raise ValueError(f"Citizen {report.citizen_id} not found")

    points = settings.earn_rsn_per_verified_report
    reward = Reward(
        citizen_id=citizen.id,
        report_id=report.id,
        points_earned=points,
        status=RewardStatus.EARNED,
    )

    # Accumulate off-chain first (cheap, no tx).
    citizen.rsn_offchain += points

    # Threshold crossed → mint the accumulated batch on-chain.
    if citizen.rsn_offchain >= settings.mint_threshold_rsn:
        citizen = _ensure_wallet(citizen)
        to_mint = citizen.rsn_offchain
        mint_result = await mint_rsn(citizen.solana_wallet, to_mint)
        citizen.rsn_offchain = 0
        citizen.rsn_onchain = await get_rsn_balance(citizen.solana_wallet)
        reward.status = RewardStatus.MINTED
        reward.minted_at = datetime.utcnow()
        reward.spl_mint_tx = mint_result["signature"]
        reward.spl_solscan_url = mint_result["solscan_url"]

    store.upsert_citizen(citizen)
    store.upsert_reward(reward)
    return reward


async def redeem_civic_credit(
    citizen_id: str,
    retribusi_type: str,
    retribusi_amount_idr: int,
) -> dict:
    """Redeem RSN as Civic Credit against a government retribusi bill.

    Flow: compute offset → burn RSN on Solana → generate DOKU QRIS for the rest.

    Returns a dict with the credit breakdown, burn proof, and QRIS payment.
    """
    from agent.tools.solana_token import burn_rsn  # local import: avoid cycle

    settings = get_settings()
    store = get_store()
    citizen = store.get_citizen(citizen_id)
    if citizen is None:
        raise ValueError(f"Citizen {citizen_id} not found")
    if not citizen.solana_wallet:
        raise ValueError("Citizen belum punya RSN — belum ada laporan verified.")

    rsn_balance = await get_rsn_balance(citizen.solana_wallet)
    credit = compute_civic_credit(
        retribusi_amount_idr, rsn_balance, settings.redemption_rate_idr_per_rsn
    )

    invoice_number = f"RTB-{retribusi_type[:3].upper()}-{uuid4().hex[:8]}"
    result: dict = {
        "invoice_number": invoice_number,
        "retribusi_type": retribusi_type,
        "retribusi_amount_idr": retribusi_amount_idr,
        "rsn_balance_before": rsn_balance,
        **credit,  # rsn_used, idr_offset, cash_due_idr
    }

    # Burn the RSN that was used as credit (on-chain proof).
    if credit["rsn_used"] > 0:
        burn_result = await burn_rsn(
            citizen.solana_wallet,
            citizen.solana_wallet_secret,
            credit["rsn_used"],
        )
        result["burn_tx"] = burn_result["signature"]
        result["burn_solscan_url"] = burn_result["solscan_url"]
        citizen.rsn_onchain = await get_rsn_balance(citizen.solana_wallet)
        store.upsert_citizen(citizen)

    # Generate DOKU QRIS for the remaining cash due.
    qris = await create_retribusi_qris(
        invoice_number=invoice_number,
        amount_idr=credit["cash_due_idr"],
        citizen_name=citizen.name,
        description=f"Retribusi {retribusi_type}",
    )
    result["doku_qris"] = qris

    # Record the redemption as a Reward entry.
    redemption = Reward(
        citizen_id=citizen.id,
        report_id=citizen.id,  # redemption not tied to single report
        points_earned=0,
        status=RewardStatus.REDEEMED,
        redeemed_at=datetime.utcnow(),
        burn_tx=result.get("burn_tx"),
        idr_amount=credit["idr_offset"],
    )
    store.upsert_reward(redemption)
    return result
