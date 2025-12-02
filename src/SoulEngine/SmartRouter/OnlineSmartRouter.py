import redis
import json
import networkx as nx
import pydantic
import multiprocessing
import time
import os
import logging
from decimal import Decimal
from typing import Literal
import math

####################################
from src.Config import config, Bases
from src.LoggerHandler.logger import get_logger, setup_logger
from src.SoulEngine.SmartRouter.MathSmartRouter import MathSmartRouter
####################################


def create_graph(metadata: dict, state: dict) -> nx.Graph:
    G = nx.Graph()
    for pool, data in state.items():
        if not pool in metadata: continue

        mint0 = metadata.get(pool).get('mint0')
        mint1 = metadata.get(pool).get('mint1')
        if G.has_edge(mint0, mint1):
            G[mint0][mint1]['pools'].append(pool)
        else:
            G.add_edge(mint0, mint1, pools=[pool])

    return G

def get_active_metadata(redis_connection: redis.Redis) -> dict:
    all_metadata = {}
    for active_market in config.ACTIVE_MARKETS:
        market, version = config.MARKETS.get(active_market).values()
        metadata = json.loads(redis_connection.get(config.REDIS_METADATA_KEY % (market, version)))
        all_metadata |= metadata

    return all_metadata

def get_active_state(redis_connection: redis.Redis) -> dict:
    all_state = {}
    for active_market in config.ACTIVE_MARKETS:
        market, version = config.MARKETS.get(active_market).values()
        state = json.loads(redis_connection.get(config.POOLS_CURRENT_STATE_DICT_REDIS_KEY % (market, version)))
        all_state |= state

    return all_state

