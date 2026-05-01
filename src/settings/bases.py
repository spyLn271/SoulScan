from decimal import Decimal

Bases = {
    'solana': [
        'So11111111111111111111111111111111111111112',
        'mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So',
        'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
        'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
        'cbbtcf3aa214zXHbiAZQwf4122FBYbraNdFqgw4iMij'
    ],
    'ethereum': ['ETH', 'USDC', 'USDT', 'WBTC', 'DAI', 'UNI'],
    'base': ['ETH', 'USDC', 'USDT', 'WBTC', 'DAI', 'UNI'],
    'arbitrum': ['ETH', 'USDC', 'USDT', 'WBTC', 'DAI', 'UNI'],
    'avalanche': ['AVAX', 'USDC', 'USDT', 'WBTC', 'DAI', 'UNI', 'WETH'],
    'op_mainnet': ['ETH', 'USDC', 'USDT', 'WBTC', 'DAI', 'UNI'],
    'polygon': ['POL', 'USDC', 'USDT', 'WBTC', 'DAI', 'UNI', 'WETH'],
    'bsc': ['BNB', 'USDC', 'USDT', 'WBTC', 'DAI', 'UNI', 'WETH'],
    'unichain': ['ETH', 'USDC', 'USDT', 'WBTC', 'DAI', 'UNI'],
}

SecondBases = {
    "solana": ['USD1ttGY1N17NEEHLmELoaybftRBUSErhqYiQzvEmuB']
}

ExcludeBases = {
    "solana": [
        'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
        'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
        'USD1ttGY1N17NEEHLmELoaybftRBUSErhqYiQzvEmuB',
        'CASHx9KJUStyftLFWGvEVf59SGeG9sh5FfcnZMVPCASH'
    ]
}

AMOUNT_PROBE = [
    Decimal("500_000"),
    Decimal("250_000"),
    Decimal("125_000"),
    Decimal("62_500"),
    Decimal("31_250"),
    Decimal("15_625"),
    Decimal("7812.5"),
    Decimal("1000"),
    Decimal("500"),
    Decimal("100"),
    Decimal("1"),
    Decimal("0.1")
]
SUPPORTED_QUOTES_SOLANA = [
    'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
    'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',  # USDT
]

SUPPORTED_QUOTES_EVM = {
    'ethereum': {
        'USDC': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
        'USDT': '0xdac17f958d2ee523a2206206994597c13d831ec7'
    },
    'arbitrum': {
        'USDC': '0xaf88d065e77c8cc2239327c5edb3a432268e5831',
        'USDT': '0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9'
    },
    'avalanche': {
        'USDC': '0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e',
        'USDT': '0x9702230a8ea53601f5cd2dc00fdbc13d4df4a8c7'
    },
    'base': {
        'USDC': '0x833589fcd6edb6e08f4c7c32d4f71b54bda02913',
        'USDT': '0xfde4c96c8593536e31f229ea8f37b2ada2699bb2'
    },
    'op_mainnet': {
        'USDC': '0x0b2c639c533813f4aa9d7837caf62653d097ff85',
        'USDT': '0x94b008aa00579c1307b0ef2c499ad98a8ce58e58'
    },
    'polygon': {
        'USDC': '0x3c499c542cef5e3811e1192ce70d8cc03d5c3359',
        'USDT': '0xc2132d05d31c914a87c6611c10748aeb04b58e8f'
    },
    'bsc': {
        'USDC': '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d',
        'USDT': '0x55d398326f99059ff775485246999027b3197955'
    },
    'unichain': {
        'USDC': '0x078d782b760474a361dda0af3839290b0ef57ad6',
        'USDT': '0x588ce4f028d8e7b53b687865d6a67b3a54c75518'
    }
}