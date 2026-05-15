"""Doku Payer tool — connects to the DOKU MCP Server to generate civic retribusi bills.

LaporKita's reward model is "Civic Credit": citizens spend earned LaporPoints (LPT)
to offset government retribusi bills. This module talks to the DOKU MCP Server
(the same one judged in the Best Payment Track) to generate QRIS/VA payment
instructions for the remaining balance.

Architecture note: we connect to DOKU's MCP server as an MCP *client* from Python,
so both the agent loop and deterministic backend flows use one integration path.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from agent.config import get_settings


@asynccontextmanager
async def _doku_session():
    """Open an authenticated MCP client session to the DOKU MCP Server."""
    settings = get_settings()
    # DOKU API expects HTTP Basic Auth: "Basic <base64(api_key:)>".
    auth = settings.doku_authorization_base64
    if not auth.startswith("Basic "):
        auth = f"Basic {auth}"
    headers = {
        "Client-Id": settings.doku_client_id,
        "Authorization": auth,
    }
    async with streamablehttp_client(settings.doku_mcp_url, headers=headers) as (
        read,
        write,
        _,
    ):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def list_doku_tools() -> list[str]:
    """Discover available DOKU MCP tools (used to verify connectivity + schema)."""
    async with _doku_session() as session:
        result = await session.list_tools()
        return [t.name for t in result.tools]


async def _call_doku(tool_name: str, tool_request: dict[str, Any]) -> dict[str, Any]:
    """Invoke a single DOKU MCP tool and return its structured result.

    All DOKU MCP tools wrap parameters in a top-level `toolRequest` object.
    """
    async with _doku_session() as session:
        result = await session.call_tool(
            tool_name, arguments={"toolRequest": tool_request}
        )
        # MCP returns content blocks; structured tools put JSON in the first block.
        if result.structuredContent:
            return result.structuredContent
        text = "".join(
            block.text for block in result.content if getattr(block, "type", "") == "text"
        )
        return {"raw": text, "is_error": result.isError}


def _format_idr_amount(amount_idr: int) -> str:
    """DOKU expects amount as a 2-decimal string per ISO 4217 (e.g. '10000.00')."""
    return f"{amount_idr}.00"


def compute_civic_credit(
    retribusi_amount_idr: int,
    lpt_balance: int,
    rate_idr_per_lpt: int,
) -> dict[str, int]:
    """Compute how much LPT offsets a retribusi bill, and the remaining cash due.

    Args:
        retribusi_amount_idr: Total tagihan retribusi.
        lpt_balance: LaporPoints token balance citizen punya.
        rate_idr_per_lpt: Konversi (default Rp 1000 / LPT).

    Returns:
        Dict: lpt_used, idr_offset, cash_due_idr.
    """
    max_offset_idr = lpt_balance * rate_idr_per_lpt
    idr_offset = min(max_offset_idr, retribusi_amount_idr)
    lpt_used = (idr_offset + rate_idr_per_lpt - 1) // rate_idr_per_lpt  # ceil-div
    cash_due = max(0, retribusi_amount_idr - idr_offset)
    return {
        "lpt_used": lpt_used,
        "idr_offset": idr_offset,
        "cash_due_idr": cash_due,
    }


async def create_retribusi_qris(
    invoice_number: str,
    amount_idr: int,
    citizen_name: str,
    description: str = "",
) -> dict[str, Any]:
    """Generate a QRIS payment for a retribusi bill via DOKU MCP.

    Returns the DOKU response containing the QRIS string / QR image data.
    Caller is responsible for the civic-credit offset (compute_civic_credit).
    """
    if amount_idr <= 0:
        return {
            "status": "fully_covered_by_lpt",
            "partnerReferenceNo": invoice_number,
            "amount_idr": 0,
            "note": "Tagihan sepenuhnya tertutup LaporPoints — tidak perlu QRIS.",
        }
    return await _call_doku(
        "create_qris_payment",
        {
            "amount": _format_idr_amount(amount_idr),
            "partnerReferenceNo": invoice_number,
        },
    )


async def create_retribusi_va(
    invoice_number: str,
    amount_idr: int,
    citizen_name: str,
    channel: str = "VIRTUAL_ACCOUNT_BCA",
) -> dict[str, Any]:
    """Generate a Virtual Account payment for a retribusi bill via DOKU MCP.

    `channel` is a DOKU channel code, e.g. VIRTUAL_ACCOUNT_BCA,
    VIRTUAL_ACCOUNT_BANK_MANDIRI, VIRTUAL_ACCOUNT_BRI.
    """
    return await _call_doku(
        "create_virtual_account_payment",
        {
            "amount": _format_idr_amount(amount_idr),
            "channel": channel,
            "virtualAccountName": citizen_name,
            "trxId": invoice_number,
        },
    )


async def check_payment_status(invoice_number: str) -> dict[str, Any]:
    """Poll payment status of a retribusi bill via DOKU MCP."""
    return await _call_doku(
        "get_transaction_by_invoice_number",
        {"invoiceNumber": invoice_number},
    )


# --- Sync wrappers for use in non-async contexts (e.g. quick scripts) ---
def create_retribusi_qris_sync(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return asyncio.run(create_retribusi_qris(*args, **kwargs))


def list_doku_tools_sync() -> list[str]:
    return asyncio.run(list_doku_tools())
