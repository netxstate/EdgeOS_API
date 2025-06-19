from web3 import Web3

from app.core.config import settings
from app.core.logger import logger


def verify_safe_signature(safe_address: str, signature_hex: str) -> bool:
    logger.info('Verifying safe signature for address: %s', safe_address)
    logger.info('Signature: %s', signature_hex)
    logger.info('Message hash: %s', settings.WORLD_LOGIN_MESSAGE_HASH)
    w3 = Web3(Web3.HTTPProvider(settings.WORLD_CHAIN_URL))
    abi = [
        {
            'constant': True,
            'inputs': [
                {'name': 'hash', 'type': 'bytes32'},
                {'name': 'signature', 'type': 'bytes'},
            ],
            'name': 'isValidSignature',
            'outputs': [{'name': 'magic', 'type': 'bytes4'}],
            'type': 'function',
        }
    ]
    safe = w3.eth.contract(address=w3.to_checksum_address(safe_address), abi=abi)
    message_hash = settings.WORLD_LOGIN_MESSAGE_HASH
    try:
        magic = safe.functions.isValidSignature(
            message_hash, bytes.fromhex(signature_hex[2:])
        ).call()
        return magic == b'\x16&\xba~'
    except Exception as e:
        logger.error('Error verifying safe signature: %s', e)
        return False
