import redis
import os
import time
import json

####################################
from src.Config import config
from src.CEX.contract_address_cex_checker.service.lookup import lookup_mint
from src.CEX.CEXAPI import get_exchange_asks, get_exchange_bids, cleanup_aggregator
from src.LoggerHandler.logger import setup_logger, get_logger
from src.SoulEngine.SmartRouter.SmartRouter import SmartRouter
####################################

CEX_QUOTES = ['USDC', 'USDT']
DEX_QUOTE = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'  # USDC
DEX_QUOTE_DECIMALS = 6
RESTRICTED_BASES = [
    'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
    'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',  # USDT
]

"""
Comparer takes only mint address then call mint look up for finding all CEX who offer that mint and what is the 
symbol of the mint. Then it will call the SmartRouter to find the best swap path for each CEX. Finally, it will 
calculate the profit of the swap and report the best swap path for each CEX.
"""


class Comparer:
    def __init__(self, r: redis.Redis, network: str, dex: str):
        logger_name = f'{dex}-Scanner-{network}-{os.getpid()}'
        log_file = os.path.join(config.LOG_MAIN_FOLDER, f'{logger_name}.log')
        setup_logger(logger_name=logger_name, log_file=log_file)
        self.logger = get_logger(logger_name)

        self.r = r
        self.network = network
        self.dex = dex

    async def start_comparing(self, base_mint: str, base_decimals: int, smart_router: SmartRouter):
        self.logger.info(
            f'Comparer started. (network: {self.network}, dex: {self.dex}, base_mint: {base_mint})')

        if base_mint in RESTRICTED_BASES:
            self.logger.warning(f'Base mint {base_mint} is in restricted bases list.')
            return

        mint_supported_cex = lookup_mint(base_mint)
        if not mint_supported_cex:
            self.logger.warning(f'Mint {base_mint} is not supported by any CEX.')
            return

        for cex, base_symbol in mint_supported_cex.items():
            self.logger.info(f'Processing CEX: {cex}, base_symbol: {base_symbol}')

            for quote_symbol in CEX_QUOTES:
                try:
                    # Probe ASK side (CEX->DEX: Buy on CEX, sell on DEX)
                    await self._probe_cex_ask(
                        cex=cex,
                        base_mint=base_mint,
                        base_symbol=base_symbol,
                        quote_symbol=quote_symbol,
                        smart_router=smart_router,
                        base_decimals=base_decimals,
                        quote_decimals=DEX_QUOTE_DECIMALS
                    )

                    # Probe BID side (DEX->CEX: Buy on DEX, sell on CEX)
                    await self._probe_cex_bid(
                        cex=cex,
                        base_mint=base_mint,
                        base_symbol=base_symbol,
                        quote_symbol=quote_symbol,
                        smart_router=smart_router,
                        base_decimals=base_decimals,
                        quote_decimals=DEX_QUOTE_DECIMALS
                    )

                except Exception as e:
                    self.logger.error(f'Error probing {cex} for {base_symbol}/{quote_symbol}: {e}')
                    continue

        self.logger.info(f'Comparer finished for {base_mint}')




    # =================================================================
    #  PRIVATE HELPER: The Core Logic Ported from V1 (https://github.com/spyLn271/JupiterArbitrageBot)
    # =================================================================

    async def _probe_cex_ask(self, cex: str, base_mint: str, base_symbol: str, quote_symbol: str,
                             smart_router: SmartRouter, base_decimals: int, quote_decimals: int):
        self.logger.info('_'*50)
        self.logger.info(f'Probe CEX-ASK for CEX: {cex} network:{self.network}, dex:{self.dex}, base_mint:{base_mint}, base_token:{quote_symbol}')
        start_time = time.time()

        orderbook = await get_exchange_asks(exchange=cex, symbol=f'{base_symbol}{quote_symbol}')
        cex_total_sum_out = 0  # some base token out
        cex_total_sum_in = 0  # USDC ot USDT in
        profit = 0
        order_number = 0
        best_swap = {
            'CEX_amountIn': 0,
            'CEX_amountOut': 0,
            'DEX_amountIn': 0,
            'DEX_amountOut': 0,
            'profit': 0,
            'CEX_start_price': float(orderbook[0][0]),
            'CEX_end_price': 0,
        }

        for order in orderbook:
            level_price = float(order[0])
            level_amount = float(order[1])
            order_number += 1
            self.logger.info(f'Order number: {order_number}, level_price: {level_price}, level_amount: {level_amount}')


            # ------ Greedy TEST Start ------
            # Adjusting amount in, taking in equation the swap fee, Human -> Atomic.
            greedy_delta_amount = (cex_total_sum_out + level_amount) * (1 - config.SWAPPER_FEE) * 10 ** base_decimals
            greedy_result_SmartRouter = smart_router.ExactSwap(base_mint=base_mint,
                                                               quote_mint=DEX_QUOTE,
                                                               delta_amount=greedy_delta_amount)

            self.logger.info(f'Greedy SmartRouter result: {greedy_result_SmartRouter}')
            # Normalizing amount, Atomic -> Human
            greedy_dex_sum_out = greedy_result_SmartRouter['result'] / 10 ** quote_decimals
            greedy_profit = greedy_dex_sum_out - (cex_total_sum_in + level_amount * level_price)

            if greedy_result_SmartRouter['success'] and greedy_profit > profit:
                cex_total_sum_out += level_amount
                cex_total_sum_in += level_amount * level_price

                self.logger.info(
                    f"\n============---- [ASK] Greedy Step Success ----============\n"
                    f" CEX            : {cex}\n"
                    f" Pair           : {base_mint}/{quote_symbol}\n"
                    f" Order Level    : {order_number} (Consumed full level)\n"
                    f"----------------------------------------------------------\n"
                    f" CEX Trade Size : {cex_total_sum_out} {base_mint}\n"
                    f" CEX Cost       : ${cex_total_sum_in}\n"
                    f" DEX Revenue    : ${greedy_dex_sum_out}\n"
                    f"----------------------------------------------------------\n"
                    f" Greedy Profit  : ${greedy_profit}\n"
                    f" Previous Best  : ${profit}\n"
                    f" VERDICT        : New Best! Skipping detailed probe.\n"
                    f"=========================================================="
                )
                profit = greedy_profit
                best_swap['CEX_amountIn'] = cex_total_sum_in
                best_swap['CEX_amountOut'] = cex_total_sum_out
                best_swap['DEX_amountIn'] = cex_total_sum_out
                best_swap['DEX_amountOut'] = greedy_dex_sum_out
                best_swap['profit'] = profit
                best_swap['CEX_end_price'] = level_price
                continue
            # ------ Greedy TEST End ------

            self.logger.info(f"Greedy test is failed. Probing through orderbook... ")
            is_broken_loop = False

            # ------ Probe TEST Start ------
            for i in range(1, 11):
                what_if_cex_sum_out = cex_total_sum_out + level_amount * (i / 10)
                what_if_cex_sum_in = cex_total_sum_in + level_amount * (i / 10) * level_price

                probe_delta_amount = what_if_cex_sum_out * (1 - config.SWAPPER_FEE) * 10 ** base_decimals  # Adjusting amount in
                result_SmartRouter = smart_router.ExactSwap(base_mint=base_mint,
                                                            quote_mint=DEX_QUOTE,
                                                            delta_amount=probe_delta_amount)

                dex_sum_out = result_SmartRouter['result'] / 10 ** quote_decimals  # Normalizing amount

                if not result_SmartRouter['success']:
                    is_broken_loop = True
                    self.logger.warning(
                        f"  [Probe Break] SmartRouter failed to find a path for {what_if_cex_sum_out} {base_mint}. Stopping probe.\n"
                        f"SmartRouter result: {result_SmartRouter}"
                    )
                    break

                if dex_sum_out - what_if_cex_sum_in < profit:
                    is_broken_loop = True
                    self.logger.info(
                        f"  [Probe Break] Profit diminishing at probe {i}/10. "
                        f"(Current Profit: ${dex_sum_out - what_if_cex_sum_in} < Best Profit: ${profit}). Stopping probe."
                    )
                    break

                self.logger.info(
                    f"\n============= [ASK] Probe Step Success {i}/10 ==========\n"
                    f" CEX            : {cex}\n"
                    f" Pair           : {base_mint}/{quote_symbol}\n"
                    f" Order Level    : {order_number}\n"
                    f" Probe          : {i}/10\n"
                    f"----------------------------------------------------------\n"
                    f" CEX Trade Size : {what_if_cex_sum_out} {base_mint}\n"
                    f" CEX Cost       : ${what_if_cex_sum_in}\n"
                    f" DEX Revenue    : ${dex_sum_out}\n"
                    f"----------------------------------------------------------\n"
                    f" Probe Profit   : ${dex_sum_out - what_if_cex_sum_in}\n"
                    f" Previous Best  : ${profit}\n"
                    f" VERDICT        : New Best! Updating...\n"
                    f"=========================================================="
                )

                profit = dex_sum_out - what_if_cex_sum_in

                best_swap['CEX_amountIn'] = what_if_cex_sum_in
                best_swap['CEX_amountOut'] = what_if_cex_sum_out
                best_swap['DEX_amountIn'] = what_if_cex_sum_out
                best_swap['DEX_amountOut'] = dex_sum_out
                best_swap['profit'] = profit
                best_swap['CEX_end_price'] = level_price
            # ------ Probe TEST End ------

            if is_broken_loop:
                break

            cex_total_sum_out += level_amount
            cex_total_sum_in += level_amount * level_price

        self.logger.info(f"Total Time For Calculation: {time.time() - start_time}")

        self._finalizer(cex=cex,
                        mode='CEX->DEX',
                        base=base_symbol,
                        quote=quote_symbol,
                        base_address=base_mint,
                        quote_address=DEX_QUOTE,
                        order_number=order_number,
                        best_swap=best_swap)

    async def _probe_cex_bid(self, cex: str, base_mint: str, base_symbol: str, quote_symbol: str,
                             smart_router: SmartRouter, base_decimals: int, quote_decimals: int):
        self.logger.info('_' * 50)
        self.logger.info(
            f'Probe CEX-BID for CEX: {cex} network:{self.network}, dex:{self.dex}, target_token:{base_mint}, base_token:{quote_symbol}')
        start_time = time.time()

        orderbook = await get_exchange_bids(exchange=cex, symbol=f'{base_symbol}{quote_symbol}')
        cex_total_sum_in = 0  # some token base in
        cex_total_sum_out = 0  # USDC or USDT out
        profit = 0
        order_number = 0
        best_swap = {
            'CEX_amountIn': 0,
            'CEX_amountOut': 0,
            'DEX_amountIn': 0,
            'DEX_amountOut': 0,
            'profit': 0,
            'CEX_start_price': float(orderbook[0][0]),
            'CEX_end_price': 0,
        }

        for order in orderbook:
            level_price = float(order[0])
            level_amount = float(order[1])
            order_number += 1
            self.logger.info(f'Order number: {order_number}, level_price: {level_price}, level_amount: {level_amount}')

            # ------ Greedy TEST Start ------
            # Adjusted delta amount, Human -> Atomic
            greedy_delta_amount = (cex_total_sum_in + level_amount) * 10 ** base_decimals
            greedy_result_SmartRouter = smart_router.ExactSwap(base_mint=base_mint,
                                                               quote_mint=DEX_QUOTE,
                                                               delta_amount=greedy_delta_amount,
                                                               amount_specified_is_input=False)

            self.logger.info(f'Greedy SmartRouter result: {greedy_result_SmartRouter}')

            # Normalizing the amount that we need to give to DEX aggregator (in our case it is Jupiter)
            # to get greedy_delta_amount, Atomic -> Human
            greedy_dex_sum_in = greedy_result_SmartRouter['result'] / (1-config.SWAPPER_FEE) / 10 ** quote_decimals
            greedy_profit = cex_total_sum_out + level_amount * level_price - greedy_dex_sum_in

            if greedy_result_SmartRouter['success'] and greedy_profit > profit:
                cex_total_sum_in += level_amount
                cex_total_sum_out += level_amount * level_price

                self.logger.info(
                    f"\n============---- [BID] Greedy Step Success ----============\n"
                    f" CEX            : {cex}\n"
                    f" Pair           : {base_mint}/{quote_symbol}\n"
                    f" Order Level    : {order_number} (Consumed full level)\n"
                    f"----------------------------------------------------------\n"
                    f" CEX Revenue    : {cex_total_sum_out} {quote_symbol}\n"
                    f" CEX Trade Size : {cex_total_sum_in} {base_mint}\n"
                    f" DEX Cost       : {greedy_dex_sum_in} {quote_symbol}\n"
                    f"----------------------------------------------------------\n"
                    f" Greedy Profit  : ${greedy_profit}\n"
                    f" Previous Best  : ${profit}\n"
                    f" VERDICT        : New Best! Skipping detailed probe.\n"
                    f"=========================================================="
                )
                profit = greedy_profit
                best_swap['CEX_amountIn'] = cex_total_sum_in
                best_swap['CEX_amountOut'] = cex_total_sum_out
                best_swap['DEX_amountIn'] = greedy_dex_sum_in
                best_swap['DEX_amountOut'] = cex_total_sum_in
                best_swap['profit'] = profit
                best_swap['CEX_end_price'] = level_price
                continue
            # ------ Greedy TEST End ------

            self.logger.info(f"Greedy test is failed. Probing through orderbook... ")
            is_broken_loop = False

            # ------ Probe TEST Start ------
            for i in range(1, 11):
                what_if_cex_sum_in = cex_total_sum_in + level_amount * (i / 10)
                what_if_cex_sum_out = cex_total_sum_out + (level_amount * (i / 10) * level_price)

                probe_delta_amount = what_if_cex_sum_in * 10 ** base_decimals  # Adjusted delta amount
                result_SmartRouter = smart_router.ExactSwap(base_mint=base_mint,
                                                            quote_mint=DEX_QUOTE,
                                                            delta_amount=probe_delta_amount,
                                                            amount_specified_is_input=False)

                # Normalizing the amount that we need to give to DEX aggregator (in our case it is Jupiter)
                # to get probe_delta_amount
                dex_sum_in = result_SmartRouter['result'] / (1 - config.SWAPPER_FEE) / 10 ** quote_decimals

                if not result_SmartRouter['success']:
                    is_broken_loop = True
                    self.logger.warning(
                        f"[Probe Break] SmartRouter failed to find a path for {what_if_cex_sum_in} {base_mint}. Stopping probe.\n"
                        f"SmartRouter result: {result_SmartRouter}")
                    break

                if what_if_cex_sum_out - dex_sum_in < profit:
                    is_broken_loop = True
                    self.logger.info(
                        f"  [Probe Break] Profit diminishing at probe {i}/10. "
                        f"(Current Profit: ${what_if_cex_sum_out - dex_sum_in} < Best Profit: ${profit}). Stopping probe."
                    )
                    break

                self.logger.info(
                    f"\n============= [BID] Probe Step Success {i}/10 ==========\n"
                    f" CEX            : {cex}\n"
                    f" Pair           : {base_mint}/{quote_symbol}\n"
                    f" Order Level    : {order_number}\n"
                    f" Probe          : {i}/10\n"
                    f"----------------------------------------------------------\n"
                    f" CEX Revenue    : {what_if_cex_sum_out} {quote_symbol}\n"
                    f" CEX Trade Size : {what_if_cex_sum_in} {base_mint}\n"
                    f" DEX Cost       : {dex_sum_in} {quote_symbol}\n"
                    f"----------------------------------------------------------\n"
                    f" Probe Profit   : ${what_if_cex_sum_out - dex_sum_in}\n"
                    f" Previous Best  : ${profit}\n"
                    f" VERDICT        : New Best! Updating...\n"
                    f"=========================================================="
                )

                profit = what_if_cex_sum_out - dex_sum_in
                best_swap['CEX_amountIn'] = what_if_cex_sum_in
                best_swap['CEX_amountOut'] = what_if_cex_sum_out
                best_swap['DEX_amountIn'] = dex_sum_in
                best_swap['DEX_amountOut'] = what_if_cex_sum_in
                best_swap['profit'] = profit
                best_swap['CEX_end_price'] = level_price
            # ------ Probe TEST End ------

            if is_broken_loop:
                break

            cex_total_sum_in += level_amount
            cex_total_sum_out += level_amount * level_price

        self.logger.info(f"Total Time For Calculation: {time.time() - start_time}")

        self._finalizer(cex=cex,
                        mode='DEX->CEX',
                        base=base_symbol,
                        quote=quote_symbol,
                        base_address=base_mint,
                        quote_address=DEX_QUOTE,
                        best_swap=best_swap,
                        order_number=order_number)

    def _finalizer(self, cex, mode, base, quote, base_address, quote_address, best_swap, order_number):
        try:
            if best_swap.get('profit') < config.MINIMAL_PROFIT:
                return


            signal_payload = config.SignalFormat(
                dex=self.dex,
                network=self.network,
                cex=cex,
                mode=mode,
                token_pair=f"{base}{quote}",
                profit=best_swap['profit'],
                target_token=base,
                target_address=base_address,
                base_address=quote_address,
                base_token=quote,
                CEX_amountIn=best_swap['CEX_amountIn'],
                CEX_amountOut=best_swap['CEX_amountOut'],
                DEX_amountIn=best_swap['DEX_amountIn'],
                DEX_amountOut=best_swap['DEX_amountOut'],
                order_number=order_number,
                CEX_start_price=best_swap['CEX_start_price'],
                CEX_end_price=best_swap['CEX_end_price'],
            )

            self.logger.info(f"\n============---- [{cex} {mode} {base}/{quote}] FINAL ----============\n"
                             f'Signal: {signal_payload.model_dump()}\n')
            self.logger.info('_' * 50)

            signal_dict = signal_payload.model_dump()
            self.r.xadd(
                config.SIGNAL_STREAM_REDIS_KEY,
                {'signal': json.dumps(signal_dict)}
            )
        except Exception as e:
            self.logger.warning(f"Finalizer failed. Error: {e}")