import math

import redis
import os
from typing import TypedDict
import json
import time

####################################
from src.Config import config
from src.Config.BasicSchemeAndTypeDict import ColdPathScheme
from src.LoggerHandler.logger import get_logger, setup_logger
from src.SoulEngine.SmartRouter.MathSmartRouter import MathSmartRouter
####################################



class SmartOutputTD(TypedDict):
    result: int | float
    success: bool
    error_code: int
    message: str



ERROR_CODES = {
    1: "Cold path not found.",
    2: "Error parsing cold path.",
    3: "Couldn't validate cold path schema.",
    4: "Cold path expired.",
    5: "Math calculation failed.",
    6: "Error in MathSmartRouter.",
    7: "Insufficient liquidity.",
    8: "max/min variable is Infinite",
    9: "Unknown error."
  }

def _error(code: int, detail: str = "") -> SmartOutputTD:
    msg = ERROR_CODES.get(code, "Unknown error")
    if detail:
        msg = f"{msg} {detail}"
    return {"result": 0, "success": False, "error_code": code, "message": msg}




class SmartRouter:
    def __init__(self, logger_name: str = "SmartRouter", log_file: str = "SmartRouter.log"):
        setup_logger(logger_name=logger_name, log_file=os.path.join(config.LOG_MAIN_FOLDER, log_file))
        self.logger = get_logger(logger_name)
        self.r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
        self.math_router = MathSmartRouter(self.logger)
        self.route_expired = 60 * 3
        self.COLD_PATH_CACHE_TTL = 5
        self.COLD_PATH_CACHE: dict[str, tuple[ColdPathScheme, float]] = {}

    def _get_cold_path(self, base_mint: str, quote_mint: str) -> ColdPathScheme | tuple[int, str]:
        current_time = int(time.time())
        cached_cold_path = self.COLD_PATH_CACHE.get(f'{base_mint}/{quote_mint}')
        if cached_cold_path:
            cold_path, cached_cold_path_ts = cached_cold_path
            if abs(current_time - cached_cold_path_ts) < self.COLD_PATH_CACHE_TTL:
                if abs(current_time - int(cold_path.ts)) < self.route_expired:
                    return cold_path


        cold_path_unsterilized = self.r.hget(config.REDIS_KEY_COLD_PATH, f'{base_mint}/{quote_mint}')
        if not cold_path_unsterilized:
            return 1, ""

        try:
            cold_path_sterilized = json.loads(cold_path_unsterilized)
        except Exception as e:
            return 2, f"{e}"

        try:
            cold_path = ColdPathScheme(**cold_path_sterilized)
        except Exception as e:
            return 3, f"{e}"

        ts = int(cold_path.ts)
        if abs(current_time - ts) > self.route_expired:
            return 4, ""

        self.COLD_PATH_CACHE[f'{base_mint}/{quote_mint}'] = (cold_path, current_time)
        return cold_path


    def ExactSwap(self, base_mint: str, quote_mint: str, delta_amount: float | int,
                  metadata: dict, state: dict, amount_specified_is_input: bool = True) -> SmartOutputTD:
        cold_path = self._get_cold_path(base_mint, quote_mint)
        if not isinstance(cold_path, ColdPathScheme):
            return _error(cold_path[0], cold_path[1])

        _max = -math.inf
        _min = math.inf

        for route in cold_path.routes:
            try:
                smart_swap_result = self.math_router.smart_swap(route=route,
                                                                delta_amount=delta_amount,
                                                                mint_in=base_mint,
                                                                mint_out=quote_mint,
                                                                metadata=metadata,
                                                                state=state,
                                                                amount_specified_is_input=amount_specified_is_input)

                if smart_swap_result["is_success"]:
                    val = int(smart_swap_result["result"])
                    _max = max(_max, val)
                    _min = min(_min, val)
                else:
                    self.logger.warning(f"Error in MathSmartRouter: {smart_swap_result['message']}. route: {route}")

            except Exception as e:
                self.logger.warning(f"Error in MathSmartRouter: {e}. route: {route}")

        if amount_specified_is_input:
            if _max != -math.inf:
                return {"result": _max, "success": True, "error_code": 0, "message": "success"}
            return _error(7)
        else:
            if _min != math.inf:
                return {"result": _min, "success": True, "error_code": 0, "message": "success"}
            return _error(7)

