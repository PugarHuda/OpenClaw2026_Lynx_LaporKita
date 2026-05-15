"""One-time Solana setup: create the LaporPoints (LPT) SPL token mint.

Run once after funding the mint-authority wallet with devnet SOL:

    python scripts/setup_solana.py

Then copy the printed mint address into .env as LAPORPOINTS_MINT_ADDRESS.
"""
from __future__ import annotations

import asyncio

from solana.rpc.async_api import AsyncClient

from agent.config import get_settings
from agent.tools.solana_token import create_laporpoints_mint, load_mint_authority


async def main() -> None:
    settings = get_settings()
    authority = load_mint_authority()
    print(f"Mint authority wallet: {authority.pubkey()}")

    async with AsyncClient(settings.solana_rpc_url) as client:
        balance = await client.get_balance(authority.pubkey())
        sol = balance.value / 1_000_000_000
        print(f"Balance: {sol} SOL")
        if sol < 0.05:
            print("\nERROR: Saldo SOL kurang. Airdrop dulu:")
            print(f"  https://faucet.solana.com  (address: {authority.pubkey()})")
            print("  atau: solana airdrop 1 <address> --url devnet")
            return

    print("\nMembuat LaporPoints (LPT) SPL token mint...")
    mint_address = await create_laporpoints_mint()
    print("\n=== MINT CREATED ===")
    print(f"LAPORPOINTS_MINT_ADDRESS={mint_address}")
    print(f"Solscan: https://solscan.io/token/{mint_address}?cluster=devnet")
    print("\nTambahkan baris LAPORPOINTS_MINT_ADDRESS di atas ke file .env")


if __name__ == "__main__":
    asyncio.run(main())