class OnlineSmartRouterEngineV1:
    """
    This version provides the top 40 (and less) best routes for any token pair by brute forcing through unfiltered routes.
    """
    def __init__(self, logger: logging.Logger, math_smart_router: MathSmartRouter):
        self.logger = logger
        self.math_smart_router = math_smart_router

    def filter_candidates_v1(self, unfiltered_candidates: list[list[str]], state: dict, metadata: dict, mint_in: str,
                             mint_out: str) -> list[list[str]]:

        if len(unfiltered_candidates) <= 10:
            return unfiltered_candidates

        best_candidates = []

        decimals = 6
        sample_pool = unfiltered_candidates[0][0]
        pool_meta = metadata.get(sample_pool)

        if pool_meta:
            if pool_meta.get('mint0') == mint_in:
                decimals = pool_meta['decimals0']
            elif pool_meta.get('mint1') == mint_in:
                decimals = pool_meta['decimals1']
            else:
                raise Exception(f"Mint {mint_in} not found in pool {sample_pool}")

        for human_amount in Bases.AMOUNT_PROBE:
            atomic_amount = human_amount * (Decimal(10) ** decimals)

            current_probe_candidates = {}

            for i, candidate in enumerate(unfiltered_candidates):
                swap_result = self.math_smart_router.smart_swap(
                    route=candidate,
                    metadata=metadata,
                    state=state,
                    delta_amount=atomic_amount,
                    mint_in=mint_in,
                    mint_out=mint_out,
                    amount_specified_is_input=True
                )

                if swap_result['is_success'] and swap_result['result'] > Decimal(0):
                    current_probe_candidates[i] = swap_result['result']

            sorted_results = sorted(
                current_probe_candidates.items(),
                key=lambda x: x[1],
                reverse=True
            )

            level_count = 0
            for index, amount_out in sorted_results:
                if level_count >= 3: break

                candidate_route = unfiltered_candidates[index]
                if candidate_route not in best_candidates:
                    best_candidates.append(candidate_route)
                level_count += 1

        if not best_candidates:
            self.logger.warning(f"Couldn't filter pools for {mint_in}/{mint_out} (candidates: {unfiltered_candidates}). Returning empty list.")
            return []

        return best_candidates

    @staticmethod
    def get_candidate_mint_path(all_paths, Bases_mint) -> list:
        filtered_paths = []

        for path in all_paths:
            intermediate_tokens = path[1:-1]
            if all(mint in Bases_mint for mint in intermediate_tokens):
                filtered_paths.append(path)

        return filtered_paths

    def find_candidates_v1(self, G: nx.Graph, token_in: str, token_out: str) -> list[list[str]]:
        all_paths = list(nx.all_simple_paths(G, token_in, token_out, cutoff=3))
        if not all_paths:
            self.logger.warning(f"No paths found between {token_in} and {token_out}")
            return []

        filtered_paths = self.get_candidate_mint_path(all_paths, Bases.Bases_mint)

        if not filtered_paths:
            filtered_paths = self.get_candidate_mint_path(all_paths, Bases.Second_Bases_mint)

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

    def get_all_candidates_v1(self, G: nx.Graph, target_bases: list[str], quotes: list) -> dict:
        all_paths = {}

        for quote in quotes:
            for base in target_bases:
                if quote == base:
                    continue
                elif base in Bases.exclude_bases:
                    continue

                candidates = self.find_candidates_v1(G, base, quote)
                all_paths[f"{base}/{quote}"] = candidates

        return all_paths

    @staticmethod
    def save_candidates_to_redis(candidates: dict, redis_connection: redis.Redis):
        """
            candidates format:
            {
                "SOL/USDC": [ ...list of routes... ],
                "RAY/USDT": [ ...list of routes... ]
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

    def get_the_best_candidates(self, G: nx.Graph, target_bases: list[str], quotes: list,
                                state: dict, metadata: dict) -> dict[str, list[list[str]]]:
        all_candidates = self.get_all_candidates_v1(G, target_bases, quotes)
        best_candidates = {}
        for quote, candidates in all_candidates.items():
            try:
                mint_in, mint_out = quote.split('/')
                best_candidates[quote] = self.filter_candidates_v1(unfiltered_candidates=candidates,
                                                                   state=state,
                                                                   metadata=metadata,
                                                                   mint_in=mint_in,
                                                                   mint_out=mint_out)
            except Exception as e:
                self.logger.warning(f"Filter failed for {quote}. Exception: {e}")
        return best_candidates


class OnlineSmartRouterConfigScheme(pydantic.BaseModel):
    logger_name: str = 'OnlineSmartRouter'
    log_file: str = 'OnlineSmartRouter.log'
    worker_number: int = 20
    Graph_update_time: int = 60 * 3
    version: Literal['v1'] = 'v1'
    quote: list[str] = pydantic.Field(default_factory=lambda: [
        'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
    ])
class OnlineSmartRouter:
    Engine = {
        'v1': OnlineSmartRouterEngineV1
    }

    def __init__(self, conf: OnlineSmartRouterConfigScheme):
        self.conf = conf
        logger_name = conf.logger_name
        log_file = conf.log_file
        setup_logger(logger_name=logger_name, log_file=os.path.join(config.LOG_MAIN_FOLDER, log_file))
        self.logger = get_logger(logger_name)
        self.r = redis.Redis(port=config.REDIS_PORT, host=config.REDIS_HOST, decode_responses=True)

        math_smart_router = MathSmartRouter(logger=self.logger)
        self.engine = OnlineSmartRouter.Engine[conf.version](logger=self.logger, math_smart_router=math_smart_router)

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
        logger_name = 'OSR_worker_%s' % multiprocessing.current_process().name
        log_file = 'OSR_worker_%s.log' % multiprocessing.current_process().name
        setup_logger(logger_name=logger_name, log_file=os.path.join(config.LOG_MAIN_FOLDER, log_file))
        self.logger = get_logger(logger_name)
        math_smart_router = MathSmartRouter(logger=self.logger)
        self.engine = OnlineSmartRouter.Engine[state['conf'].version](logger=self.logger, math_smart_router=math_smart_router)


    def worker(self):
        while True:
            try:
                target_bases = self.queue.get()
                self.logger.info(f"Worker {multiprocessing.current_process().name} started for {target_bases}")
                metadata = get_active_metadata(self.r)
                state = get_active_state(self.r)
                G = create_graph(metadata, state)
                candidates = self.engine.get_the_best_candidates(G=G,
                                                                 target_bases=target_bases,
                                                                 quotes=self.conf.quote,
                                                                 state=state,
                                                                 metadata=metadata)
                self.engine.save_candidates_to_redis(candidates, self.r)
                self.logger.info(f"Worker {multiprocessing.current_process().name} finished task.")

            except Exception as e:
                self.logger.error(f"In worker {multiprocessing.current_process().name} something gone wrong. Exception: {e}")

            self.queue.task_done()

    def init_workers(self) -> bool:
        number_of_started_workers = 0
        worker_index = 0

        brute_stop = 0
        MAX_ATTEMPTS = self.conf.worker_number + 10

        while number_of_started_workers < self.conf.worker_number:
            try:
                w_name = f'OSR_Worker_{worker_index}'

                worker = multiprocessing.Process(target=self.worker, name=w_name, daemon=True)
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

    def restart_dead_worker(self, w_name) -> bool:
        try:
            worker = multiprocessing.Process(target=self.worker, name=w_name, daemon=True)
            worker.start()
            self.logger.info(f"Restarted {w_name} (PID: {worker.pid})")

            self.workers[w_name] = worker
        except Exception as e:
            self.logger.error(f"Worker {w_name} restart failed. Exception: {e}")
            return False

        return True

    def check_workers_health(self):
        for w_name, worker in list(self.workers.items()):
            if not worker.is_alive():
                self.logger.warning(f"{w_name} is dead. Restarting...")
                worker.join()
                self.restart_dead_worker(w_name)

    def break_tasks_in_chunks(self, bases: list):
        num_symbols = len(bases)
        chunk_size = math.ceil(num_symbols / self.conf.worker_number)
        if chunk_size == 0:
            return

        for i in range(0, num_symbols, chunk_size):
            yield bases[i:i + chunk_size]


    def start(self):
        are_workers_initialized = self.init_workers()
        if not are_workers_initialized:
            self.logger.critical("Critical Fail: Could not start any workers.")
            raise Exception("Critical Fail: Could not start any workers.")

        metadata = get_active_metadata(self.r)
        state = get_active_state(self.r)
        G = create_graph(metadata, state)
        last_graph_update = time.time()
        bases = list(G.nodes)

        while True:
            try:
                if time.time() - last_graph_update >= self.conf.Graph_update_time:
                    metadata = get_active_metadata(self.r)
                    state = get_active_state(self.r)
                    G = create_graph(metadata, state)
                    last_graph_update = time.time()
                    bases = list(G.nodes)

                if not bases:
                    self.logger.warning("No bases found. Sleeping.")
                    time.sleep(5)
                    continue

                self.check_workers_health()

                chunks = list(self.break_tasks_in_chunks(bases))

                start_time = time.time()
                for chunk in chunks:
                    self.queue.put(chunk)

                self.queue.join()
                self.logger.info(f"All tasks is done. Time elapsed: {time.time() - start_time} seconds.")

            except Exception as e:
                self.logger.error(f"Supervisor Loop Error: {e}")
                time.sleep(5)