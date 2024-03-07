import os
import sys
from dotenv import load_dotenv
from os import environ
from os.path import join, dirname


program_root_path = os.path.dirname(os.path.realpath(sys.argv[0]))


class Settings(object):

    def __init__(self, filename='.env'):
        envpath = join(dirname(__file__), filename)
        load_dotenv(envpath)

        self.SECRET_KEY = environ.get('SECRET_KEY')
        self.AUTH_LOGIN_ENDPOINT = 'auth.login'
        self.AUTH_LOGIN_URL = "/"
        self.log_file_path = os.path.join(program_root_path, 'logs')


settings = Settings()
