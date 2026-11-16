#!/usr/bin/env python3
"""Phase B: launch the GAVEL coin on pump.fun. DO NOT RUN during phase A.

Flow:
  1. Load the creator keypair (the wallet linked to the make.fun account)
     from makefun-keypair.json. Its bytes are never printed.
  2. Load the mint keypair from gavel-mint-keypair.json, or generate one and
     save it there (mode 600) if it does not exist yet, so a re-run reuses
     the same mint instead of minting a second coin.
  3. Ask PumpPortal's local-trade API for an unsigned "create" transaction
     (with a small initial buy), sign it with both keypairs, and send it via
     the Solana RPC.
  4. Wait for confirmation, write LAUNCH.json into this repository, and print
     only the mint address and the transaction signature.

Guards: aborts before doing anything if the creator holds less than
0.04 SOL. Total spend target is ~0.03 SOL (0.01 initial buy + pump.fun
creation costs + fees).

Run with the newwallets venv:
  /home/hatch/workspace/newwallets/venv/bin/python launch.py
"""

import base64
import json
import os
import sys
import time

import requests
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction

CREATOR_KEYPAIR_PATH = "/home/hatch/workspace/makefun/makefun-keypair.json"
MINT_KEYPAIR_PATH = "/home/hatch/workspace/makefun/gavel-mint-keypair.json"
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
LAUNCH_JSON_PATH = os.path.join(REPO_DIR, "LAUNCH.json")

METADATA_URI = (
    "https://raw.githubusercontent.com/raraanzaii/"
    "makefun-coin-promo-01-entry/main/metadata.json"
)
PUMPPORTAL_URL = "https://pumpportal.fun/api/trade-local"
RPC_URL = "https://api.mainnet-beta.solana.com"

TOKEN_NAME = "GAVEL"
TOKEN_SYMBOL = "GAVEL"
INITIAL_BUY_SOL = 0.01
SLIPPAGE = 10
PRIORITY_FEE_SOL = 0.0005
MIN_CREATOR_BALANCE_SOL = 0.04  # hard guard: below this, abort
CONFIRM_TIMEOUT_SECONDS = 90


def fail(message: str) -> "SystemExit":
    print(f"error: {message}", file=sys.stderr)
    return SystemExit(1)


def rpc(method: str, params: list):
    """One JSON-RPC call against the Solana mainnet RPC."""
    resp = requests.post(
        RPC_URL,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        timeout=30,
    )
    resp.raise_for_status()
    body = resp.json()
    if "error" in body:
        raise fail(f"RPC {method} failed: {body['error']}")
    return body["result"]


def load_keypair(path: str) -> Keypair:
    with open(path, "r") as fh:
        raw = json.load(fh)
    return Keypair.from_bytes(bytes(raw))


def load_or_create_mint_keypair() -> Keypair:
    """Reuse the saved mint keypair, or generate and persist a new one."""
    if os.path.exists(MINT_KEYPAIR_PATH):
        return load_keypair(MINT_KEYPAIR_PATH)
    mint = Keypair()
    fd = os.open(MINT_KEYPAIR_PATH, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as fh:
        json.dump(list(bytes(mint)), fh)
    os.chmod(MINT_KEYPAIR_PATH, 0o600)
    return mint


def creator_balance_sol(creator: Keypair) -> float:
    result = rpc("getBalance", [str(creator.pubkey())])
    return result["value"] / 1_000_000_000


def request_create_transaction(creator: Keypair, mint: Keypair) -> VersionedTransaction:
    """Ask PumpPortal to build the unsigned pump.fun create transaction."""
    payload = {
        "publicKey": str(creator.pubkey()),
        "action": "create",
        "tokenMetadata": {
            "name": TOKEN_NAME,
            "symbol": TOKEN_SYMBOL,
            "uri": METADATA_URI,
        },
        "mint": str(mint.pubkey()),
        "denominatedInSol": "true",
        "amount": INITIAL_BUY_SOL,
        "slippage": SLIPPAGE,
        "priorityFee": PRIORITY_FEE_SOL,
        "pool": "pump",
    }
    resp = requests.post(PUMPPORTAL_URL, json=payload, timeout=60)
    if resp.status_code != 200:
        raise fail(
            f"PumpPortal answered HTTP {resp.status_code}: {resp.text[:200]}"
        )
    return VersionedTransaction.from_bytes(resp.content)


def send_transaction(signed: VersionedTransaction) -> str:
    encoded = base64.b64encode(bytes(signed)).decode("ascii")
    return rpc(
        "sendTransaction",
        [encoded, {"skipPreflight": False, "maxRetries": 3, "encoding": "base64"}],
    )


def wait_for_confirmation(signature: str) -> None:
    deadline = time.time() + CONFIRM_TIMEOUT_SECONDS
    while time.time() < deadline:
        result = rpc(
            "getSignatureStatuses", [[signature], {"searchTransactionHistory": True}]
        )
        status = (result.get("value") or [None])[0]
        if status is not None:
            if status.get("err") is not None:
                raise fail(f"transaction failed on-chain: {status['err']}")
            if status.get("confirmationStatus") in ("confirmed", "finalized"):
                return
        time.sleep(2)
    raise fail(f"transaction not confirmed within {CONFIRM_TIMEOUT_SECONDS}s")


def main() -> int:
    creator = load_keypair(CREATOR_KEYPAIR_PATH)

    balance = creator_balance_sol(creator)
    if balance < MIN_CREATOR_BALANCE_SOL:
        raise fail(
            f"creator balance {balance:.4f} SOL is below the "
            f"{MIN_CREATOR_BALANCE_SOL} SOL guard; aborting before any spend"
        )

    mint = load_or_create_mint_keypair()

    unsigned = request_create_transaction(creator, mint)
    # solders signs a versioned transaction by constructing it from the
    # message plus the signer keypairs; verify locally before sending.
    signed = VersionedTransaction(unsigned.message, [creator, mint])
    signed.verify_and_hash_message()

    signature = send_transaction(signed)
    wait_for_confirmation(signature)

    with open(LAUNCH_JSON_PATH, "w") as fh:
        json.dump(
            {"mint": str(mint.pubkey()), "create_signature": signature},
            fh,
            indent=2,
        )
        fh.write("\n")

    print(str(mint.pubkey()))
    print(signature)
    return 0


if __name__ == "__main__":
    sys.exit(main())
