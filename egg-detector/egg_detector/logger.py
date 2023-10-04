import logging


def get(module):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        force=True,
    )
    return logging.getLogger(module)
