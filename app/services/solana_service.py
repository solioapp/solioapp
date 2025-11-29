"""Solana blockchain service."""
import base64
import json
from decimal import Decimal
from typing import Optional

import requests
from flask import current_app
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
import base58


def get_rpc_url():
    """Get the appropriate RPC URL based on config."""
    if current_app.config.get('USE_DEVNET'):
        return current_app.config.get('SOLANA_DEVNET_RPC_URL', 'https://api.devnet.solana.com')
    return current_app.config.get('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com')


def rpc_request(method: str, params: list = None):
    """Make a JSON-RPC request to Solana."""
    rpc_url = get_rpc_url()

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or []
    }

    try:
        response = requests.post(
            rpc_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        current_app.logger.error(f"Solana RPC error: {e}")
        return None


def verify_wallet_signature(wallet_address: str, message: str, signature: str) -> bool:
    """
    Verify a wallet signature for authentication.

    Args:
        wallet_address: The Solana public key (base58)
        message: The message that was signed
        signature: The signature (base58 or base64)
    """
    try:
        # Decode public key
        public_key_bytes = base58.b58decode(wallet_address)

        # Decode signature (try base58 first, then base64)
        try:
            signature_bytes = base58.b58decode(signature)
        except Exception:
            try:
                signature_bytes = base64.b64decode(signature)
            except Exception:
                return False

        # Message bytes
        message_bytes = message.encode('utf-8')

        # Verify using Ed25519
        verify_key = VerifyKey(public_key_bytes)
        verify_key.verify(message_bytes, signature_bytes)

        return True

    except BadSignatureError:
        return False
    except Exception as e:
        current_app.logger.error(f"Signature verification error: {e}")
        return False


def verify_transaction(
    tx_signature: str,
    expected_recipient: str,
    expected_amount_sol: Decimal,
    expected_sender: str
) -> dict:
    """
    Verify a transaction on the Solana blockchain.

    Returns dict with 'success' boolean and optional 'error' message.
    """
    import time

    # Retry logic - transaction may not be immediately visible
    max_retries = 10
    retry_delay = 2  # seconds

    tx = None
    for attempt in range(max_retries):
        # Get transaction details
        result = rpc_request("getTransaction", [
            tx_signature,
            {
                "encoding": "jsonParsed",
                "maxSupportedTransactionVersion": 0
            }
        ])

        if result and 'result' in result and result['result'] is not None:
            tx = result['result']
            break

        # Transaction not found yet, wait and retry
        if attempt < max_retries - 1:
            current_app.logger.info(f"Transaction {tx_signature} not found, retry {attempt + 1}/{max_retries}")
            time.sleep(retry_delay)

    if tx is None:
        return {'success': False, 'error': 'Transaction not found or not confirmed after retries'}

    # Check if transaction was successful
    meta = tx.get('meta', {})
    if meta.get('err') is not None:
        return {'success': False, 'error': 'Transaction failed'}

    # Parse transaction for SOL transfer
    try:
        message = tx.get('transaction', {}).get('message', {})
        instructions = message.get('instructions', [])

        # Look for system program transfer
        for instruction in instructions:
            program = instruction.get('program')
            parsed = instruction.get('parsed', {})

            if program == 'system' and parsed.get('type') == 'transfer':
                info = parsed.get('info', {})

                source = info.get('source', '')
                destination = info.get('destination', '')
                lamports = info.get('lamports', 0)

                # Convert lamports to SOL
                amount_sol = Decimal(str(lamports)) / Decimal('1000000000')

                # Verify sender
                if source != expected_sender:
                    continue

                # Verify recipient
                if destination != expected_recipient:
                    continue

                # Verify amount (allow small tolerance for rounding)
                tolerance = Decimal('0.000001')
                if abs(amount_sol - expected_amount_sol) > tolerance:
                    continue

                return {'success': True}

        return {'success': False, 'error': 'Transfer not found in transaction'}

    except Exception as e:
        current_app.logger.error(f"Transaction parsing error: {e}")
        return {'success': False, 'error': 'Transaction processing error'}


def send_sol(
    recipient: str,
    amount_sol: Decimal,
    sender_secret: str
) -> dict:
    """
    Send SOL from platform wallet to recipient.

    This requires the platform wallet's secret key.
    Returns dict with 'success', 'signature' or 'error'.
    """
    try:
        from solders.keypair import Keypair
        from solders.pubkey import Pubkey
        from solders.system_program import TransferParams, transfer
        from solders.transaction import Transaction
        from solders.message import Message

        # Decode sender keypair
        sender_keypair = Keypair.from_base58_string(sender_secret)

        # Get recipient pubkey
        recipient_pubkey = Pubkey.from_string(recipient)

        # Convert SOL to lamports
        lamports = int(amount_sol * Decimal('1000000000'))

        # Get recent blockhash
        blockhash_result = rpc_request("getLatestBlockhash", [{"commitment": "finalized"}])
        if not blockhash_result or 'result' not in blockhash_result:
            return {'success': False, 'error': 'Failed to get blockhash'}

        blockhash = blockhash_result['result']['value']['blockhash']

        # Create transfer instruction
        transfer_ix = transfer(
            TransferParams(
                from_pubkey=sender_keypair.pubkey(),
                to_pubkey=recipient_pubkey,
                lamports=lamports
            )
        )

        # Create and sign transaction
        from solders.hash import Hash
        recent_blockhash = Hash.from_string(blockhash)

        msg = Message.new_with_blockhash(
            [transfer_ix],
            sender_keypair.pubkey(),
            recent_blockhash
        )

        tx = Transaction.new_unsigned(msg)
        tx.sign([sender_keypair], recent_blockhash)

        # Send transaction
        tx_bytes = bytes(tx)
        tx_base64 = base64.b64encode(tx_bytes).decode('utf-8')

        send_result = rpc_request("sendTransaction", [
            tx_base64,
            {"encoding": "base64", "preflightCommitment": "confirmed"}
        ])

        if send_result and 'result' in send_result:
            return {
                'success': True,
                'signature': send_result['result']
            }
        elif send_result and 'error' in send_result:
            return {
                'success': False,
                'error': send_result['error'].get('message', 'Unknown error')
            }
        else:
            return {'success': False, 'error': 'Failed to send transaction'}

    except ImportError:
        current_app.logger.error("solders library not installed")
        return {'success': False, 'error': 'Solana library not installed'}
    except Exception as e:
        current_app.logger.error(f"Send SOL error: {e}")
        return {'success': False, 'error': str(e)}


def get_balance(wallet_address: str) -> Optional[Decimal]:
    """Get SOL balance for a wallet address."""
    result = rpc_request("getBalance", [wallet_address])

    if result and 'result' in result:
        lamports = result['result'].get('value', 0)
        return Decimal(str(lamports)) / Decimal('1000000000')

    return None


def get_transaction_status(tx_signature: str) -> Optional[str]:
    """Get the status of a transaction."""
    result = rpc_request("getSignatureStatuses", [[tx_signature]])

    if result and 'result' in result:
        value = result['result'].get('value', [None])[0]
        if value:
            if value.get('err'):
                return 'failed'
            if value.get('confirmationStatus') == 'finalized':
                return 'confirmed'
            return 'pending'

    return None
