""" Application config values hub """
from os import getenv


def get_env(env_name, default_val=None, conv_func=str):
    """ Get environment variable and convert it."""
    val = getenv(env_name, default_val)
    if val is not None:
        val = conv_func(val)
    return val


UPLOAD_DIR = get_env('UPLOAD_DIR', '/tmp/')
PROCESSOR_DIR = get_env('PROCESSOR_DIR', '/tmp/bugz/')
