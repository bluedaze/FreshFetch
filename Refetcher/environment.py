import os
from os.path import abspath, dirname
from dotenv import dotenv_values

def get_env():
    cwd = os.getcwd()
    working_path = abspath(__file__)
    os.chdir(dirname(working_path))
    config = dotenv_values('.env')
    os.chdir(cwd)
    return config