#!/usr/bin/python3
# encoding: utf-8
import argparse
from sanic import Sanic
from os import environ

# from core import serverdb
from core.logger import logger
from apps.auth.views import auth_bp
from tortoise.contrib.sanic import register_tortoise
from settings import settings
from core.extentions.exceptions import handle_404
from core.extentions.middlewares import check_content_negotiation, jsonapi_standard_response_header
from apps import app, auth_instance


app.config.update_config(settings)
auth_instance.setup(app)


# Install Apps
app.blueprint(auth_bp)

# Regist middleware & handler
app.register_middleware(check_content_negotiation, "request")
app.register_middleware(jsonapi_standard_response_header, "response")
# app.error_handler.add(Exception, handle_404)

# 模板文件路由
app.static('/', './static/index.html', name='index')
app.static('/static', './static/static', name='pc_static')
app.static('/h5', './static/h5/index.html', name='h5')
app.static('/h5/static', './static/h5/static', name='static')
app.static('/favicon.ico', './static/favicon.ico', name='fav')


register_tortoise(
    app,
    db_url=f"asyncpg://{environ.get('DB_USER')}:{environ.get('DB_PWD')}@{environ.get('DB_HOST')}:{environ.get('DB_PORT')}/{environ.get('DB_NAME')}",
    modules={"models": ["apps.auth"]},
    generate_schemas=True
)


# Command line parser options & setup default values
parser = argparse.ArgumentParser()
parser.add_argument(
    '--host', help='Setup host ip to listen up, default to 0.0.0.0', default='0.0.0.0')
parser.add_argument(
    '--port', help='Setup port to attach, default to 8093', default=8093)
parser.add_argument(
    '--workers', help='Setup workers to run, default to 1', type=int, default=2)
parser.add_argument('--debug', help='Enable or disable debugging',
                    default=True, action='store_true')
parser.add_argument('--accesslog', help='Enable or disable access log',
                    default=True, action='store_true')
args = parser.parse_args()


if __name__ == "__main__":
    app.run(
        host=args.host,
        port=args.port,
        workers=args.workers,
        debug=args.debug,
        access_log=args.accesslog
    )
