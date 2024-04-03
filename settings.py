import os
import sys
import json
from os.path import join, dirname


program_root_path = os.path.dirname(os.path.realpath(sys.argv[0]))


class Settings(object):

    def __init__(self, filename='env.json'):
        envpath = join(program_root_path, filename)
        with open(envpath, 'r')as f:
            data = json.load(f)
        self.Data = data
        self.SECRET_KEY = "www.swissmic.cn/factory_cloud"
        self.AUTH_LOGIN_ENDPOINT = 'auth.login'
        self.AUTH_LOGIN_URL = "/"
        self.log_file_path = os.path.join(program_root_path, 'logs')


settings = Settings()
