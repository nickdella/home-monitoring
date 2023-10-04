import logging


def get(module: str) -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        force=True,
    )
    return logging.getLogger(module)
