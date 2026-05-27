import redis
import json
import networkx as nx
import pydantic
import multiprocessing
import time
import logging
from decimal import Decimal
from typing import Literal
import math
import signal

####################################
from src.settings import config
from src.settings.bases import Bases, SecondBases, ExcludeBases, AMOUNT_PROBE, SUPPORTED_QUOTES
from src.settings.config import Network
from src.logger_handler.logger import get_logger, setup_logger
from src.engine.osr.math_smart_router import MathSmartRouter
from src.settings.graceful_shut_down import TerminateSignal, sigterm_handler
from src.engine.osr.osr_helper import get_network_active_metadata, get_network_active_state, create_graph
####################################

class OnlineSmartRouterEngineV1:
    """
    This version provides the top 40 (and less) best routes for any token pair by brute forcing through unfiltered routes.
    """
    MIN_CANDIDATES_LENGTH_REQUIREMENTS = 10
    LEVEL_DEPTH = 3

    def __init__(self, logger: logging.Logger, math_smart_router: MathSmartRouter, network: Network):
        self.logger = logger
        self.math_smart_router = math_smart_router
        self.network = network


    # Filter candidates by brute force
    def _filter_candidates_v1(
            self,
            unfiltered_candidates: list[list[str]],
            state: dict,
            metadata: dict,
            mint_in: str,
            mint_out: str
    ) -> list[list[str]]:

        if len(unfiltered_candidates) <= self.MIN_CANDIDATES_LENGTH_REQUIREMENTS:
            return unfiltered_candidates

        best_candidates = []

        sample_pool = unfiltered_candidates[0][0]
        pool_meta = metadata.get(sample_pool)

        if pool_meta:
            if pool_meta.get('mint0') == mint_in:
                decimals = pool_meta['decimals0']
            elif pool_meta.get('mint1') == mint_in:
                decimals = pool_meta['decimals1']
            else:
                raise Exception(f"Mint {mint_in} not found in pool {sample_pool}")
        else:
            raise Exception(f"Pool {sample_pool} not found in metadata")

        for human_amount in AMOUNT_PROBE:
            atomic_amount = human_amount * (Decimal(10) ** decimals)

            current_probe_candidates = {}

            for i, candidate in enumerate(unfiltered_candidates):
                swap_result = self.math_smart_router.smart_swap(
                    route=candidate,
                    metadata=metadata,
                    state=state,
                    delta_amount=atomic_amount,
                    base_mint=mint_in,
                    quote_mint=mint_out,
                    amount_specified_is_input=True
                )

                if swap_result['is_success'] and swap_result['result'] > Decimal(0):
                    current_probe_candidates[i] = swap_result['result']
                elif not swap_result['is_success']:
                    self.logger.warning(f"Swap failed for {candidate}. Result: {swap_result}")

            sorted_results = sorted(
                current_probe_candidates.items(),
                key=lambda x: x[1],
                reverse=True
            )

            level_count = 0
            for index, amount_out in sorted_results:
                if level_count >= self.LEVEL_DEPTH: break

                candidate_route = unfiltered_candidates[index]
                if candidate_route not in best_candidates:
                    best_candidates.append(candidate_route)
                level_count += 1

        if not best_candidates:
            self.logger.warning(f"Couldn't filter pools for {mint_in}/{mint_out} (candidates: {unfiltered_candidates}). Returning empty list.")
            return []

        return best_candidates


    # Get candidates whose intermediate tokens are in Bases
    @staticmethod
    def _get_candidates_path(
            all_paths,
            bases_addresses
    ) -> list:
        filtered_paths = []

        for path in all_paths:
            intermediate_tokens = path[1:-1]
            if all(mint in bases_addresses for mint in intermediate_tokens):
                filtered_paths.append(path)

        return filtered_paths


    # Find candidates for a given pair token_in/token_out
    def _find_candidates_for_pair_v1(
            self,
            G: nx.Graph,
            token_in: str,
            token_out: str
    ) -> list[list[str]]:
        all_paths = list(nx.all_simple_paths(G, token_in, token_out, cutoff=3))
        if not all_paths:
            self.logger.warning(f"No paths found between {token_in} and {token_out}")
            return []

        filtered_paths = self._get_candidates_path(all_paths, Bases.get(self.network))

        if not filtered_paths:
            filtered_paths = self._get_candidates_path(all_paths, SecondBases.get(self.network))

        if not filtered_paths:
            self.logger.warning(f"Paths between {token_in} and {token_out} don't contain any of the Bases. Returning empty list.")
            return []

        candidates = []
        for path in filtered_paths:
            pool_paths = [[]]

            for m1, m2 in zip(path, path[1:]):
                edge_pools: list = G[m1][m2]['pools']
                new_pool_path = []
                for partial in pool_paths:
                    for pool in edge_pools:
                        new_pool_path.append(partial + [pool])
                pool_paths = new_pool_path

            candidates.extend(pool_paths)

        return candidates

    def _get_all_candidates_v1(
            self,
            G: nx.Graph,
            target_bases: list[str],
            quotes: list[str]
    ) -> dict:
        all_paths = {}

        for quote in quotes:
            for base in target_bases:
                if quote == base:
                    continue
                elif base in ExcludeBases.get(self.network):
                    continue

                candidates = self._find_candidates_for_pair_v1(G, base, quote)
                all_paths[f"{base}/{quote}"] = candidates

        return all_paths

    def get_the_best_candidates(
            self,
            G: nx.Graph,
            target_bases: list[str],
            quotes: list,
            state: dict,
            metadata: dict
    ) -> dict[str, list[list[str]]]:
        all_candidates = self._get_all_candidates_v1(G, target_bases, quotes)
        best_candidates = {}

        for pair, candidates in all_candidates.items():
            try:
                mint_in, mint_out = pair.split('/')
                best_candidates[pair] = self._filter_candidates_v1(unfiltered_candidates=candidates,
                                                                    state=state,
                                                                    metadata=metadata,
                                                                    mint_in=mint_in,
                                                                    mint_out=mint_out)
            except Exception as e:
                self.logger.warning(f"Filter failed for {pair}. Exception: {e}")
        return best_candidates


