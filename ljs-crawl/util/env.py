import dotenv
import os

def LOAD_ENV():
    dotenv.load_dotenv(dotenv.find_dotenv())

def GET_ENV(key:str):
    return os.getenv(key)