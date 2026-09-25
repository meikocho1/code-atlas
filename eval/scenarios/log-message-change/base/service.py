import logging

logger = logging.getLogger(__name__)


def process(order_id):
    logger.info("Processing order %s", order_id)
    return True
