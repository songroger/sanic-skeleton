from http import HTTPStatus

from sanic.response import json
from core.helpers import jsonapi

DEFAULT_TYPE = 'application/json'


def jsonapi_standard_response_header(request, response):
    '''Adding custom content type to all responses

    Following JSON API standard, all response headers should
    has a content-type with value is application/vnd.api+json
    '''
    response.headers['Content-Type'] = DEFAULT_TYPE 


def check_content_negotiation(request):
    '''Checking current request header content negotiation

    All request should accept application/vnd.api+json or it will
    not allowed to continue process, and throw a http status code's 406

    For all requests that not using GET http method, should has 
    a content-type header parameter with value is application/vnd.api+json
    if not will throw a http status code's 415
    '''
    request.ctx.session = {}
    user_account = request.headers.get('user_account')
    content_type = request.headers.get('Content-Type')
    # print('user_account:', user_account, 'content-type:', content_type)
    if user_account is not None:
        if request.method == 'GET':
            pass
        else:
            if content_type == DEFAULT_TYPE:
                request.json['user_name'] = user_account
            else:
                request.form['user_name'] = [user_account]
