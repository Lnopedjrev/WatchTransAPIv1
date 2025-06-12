import logging
import json
import logging.config
import atexit
import os
import sys


def resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(relative)


CONFIG_FILE = resource_path(os.path.join('logapp', 'logConfig.json'))


def setup_logger():
    try:
        setup_Ologger()
        queue_handler = logging.getHandlerByName("queue_handler")
        if queue_handler is not None:
            queue_handler.listener.start()
            atexit.register(queue_handler.listener.stop)
    except Exception as e:
        print(f"Error configuring logging: {e}")


def setup_Ologger():
    try:
        with open(CONFIG_FILE) as f_in:
            config = json.load(f_in)
            logging.config.dictConfig(config)
    except Exception as e:
        print(f"Error configuring logging: {e}")