class OnlineSmartRouterConfigScheme(pydantic.BaseModel):
    network: Network
    worker_number: int = 25
    Graph_update_time: int = 60
    version: Literal['v1'] = 'v1'
    quote: dict[str, list] = pydantic.Field(default_factory=lambda: SUPPORTED_QUOTES)


class OnlineSmartRouter:
    Engine = {
        'v1': OnlineSmartRouterEngineV1
    }

    def __init__(self, conf: OnlineSmartRouterConfigScheme):
        self.conf = conf

        self.network = conf.network

        self.quotes = conf.quote[self.network]

        logger_name = f"osr.{self.network}.{conf.version}"
        log_file = config.OSR_LOG_FILES[self.network]


        setup_logger(logger_name=logger_name, log_file=log_file)
        self.logger = get_logger(logger_name)

        self.r = redis.Redis(port=config.REDIS_PORT, host=config.REDIS_HOST, decode_responses=True)

        math_smart_router = MathSmartRouter(logger=self.logger)
        self.engine = OnlineSmartRouter.Engine[conf.version](
            logger=self.logger,
            math_smart_router=math_smart_router,
            network=conf.network
        )

        self.queue = multiprocessing.JoinableQueue()
        self.workers = {}
        self.logger.info(f"OnlineSmartRouter initialized. Configuration: {conf.model_dump()}")

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['r']
        del state['logger']
        del state['engine']
        del state['workers']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.r = redis.Redis(port=config.REDIS_PORT, host=config.REDIS_HOST, decode_responses=True)

        logger_name = f"osr.{self.network}.{self.conf.version}"
        log_file = config.OSR_LOG_FILES[self.network]

        setup_logger(logger_name=logger_name, log_file=log_file)
        self.logger = get_logger(logger_name)

        math_smart_router = MathSmartRouter(logger=self.logger)
        self.engine = OnlineSmartRouter.Engine[state['conf'].version](
            logger=self.logger,
            math_smart_router=math_smart_router,
            network=state['conf'].network
        )

    @staticmethod
    def save_candidates_to_redis(candidates: dict, redis_connection: redis.Redis):
        """
            candidates format:
            {
                "0x…/0x…": [ ...list of routes... ],
                "base58/base58": [ ...list of routes... ]
            }
        """

        if not candidates: return

        current_time = str(int(time.time()))
        mapped_candidates = {}
        for quote, candidates_list in candidates.items():
            payload = {
                "ts": current_time,
                "routes": candidates_list
            }
            mapped_candidates[quote] = json.dumps(payload)

        if mapped_candidates:
            redis_connection.hset(config.REDIS_KEY_COLD_PATH, mapping=mapped_candidates)

    def save_dex_mints(self, mints: list, redis_connection: redis.Redis):
        if not mints: return

        redis_connection.set(config.REDIS_DEX_MINTS % (self.network, ), json.dumps({"tokens": mints}))

    def _worker(self):
        while True:
            try:
                target_bases = self.queue.get()
                self.logger.info(f"Worker {multiprocessing.current_process().name} started for {target_bases}")

                metadata = get_network_active_metadata(
                    redis_connection=self.r,
                    network=self.network,
                    logger=self.logger
                )
                state = get_network_active_state(
                    redis_connection=self.r,
                    network=self.network,
                    logger=self.logger
                )

                G = create_graph(metadata, state)
                candidates = self.engine.get_the_best_candidates(G=G,
                                                                 target_bases=target_bases,
                                                                 quotes=self.conf.quote[self.conf.network],
                                                                 state=state,
                                                                 metadata=metadata)

                self.save_candidates_to_redis(candidates, self.r)
                self.logger.info(f"Worker {multiprocessing.current_process().name} finished task.")

            except Exception as e:
                self.logger.error(f"In worker {multiprocessing.current_process().name} something gone wrong. Exception: {e}")

            self.queue.task_done()

    def _init_workers(self) -> bool:
        number_of_started_workers = 0
        worker_index = 0

        brute_stop = 0
        MAX_ATTEMPTS = self.conf.worker_number + 10

        while number_of_started_workers < self.conf.worker_number:
            try:
                w_name = f'OSR_Worker_{worker_index}'

                worker = multiprocessing.Process(target=self._worker, name=w_name, daemon=True)
                worker.start()
                self.logger.info(f"Started {w_name} (PID: {worker.pid})")

                self.workers[w_name] = worker

                number_of_started_workers += 1
                worker_index += 1

            except Exception as e:
                self.logger.error(f"Worker {worker_index} initialization failed. Exception: {e}")
                time.sleep(1)

            brute_stop += 1
            if brute_stop >= MAX_ATTEMPTS:
                self.logger.critical(f"Critical Fail: Could only start {number_of_started_workers}/{self.conf.worker_number} workers.")
                return False

        return True

    def _shutdown_workers(self):
        for name, worker in self.workers.items():
            if worker.is_alive():
                worker.terminate()

        for name, worker in self.workers.items():
            worker.join(timeout=10)
            if worker.is_alive():
                worker.kill()
                worker.join()

        self.logger.info("All workers stopped.")

    def _restart_dead_worker(self, w_name) -> bool:
        try:
            worker = multiprocessing.Process(target=self._worker, name=w_name, daemon=True)
            worker.start()
            self.logger.info(f"Restarted {w_name} (PID: {worker.pid})")

            self.workers[w_name] = worker
        except Exception as e:
            self.logger.error(f"Worker {w_name} restart failed. Exception: {e}")
            return False

        return True

    def _check_workers_health(self):
        for w_name, worker in list(self.workers.items()):
            if not worker.is_alive():
                self.logger.warning(f"{w_name} is dead. Restarting...")
                worker.join()
                self._restart_dead_worker(w_name)

    def _break_tasks_in_chunks(self, bases: list):
        num_symbols = len(bases)
        chunk_size = math.ceil(num_symbols / self.conf.worker_number)
        if chunk_size == 0:
            return

        for i in range(0, num_symbols, chunk_size):
            yield bases[i:i + chunk_size]


    def start(self):
        signal.signal(signal.SIGTERM, sigterm_handler)

        are_workers_initialized = self._init_workers()
        if not are_workers_initialized:
            self.logger.critical("Critical Fail: Could not start any workers.")
            raise Exception("Critical Fail: Could not start any workers.")

        metadata = get_network_active_metadata(
            redis_connection=self.r,
            network=self.network,
            logger=self.logger
        )
        state = get_network_active_state(
            redis_connection=self.r,
            network=self.network,
            logger=self.logger
        )

        G = create_graph(metadata, state)
        last_graph_update = time.time()
        bases = list(G.nodes)
        self.save_dex_mints(bases, self.r)

        while True:
            try:
                if time.time() - last_graph_update >= self.conf.Graph_update_time:
                    metadata = get_network_active_metadata(
                        redis_connection=self.r,
                        network=self.network,
                        logger=self.logger
                    )

                    state = get_network_active_state(
                        redis_connection=self.r,
                        network=self.network,
                        logger=self.logger
                    )

                    G = create_graph(metadata, state)
                    last_graph_update = time.time()
                    bases = list(G.nodes)
                    self.save_dex_mints(bases, self.r)

                if not bases:
                    self.logger.warning("No bases found. Sleeping.")
                    time.sleep(5)
                    continue

                self._check_workers_health()

                chunks = list(self._break_tasks_in_chunks(bases))

                start_time = time.time()
                for chunk in chunks:
                    self.queue.put(chunk)

                self.queue.join()
                self.logger.info(f"All tasks is done. Time elapsed: {time.time() - start_time} seconds.")

            except (KeyboardInterrupt, TerminateSignal):
                self.logger.info("Shutdown signal received. Stopping workers...")
                self._shutdown_workers()
                break

            except Exception as e:
                self.logger.error(f"Supervisor Loop Error: {e}")
                time.sleep(5)