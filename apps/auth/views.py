from sanic import Blueprint, response
from sanic.response import json as sanicjson
from tortoise.functions import Count

from core.logger import logger
from core import redis_conn
from core.base import baseResponse
from .models import FactoryUser
from apps import auth_instance as auth
from sanic_auth import User


auth_bp = Blueprint('auth', url_prefix='/auth')


@auth_bp.route('/test', methods=['GET', 'POST'])
@auth.login_required
async def test(request):
    logger.info("test")
    redis_conn.setex("test_key", 5, 'value')

    return baseResponse(200, "success", {})


@auth_bp.route('/login', methods=['GET', 'POST'])
async def login(request):
    payload = request.json
    data_dict = {
        'result': False
    }

    user = await FactoryUser.filter(user_name=payload['user_account']).first()
    if not user:
        response_dict = baseResponse(200, "用户不存在", data_dict)

    if payload['user_password'] == user.user_password:
        data_dict["result"] = True
        auth_user = User(id=user.id, name=user.user_name)
        auth.login_user(request, auth_user)
        response_dict = baseResponse(200, "验证成功", data_dict)
    else:
        response_dict = baseResponse(200, "密码错误", data_dict)

    return sanicjson(response_dict)


@auth_bp.route('/logout')
@auth.login_required
async def logout(request):
    auth.logout_user(request)
    return response.redirect('/')
