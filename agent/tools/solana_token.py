"""Solana SPL token tool — the Web3 layer of LaporKita's reward system.

"LaporPoints" (LPT) is an SPL token on Solana devnet. Citizens earn LPT for
verified reports; LPT is burned when redeemed as Civic Credit against retribusi.

Decimals = 0 — LaporPoints are whole units (1 verified report ~ 10 LPT).

Wallet model (V1): custodial. The backend generates a keypair per citizen so
there is zero wallet-install friction. V2 migrates to self-custody (Phantom).

Every mint/burn is a real on-chain transaction — the signature is a verifiable
proof of impact (linkable on Solscan).
"""
from __future__ import annotations

import json
from pathlib import Path

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TxOpts
from solders.keypair import Keypair
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from spl.token.async_client import AsyncToken
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import BurnParams, burn, get_associated_token_address

from agent.config import get_settings

LPT_DECIMALS = 0  # LaporPoints are whole units


def load_mint_authority() -> Keypair:
    """Load the backend mint-authority keypair from the Solana CLI JSON file."""
    settings = get_settings()
    path = Path(settings.solana_mint_authority_keypair_path)
    raw = json.loads(path.read_text())
    return Keypair.from_bytes(bytes(raw))


def solscan_url(signature_or_address: str, kind: str = "tx") -> str:
    """Build a Solscan devnet URL for a transaction or address (demo proof link)."""
    return f"https://solscan.io/{kind}/{signature_or_address}?cluster=devnet"


async def create_laporpoints_mint() -> str:
    """Create the LaporPoints (LPT) SPL token mint. One-time setup.

    Returns the mint address (string) — save this to LAPORPOINTS_MINT_ADDRESS.
    """
    settings = get_settings()
    authority = load_mint_authority()
    async with AsyncClient(settings.solana_rpc_url) as client:
        token = await AsyncToken.create_mint(
            conn=client,
            payer=authority,
            mint_authority=authority.pubkey(),
            decimals=LPT_DECIMALS,
            program_id=TOKEN_PROGRAM_ID,
            freeze_authority=authority.pubkey(),
        )
        return str(token.pubkey)


def new_citizen_wallet() -> dict[str, str]:
    """Generate a fresh custodial Solana wallet for a citizen.

    Returns dict with `address` and `secret` (base58). Secret must be stored
    encrypted in production — for the hackathon it is kept in the local store.
    """
    kp = Keypair()
    return {
        "address": str(kp.pubkey()),
        "secret": json.dumps(list(bytes(kp))),
    }


def _keypair_from_secret(secret: str) -> Keypair:
    return Keypair.from_bytes(bytes(json.loads(secret)))


async def _get_token(client: AsyncClient) -> AsyncToken:
    settings = get_settings()
    authority = load_mint_authority()
    mint = Pubkey.from_string(settings.laporpoints_mint_address)
    return AsyncToken(client, mint, TOKEN_PROGRAM_ID, authority)


async def mint_lpt(citizen_wallet_address: str, amount: int) -> dict[str, str]:
    """Mint `amount` LaporPoints to a citizen's wallet (creates ATA if needed).

    Returns the transaction signature and a Solscan proof URL.
    """
    settings = get_settings()
    authority = load_mint_authority()
    owner = Pubkey.from_string(citizen_wallet_address)
    async with AsyncClient(settings.solana_rpc_url) as client:
        token = await _get_token(client)
        ata = await token.create_associated_token_account(owner, skip_confirmation=False)
        resp = await token.mint_to(
            dest=ata,
            mint_authority=authority,
            amount=amount,
            opts=TxOpts(skip_confirmation=False, skip_preflight=False),
        )
        sig = str(resp.value)
        await client.confirm_transaction(resp.value, commitment=Confirmed)
        return {
            "signature": sig,
            "solscan_url": solscan_url(sig),
            "ata": str(ata),
            "amount": str(amount),
        }


async def burn_lpt(
    citizen_wallet_address: str, citizen_wallet_secret: str, amount: int
) -> dict[str, str]:
    """Burn `amount` LaporPoints from a citizen's wallet on redemption.

    Two-signer transaction: the mint authority pays the fee (the custodial
    citizen wallet holds no SOL), the citizen keypair authorizes the burn.
    """
    settings = get_settings()
    authority = load_mint_authority()
    owner_kp = _keypair_from_secret(citizen_wallet_secret)
    owner = Pubkey.from_string(citizen_wallet_address)
    mint = Pubkey.from_string(settings.laporpoints_mint_address)
    ata = get_associated_token_address(owner, mint)

    burn_ix = burn(
        BurnParams(
            program_id=TOKEN_PROGRAM_ID,
            account=ata,
            mint=mint,
            owner=owner,
            amount=amount,
        )
    )
    async with AsyncClient(settings.solana_rpc_url) as client:
        blockhash = (await client.get_latest_blockhash()).value.blockhash
        msg = Message.new_with_blockhash([burn_ix], authority.pubkey(), blockhash)
        tx = Transaction([authority, owner_kp], msg, blockhash)
        resp = await client.send_transaction(
            tx, opts=TxOpts(skip_confirmation=False, skip_preflight=False)
        )
        sig = str(resp.value)
        await client.confirm_transaction(resp.value, commitment=Confirmed)
        return {"signature": sig, "solscan_url": solscan_url(sig), "amount": str(amount)}


async def get_lpt_balance(citizen_wallet_address: str) -> int:
    """Read a citizen's on-chain LaporPoints balance. Returns 0 if no ATA yet."""
    settings = get_settings()
    owner = Pubkey.from_string(citizen_wallet_address)
    mint = Pubkey.from_string(settings.laporpoints_mint_address)
    async with AsyncClient(settings.solana_rpc_url, commitment=Confirmed) as client:
        token = await _get_token(client)
        ata = get_associated_token_address(owner, mint)
        try:
            balance = await token.get_balance(ata)
            return int(balance.value.amount)
        except Exception:
            return 0
