from sanic import Blueprint, response
from sanic.response import json as sanicjson
from tortoise.functions import Count

from core.logger import logger
from core.utils_init import redis_conn
from core.base import ResponseCode, baseResponse
from .models import FactoryUser, SisUser
from apps import auth_instance as auth
from sanic_auth import User
from .utils import loginAuth
from sanic.views import HTTPMethodView


auth_bp = Blueprint('auth', url_prefix='/auth')


@auth_bp.route('/test', methods=['GET', 'POST'])
@auth.login_required
async def test(request):
    logger.info("test")
    redis_conn.setex("test_key", 5, 'value')

    return baseResponse(ResponseCode.OK, "success", {})


@auth_bp.route('/logout')
@auth.login_required
async def logout(request):
    auth.logout_user(request)
    return response.redirect('/')


@auth_bp.route('/login', methods=['POST', 'GET'])
async def login(request, *args, **kwargs):
    payload = request.json

    user_name = payload.get('user_name')
    password = payload.get("user_passwd")

    s, res = await loginAuth(user_name, password)
    if not s:
        return baseResponse(ResponseCode.FAIL, res)

    kwargs.update(user=res)
    return baseResponse(ResponseCode.OK, "success", data=kwargs)


class SisUserManager(HTTPMethodView):
    async def get(self, request):
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        users = await SisUser.all().select_related('user_group'
            ).order_by('-id').offset((page - 1) * per_page).limit(per_page)
        total = await SisUser.all().count()

        data = {
            'user': [s.to_dict() for s in users],
            'total': total,
            'page': page,
            'per_page': per_page
        }

        return baseResponse(ResponseCode.OK, "success", data)

    async def post(self, request):
        args = request.json

        _exist = await SisUser.filter(user_name=args.get("user_name")).exists()
        if _exist and not args.get("id"):
            return baseResponse(ResponseCode.FAIL, "用户已存在", {})

        _ = await SisUser().create_or_update(args)

        return baseResponse(ResponseCode.OK, "success", {})

    async def delete(self, request):
        args = request.json
        sid = args.get("id")

        _ = await SisUser.filter(id=sid).delete()

        return baseResponse(ResponseCode.OK, "success", {})
