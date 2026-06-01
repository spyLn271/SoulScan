from decimal import Decimal

Bases = {
    'solana': [
        'So11111111111111111111111111111111111111112',
        'mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So',
        'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
        'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
        'cbbtcf3aa214zXHbiAZQwf4122FBYbraNdFqgw4iMij',
    ],
    'eth': [
        '0x0000000000000000000000000000000000000000',
        '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
        '0xdac17f958d2ee523a2206206994597c13d831ec7',
        '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599',
        '0x6b175474e89094c44da98b954eedeac495271d0f',
    ],
    'base': [
        '0x0000000000000000000000000000000000000000',
        '0x833589fcd6edb6e08f4c7c32d4f71b54bda02913',
        '0xfde4c96c8593536e31f229ea8f37b2ada2699bb2',
        '0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf',
        '0x50c5725949a6f0c72e6c4a641f24049a917db0cb',
    ],
    'arbitrum': [
        '0x0000000000000000000000000000000000000000',
        '0xaf88d065e77c8cc2239327c5edb3a432268e5831',
        '0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9',
        '0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f',
        '0xda10009cbd5d07dd0cecc66161fc93d7c9000da1',
    ],
    'bsc': [
        '0x0000000000000000000000000000000000000000',
        '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d',
        '0x55d398326f99059ff775485246999027b3197955',
        '0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c',
        '0x1af3f329e8be154074d8769d1ffa4ee058b1dbc3',
        '0x2170ed0880ac9a755fd29b2688956bd959f933f8',
    ],
}

SecondBases = {
    "solana": ['USD1ttGY1N17NEEHLmELoaybftRBUSErhqYiQzvEmuB'],
    "eth": [],
    "base": [],
    "arbitrum": [],
    "bsc": []
}

ExcludeBases = {
    "solana": [
        'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
        'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',  # USDT
        'USD1ttGY1N17NEEHLmELoaybftRBUSErhqYiQzvEmuB',  # USD1
        'CASHx9KJUStyftLFWGvEVf59SGeG9sh5FfcnZMVPCASH',  # CASH
        '2b1kV6DkPAnxd5ixfnxCpjxmKwqjjaYmCZfHsFu24GXo',  # PYUSD
        'USDSwr9ApdHk5bvJKMjzff41FfuX8bSxdKcR81vTwcA',  # USDS
        'DEkqHyPN7GMRJ5cArtQFAWefqbZb33Hyf6s5iCwjEonT',  # USDe
        '9zNQRsGLjNKwCUU5Gq5LR8beUCPzQMVMqKAi3SSZh54u',  # FDUSD
        '2u1tszSeqZ3qBWF3uNGPFc8TzMk2tdiwknnRMWGWjGWH',  # USDG
        'AUSD1jCcCyPLybk1YnvPWsHQSrZ46dxwoMniN4N2UEB9',  # AUSD
        'A1KLoBrKBde8Ty9qtNQUtq3C2ortoC3u7twggz7sEto6',  # USDY
        'susdabGDNbhrnCa6ncrYo81u4s9GM8ecK2UwMyZiq4X',  # sUSD
    ],

    "eth": [
        '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',  # USDC
        '0xdac17f958d2ee523a2206206994597c13d831ec7',  # USDT
        '0x6b175474e89094c44da98b954eedeac495271d0f',  # DAI
        '0x8d0d000ee44948fc98c9b98a4fa4921476f08b0d',  # USD1
        '0x6c3ea9036406852006290770bedfcaba0e23a0e8',  # PYUSD
        '0xdc035d45d973e3ec169d2276ddab16f1e407384f',  # USDS
        '0x4c9edd5852cd905f086c759e8383e09bff1e68b3',  # USDe
        '0xc5f0f7b66764f6ec8c8dff7ba683102295e16409',  # FDUSD
        '0xe343167631d89b6ffc58b88d6b7fb0228795491d',  # USDG
        '0x00000000efe302beaa2b3e6e1b18d08d69a9012a',  # AUSD
        '0x96f6ef951840721adbf46ac996b59e0235cb985c',  # USDY
    ],

    "base": [
        '0x833589fcd6edb6e08f4c7c32d4f71b54bda02913',  # USDC
        '0xfde4c96c8593536e31f229ea8f37b2ada2699bb2',  # USDT
        '0x50c5725949a6f0c72e6c4a641f24049a917db0cb',  # DAI
        '0x820c137fa70c8691f0e44dc420a5e53c168921dc',  # USDS
        '0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34',  # USDe
        '0x00000000efe302beaa2b3e6e1b18d08d69a9012a',  # AUSD
    ],

    "arbitrum": [
        '0xaf88d065e77c8cc2239327c5edb3a432268e5831',  # USDC
        '0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9',  # USDT
        '0xda10009cbd5d07dd0cecc66161fc93d7c9000da1',  # DAI
        '0x46850ad61c2b7d64d08c9c754f45254596696984',  # PYUSD
        '0x6491c05a82219b8d1479057361ff1654749b876b',  # USDS
        '0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34',  # USDe
        '0x93c9932e4afa59201f0b5e63f7d816516f1669fe',  # FDUSD
        '0x00000000efe302beaa2b3e6e1b18d08d69a9012a',  # AUSD
        '0x35e050d3c0ec2d29d269a8ecea763a183bdf9a9d',  # USDY
    ],

    "bsc": [
        '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d',  # USDC
        '0x55d398326f99059ff775485246999027b3197955',  # USDT
        '0x1af3f329e8be154074d8769d1ffa4ee058b1dbc3',  # DAI
        '0x8d0d000ee44948fc98c9b98a4fa4921476f08b0d',  # USD1
        '0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34',  # USDe
        '0xc5f0f7b66764f6ec8c8dff7ba683102295e16409',  # FDUSD
        '0x00000000efe302beaa2b3e6e1b18d08d69a9012a',  # AUSD
    ],
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


SUPPORTED_QUOTES: dict[str, list] = {
    'solana': [
        'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
        'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
    ],
    'eth': [
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "0xdac17f958d2ee523a2206206994597c13d831ec7"
    ],
    'arbitrum':[
        "0xaf88d065e77c8cc2239327c5edb3a432268e5831",
        "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9"
    ],
    'base': [
        '0x833589fcd6edb6e08f4c7c32d4f71b54bda02913',
        '0xfde4c96c8593536e31f229ea8f37b2ada2699bb2'
    ],
    'bsc': [
        '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d',
        '0x55d398326f99059ff775485246999027b3197955'
    ],
}