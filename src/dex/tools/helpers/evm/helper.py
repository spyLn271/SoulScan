import redis
import json
import logging
import time

####################################
from src.dex.evm.type_dict import MetadataDict
from src.settings.config import (
    Network,
    DEX,
    Version,
    REDIS_METADATA_KEY,
)
####################################


def get_metadata(
        network: Network,
        dex: DEX,
        version: Version,
        redis_con: redis.Redis,
        logger: logging.Logger
) -> dict[str, MetadataDict]:
    logger.info(f"Fetching metadata for {network} {dex} {version}...")

    metadata: dict[str, MetadataDict] = {}

    while True:
        raw_metadata = redis_con.get(REDIS_METADATA_KEY % (network, dex, version))

        if not isinstance(raw_metadata, str):
            logger.error(f"Metadata for {network} {dex} {version} not found.")
            time.sleep(5)
            continue

        metadata = json.loads(raw_metadata)
        break

    logger.info(f"Metadata for {network} {dex} {version} fetched: {len(metadata)} pools")

    return metadata