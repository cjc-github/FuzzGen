import logging
from datetime import datetime

def setup_logger():
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_name = f"log/log_{current_time}.log"

    logging.basicConfig(
        filename=log_file_name,
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        encoding='utf-8'
    )

    return logging.getLogger()

logger = setup_logger()