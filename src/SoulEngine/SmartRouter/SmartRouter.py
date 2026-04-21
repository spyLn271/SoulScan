import math
import redis
import os
from typing import TypedDict
import json
import time
import logging

####################################
from src.Config import config, Bases
from src.Config.BasicSchemeAndTypeDict import ColdPathScheme
from src.LoggerHandler.logger import get_logger, setup_logger
from src.SoulEngine.SmartRouter.MathSmartRouter import MathSmartRouter
####################################



class SmartOutputTD(TypedDict):
    result: int | float
    route: list[str]
    success: bool
    error_code: int
    message: str



SMART_ROUTER_ERROR_CODES = {
    1: "Cold path not found.",
    2: "Error parsing cold path.",
    3: "Couldn't validate cold path schema.",
    4: "Cold path expired.",
    5: "Math calculation failed.",
    6: "Error in MathSmartRouter.",
    7: "Insufficient liquidity.",
    8: "max/min variable is Infinite",
    9: "Unknown error.",
    10: "Not supported quotes mint"
  }

def _error(code: int, detail: str = "") -> SmartOutputTD:
    msg = SMART_ROUTER_ERROR_CODES.get(code, "Unknown error")
    if detail:
        msg = f"{msg} {detail}"
    return {"result": 0, "route": [], "success": False, "error_code": code, "message": msg}

def _success(result: int, route: list[str]) -> SmartOutputTD:
    return {"result": result, "route": route, "success": True, "error_code": 0, "message": "success"}




class SmartRouter:
    def __init__(self, metadata: dict, state: dict,
                 logger_name: str = "SmartRouter", log_file: str = "SmartRouter.log", logger: logging.Logger = None):
        if logger is None:
            setup_logger(logger_name=logger_name, log_file=os.path.join(config.LOG_MAIN_FOLDER, log_file))
            self.logger = get_logger(logger_name)
        else:
            self.logger = logger

        self.r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
        self.math_router = MathSmartRouter(self.logger)
        self.route_expired = 60 * 3
        self.COLD_PATH_CACHE_TTL = 5
        self.COLD_PATH_CACHE: dict[str, tuple[ColdPathScheme, float]] = {}
        self.metadata = metadata
        self.state = state

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
                  amount_specified_is_input: bool = True, a_to_b: bool = True) -> SmartOutputTD:
        """

        :param base_mint:
        :param quote_mint:
        :param delta_amount:
        :param amount_specified_is_input:
        :param a_to_b: 'a_to_b' means that base_mint is the input and quote_mint is the output.
                        Example: SOL/USDC -> SOL is the base_mint and USDC is the quote_mint.
                                 if a_to_b then SOL is exchanged for USDC.
                                 if not a_to_b then USDC is exchanged for SOL.
        :return:
        """

        if quote_mint not in Bases.SUPPORTED_QUOTES:
            return _error(10)
        start_time_cold_path_fetching = time.time()
        cold_path = self._get_cold_path(base_mint, quote_mint)
        self.logger.info(f"Cold path retrieval took {time.time() - start_time_cold_path_fetching} seconds")
        if not isinstance(cold_path, ColdPathScheme):
            return _error(cold_path[0], cold_path[1])

        _max = -math.inf
        _min = math.inf
        route_of_max = []
        route_of_min = []

        start_time_swap_calculation = time.perf_counter()
        for route in cold_path.routes:
            try:
                smart_swap_result = self.math_router.smart_swap(route=route,
                                                                delta_amount=delta_amount,
                                                                base_mint=base_mint,
                                                                quote_mint=quote_mint,
                                                                metadata=self.metadata,
                                                                state=self.state,
                                                                amount_specified_is_input=amount_specified_is_input,
                                                                a_to_b=a_to_b)

                if smart_swap_result["is_success"]:
                    val = int(smart_swap_result["result"])
                    if val > _max:
                        _max = val
                        route_of_max = route
                    if val < _min:
                        _min = val
                        route_of_min = route
                else:
                    self.logger.warning(f"Error in MathSmartRouter: {smart_swap_result['message']}. route: {route}")

            except Exception as e:
                self.logger.warning(f"Error in MathSmartRouter: {e}. route: {route}")
        self.logger.info(f"ExactSwap took {time.perf_counter() - start_time_swap_calculation} seconds")

        if amount_specified_is_input:
            if _max != -math.inf:
                return _success(int(_max), route=route_of_max)
            return _error(8)
        else:
            if _min != math.inf:
                return _success(int(_min), route=route_of_min)
            return _error(8)