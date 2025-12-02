from decimal import Decimal

Bases = ["SOL", "mSOL", 'USDC', 'USDT', 'cbBTC']
Bases_mint = ['So11111111111111111111111111111111111111112',
              'mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So',
              'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
              'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
              'cbbtcf3aa214zXHbiAZQwf4122FBYbraNdFqgw4iMij']

Second_Bases = ['USD1']
Second_Bases_mint = ['USD1ttGY1N17NEEHLmELoaybftRBUSErhqYiQzvEmuB']

Bases_map = {
    'SOL': 'So11111111111111111111111111111111111111112',
    'mSOL': 'mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So',
    'cbBTC': 'cbbtcf3aa214zXHbiAZQwf4122FBYbraNdFqgw4iMij',
    'USDC': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
    'USDT': 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
    'USD1': 'USD1ttGY1N17NEEHLmELoaybftRBUSErhqYiQzvEmuB'
}
exclude_bases = ['EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
                 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
                 'USD1ttGY1N17NEEHLmELoaybftRBUSErhqYiQzvEmuB',
                 'CASHx9KJUStyftLFWGvEVf59SGeG9sh5FfcnZMVPCASH']

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