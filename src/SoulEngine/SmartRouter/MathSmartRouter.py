from decimal import Decimal
import logging
from typing import TypedDict

####################################
from src.DEX.Swap import Swap, SwapParamsTD
####################################

class SmartSwapResult(TypedDict):
    result: Decimal
    is_success: bool
    message: str


class MathSmartRouter:
    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)):
        self.logger = logger
        self.swap = Swap()

    def smart_swap(self, route: list[str], metadata: dict, state: dict, delta_amount: int | float | Decimal,
                   mint_in: str, mint_out: str, amount_specified_is_input: bool) -> SmartSwapResult:

        if not route:
            return {
                "result": Decimal("0"),
                "is_success": False,
                "message": "Empty route"
            }

        # 1) Normalizing route and setting current_mint
        current_mint = mint_in if amount_specified_is_input else mint_out

        processing_route = route if amount_specified_is_input else route[::-1]

        current_amount = Decimal(str(delta_amount)) if not isinstance(delta_amount, Decimal) else delta_amount

        # 2) Calculating swap result
        for pool in processing_route:
            try:
                pool_metadata = metadata.get(pool)
                pool_state = state.get(pool)

                if not pool_metadata or not pool_state:
                    return {
                        "result": Decimal("0"),
                        "is_success": False,
                        "message": f"Pool {pool} not found in metadata/state"
                    }

                mint0 = pool_metadata["mint0"]
                mint1 = pool_metadata["mint1"]
                dex = pool_metadata["dex"]
                version = pool_metadata["version"]

                if amount_specified_is_input:
                    if current_mint == mint0:
                        x_to_y = True  # 0 -> 1
                        next_mint = mint1
                    elif current_mint == mint1:
                        x_to_y = False  # 1 -> 0
                        next_mint = mint0
                    else:
                        raise ValueError(f"Token {current_mint} not found in pool {pool} ({mint0}/{mint1})")
                else:
                    if current_mint == mint1:
                        x_to_y = True  # 0 -> 1 produces mint1
                        next_mint = mint0  # We need to input mint0
                    elif current_mint == mint0:
                        x_to_y = False  # 1 -> 0 produces mint0
                        next_mint = mint1  # We need to input mint1
                    else:
                        raise ValueError(f"Token {current_mint} not found in pool {pool} ({mint0}/{mint1})")

                swap_result = self.swap.swap(
                    dex=dex,
                    version=version,
                    params=SwapParamsTD(metadata=pool_metadata,
                                        pool_state=pool_state,
                                        delta_amount=current_amount,
                                        x_to_y=x_to_y,
                                        amount_specified_is_input=amount_specified_is_input)
                )

                if swap_result["message"] != "success":
                    raise Exception(f"Math calculation failed: {swap_result['message']}")

                if swap_result["remain"] > Decimal('1'):
                    raise Exception(f"Insufficient liquidity (Remain: {swap_result['remain']})")

                # Update state for next hop
                current_amount = swap_result['result']
                current_mint = next_mint

            except Exception as e:
                return {
                    "result": Decimal("0"),
                    "is_success": False,
                    "message": f"Error at pool {pool}: {str(e)}"
                }

        return {
            "result": current_amount,
            "is_success": True,
            "message": "success"
        }