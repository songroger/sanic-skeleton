import json, os
import pandas as pd
import psycopg2
from sanic import Blueprint, response
from sanic.response import json as sanicjson
from common import serverdb
from common.async_db_common_func import authorized, authCheck, saveToken, \
    licenceCheck, AuthProtect
from .utils import OAuth
from common.common_config import postgres_data, userGroup_zh_2_en, export_file_path
from common.base_func import utc_time_conversion, basic_return
from common.constant import BasicReturnCode

user_bp = Blueprint('user', url_prefix='/user')


# 激活licence
@user_bp.route('/addLicence', methods=['POST', 'GET'])
async def addLicence(request):
    payload = request.json
    if not payload:
        return sanicjson({"result": 0, "msg": "Parameters of the abnormal!"})
    licence = payload.get('licence')
    factory_code = payload.get('factory_code')
    await OAuth.checkFactoryExist(factory_code)
    auth_res = await authCheck(licence)
    if auth_res:
        remainDays, licenceTime = auth_res[1], auth_res[2]
        await saveToken(licence, factory_code)
        if remainDays >= 365 * 10:
            active_flag = -1
        else:
            active_flag = 0
        data = {"remainDays": remainDays, "licenceTime": licenceTime,"active_flag":active_flag}
        return sanicjson({"result": 1, "msg": data})
    else:
        return sanicjson({"result": 0, "msg": "Licence Auth Error!"})


# 登录
@user_bp.route('/login', methods=['POST', 'GET'])
@licenceCheck
async def login(request, *args, **kwargs):
    payload = request.json
    if not payload:
        return sanicjson(basic_return(BasicReturnCode.RESPONSE_FAIL, code=BasicReturnCode.PARAMS_LOST))
    user_name = payload.get('user_name')
    password = payload.get("user_passwd")
    language = payload.get("user_language")
    token = await OAuth.loginAuth(user_name, password)
    kwargs.update(token=token)
    return sanicjson(
        basic_return(result=BasicReturnCode.RESPONSE_SUCCESS, code=BasicReturnCode.USER_LOGIN_SUCCESS,
                     language=language, data=kwargs))


@user_bp.route('/refreshToken', methods=['POST', 'GET'])
@AuthProtect
async def refreshToken(request):
    payload = request.json
    language = payload.get("user_language")
    token = await OAuth.signatureToken(request, payload)
    return sanicjson(
        basic_return(result=BasicReturnCode.RESPONSE_SUCCESS, code=BasicReturnCode.USER_TOKEN_SIGNATURE_SUCCESS,
                     language=language, data=token))


@user_bp.route('/userInfo', methods=['POST', 'GET'])
@AuthProtect
async def userInfo(request):
    payload = request.json
    language = payload.get("user_language")
    user_id = payload.get("user_id")
    factory_id = payload.get("factory_id")
    user_info = await OAuth.getUserInfo(user_id, factory_id)
    return sanicjson(
        basic_return(result=BasicReturnCode.RESPONSE_SUCCESS, code=BasicReturnCode.GET_OK,
                     language=language, data=user_info))


# 权限组的信息展示
@user_bp.route('/userGroupList', methods=['GET', 'POST'])
@AuthProtect
async def userGroupList(request):
    '''
    :param request:
    :param user_name 用户名
    :param user_group_power 用户权限
    :return:
    '''
    payload = request.json
    if not payload:
        return sanicjson({"result": 0, "msg": "Parameters of the abnormal!"})
    user_group_power = payload.get('user_group_power')
    user_language = payload.get('user_language')
    query_interface_group_sql = "select * from sis_user_group where group_power>'%s'" % user_group_power
    query_res = await serverdb.querySearch(query_interface_group_sql)
    data = []
    if len(query_res) > 0:
        for i in query_res:
            item = dict(i).copy()
            if user_language != 'zh':
                item['group_name'] = userGroup_zh_2_en.get(item['group_name'])
            data.append(item)

    return sanicjson({'result': 1, 'data': data})


# 新增权限组的信息
@user_bp.route('/addUserGroupList', methods=['GET', 'POST'])
@AuthProtect
async def addUserGroupList(request):
    '''
    :param request:
    :param user_name 用户名
    :param user_group_power 用户权限
    :param group_name 分组名称
    :param group_power 分组权限
    :return:
    '''
    payload = request.json
    if not payload:
        return sanicjson({"result": 0, "msg": "Parameters of the abnormal!"})
    group_name = payload.get('group_name')
    group_power = payload.get('group_power')
    user_group_power = payload.get('user_group_power')
    # 检查新权限是否超出权限范围
    if group_power <= user_group_power:
        return sanicjson({'result': 0, 'msg': 'Insufficient permissions!'})
    # 检查权限组名称是否重复
    check_groupName_sql = "select * from sis_user_group where group_name='%s'" % group_name
    check_groupName_res = await serverdb.querySearch(check_groupName_sql)
    if len(check_groupName_res) > 0:
        return sanicjson({'result': 0, 'msg': 'groupName cannot be repeated!'})
    add_user_group_sql = "insert into sis_user_group(group_name,group_power) values('%s', '%s')" % (
        group_name, group_power)
    res = await serverdb.doSQL(add_user_group_sql)
    if res:
        return sanicjson({'result': 1})
    else:
        return sanicjson({'result': 0, 'msg': 'insert error'})


# 删除权限组的信息
@user_bp.route('/delUserGroupList', methods=['GET', 'POST'])
@AuthProtect
async def delUserGroupList(request):
    '''
    :param request:
    :param user_name 用户名
    :param user_group_power 用户权限
    :param group_id 分组id
    :return:
    '''
    payload = request.json
    if not payload:
        return sanicjson({"result": 0, "msg": "Parameters of the abnormal!"})
    group_id = payload.get('group_id')
    user_group_power = payload.get('user_group_power')
    # 检查权限是否超出用户权限范围
    sql_ = "select * from sis_user_group where id='%s'" % group_id
    res = await serverdb.querySearch(sql_)
    if len(res) == 0:
        return sanicjson({'result': 0, 'msg': 'permission group does not exist!'})
    else:
        group_power = res[0].get('group_power')
        if int(group_power) <= user_group_power:
            return sanicjson({'result': 0, 'msg': "Can't delete permission group higher than your permission!"})
    # 删除前检查权限组下是否有绑定用户
    sql_ = "select * from sis_user where user_group_id='%s'" % group_id
    res = await serverdb.querySearch(sql_)
    if len(res) > 0:
        return sanicjson(
            {'result': 0, 'msg': 'The permission group is being referenced by the user and cannot be deleted!'})
    # 删除前检查权限组是否绑定的有接口
    sql_ = "select * from interface_group where user_group_id='%s'" % group_id
    res = await serverdb.querySearch(sql_)
    if len(res) > 0:
        return sanicjson(
            {'result': 0, 'msg': 'The permission group is being referenced by the interface and cannot be deleted!'})

    del_user_group_sql = "delete from sis_user_group where id='%s'" % group_id
    res = await serverdb.doSQL(del_user_group_sql)
    if res:
        return sanicjson({'result': 1})
    else:
        return sanicjson({'result': 0, 'msg': 'delete error!'})


# 修改权限组的信息
@user_bp.route('/updateUserGroupList', methods=['GET', 'POST'])
@AuthProtect
async def updateUserGroupList(request):
    '''
    :param request:
    :param user_name 用户名
    :param user_group_power 用户权限
    :param group_id 分组id
    :param group_power 新分组权限
    :return:
    '''
    payload = request.json
    if not payload:
        return sanicjson({'result': 'error'})
    group_id = payload.get('group_id')
    group_power = payload.get('group_power')
    user_group_power = payload.get('user_group_power')
    language = payload.get('user_language')

    sql_ = "select * from sis_user_group where id='%s'" % group_id
    res = await serverdb.querySearch(sql_)
    if len(res) == 0:
        return sanicjson({'result': 0, 'msg': 'permission group does not exist!'})
    else:
        # 检查旧权限是否超出权限范围
        old_power = res[0].get('group_power')
        if old_power <= user_group_power:
            return sanicjson({'result': 0, 'msg': 'Insufficient permissions!'})

    # 检查新权限是否超出权限范围
    if int(group_power) <= user_group_power:
        return sanicjson({'result': 0, 'msg': 'Insufficient permissions!'})

    del_user_group_sql = "update sis_user_group set group_power='%s' where id='%s'" % (group_power, group_id)
    res = await serverdb.doSQL(del_user_group_sql)
    if res:
        return sanicjson({'result': 1})
    else:
        return sanicjson({'result': 0, 'msg': 'update error!'})


# 接口权限的信息展示
@user_bp.route('/interfaceGroupList', methods=['GET', 'POST'])
@AuthProtect
async def interfaceGroupList(request):
    '''
    :param request:
    :param user_name 用户名
    :param user_group_power 用户权限
    :return:
    '''
    payload = request.json
    if not payload:
        return sanicjson({"result": 0, "msg": "Parameters of the abnormal!"})

    query_interface_group_sql = "select * from sis_user_group"
    query_res = await serverdb.querySearch(query_interface_group_sql)
    group_data = []
    if len(query_res) > 0:
        for i in query_res:
            group_data.append(dict(i).copy())

    query_interface_group_sql = "select i1.*, u2.group_name from interface_group as i1 inner join sis_user_group as u2 on i1.user_group_id=u2.id"
    query_res = await serverdb.querySearch(query_interface_group_sql)
    interface_data = []
    if len(query_res) > 0:
        for i in query_res:
            interface_data.append(dict(i).copy())
        # print(data)
    return sanicjson({'result': 1, 'interface_data': interface_data, 'group_data': group_data})


# 新增接口权限信息
@user_bp.route('/addInterfaceGroupList', methods=['POST'])
@AuthProtect
async def addInterfaceGroupList(request):
    '''
    :param request:
    :param user_name 用户名
    :param user_group_power 用户权限
    :param interface_name 接口名
    :param interface_addr 接口地址
    :param user_group_id 权限组id
    :return:
    '''
    payload = request.json
    if not payload:
        return sanicjson({"result": 0, "msg": "Parameters of the abnormal!"})
    user_group_power = payload.get('user_group_power')
    interface_name = payload.get('interface_name')
    interface_addr = payload.get('interface_addr')
    user_group_id = payload.get('user_group_id')
    # 检查接口地址是否重复
    check_interface_addr_sql = "select * from interface_group where interface_addr='%s'" % interface_addr
    check_interface_addr_res = await serverdb.querySearch(check_interface_addr_sql)
    if len(check_interface_addr_res) > 0:
        return sanicjson({'result': 0, 'msg': 'interface_addr cannot be repeated!'})

    # 检查新权限是否超出当前用户权限
    check_group_power_sql = "select group_power from sis_user_group where id='%s'" % user_group_id
    check_group_power_res = await serverdb.querySearch(check_group_power_sql)
    if len(check_group_power_res) > 0:
        group_power = check_group_power_res[0].get('group_power')
        if int(group_power) <= int(user_group_power):
            return sanicjson({'result': 0, 'msg': 'Authority level exceeds current user operation authority!'})

    add_interface_group_sql = "insert into interface_group(interface_name,interface_addr,user_group_id) values('%s','%s','%s')" \
                              % (interface_name, interface_addr, user_group_id)
    res = await serverdb.doSQL(add_interface_group_sql)
    if res:
        return sanicjson({'result': 1})
    else:
        return sanicjson({'result': 0, 'msg': 'update error!'})


# 修改接口权限信息
@user_bp.route('/updateInterfaceGroupList', methods=['POST'])
@AuthProtect
async def updateInterfaceGroupList(request):
    '''
    :param request:
    :param user_name 用户名
    :param user_group_power 用户权限
    :param interface_name 接口名
    :param interface_addr 接口地址
    :param user_group_id 权限组id
    :return:
    '''
    payload = request.json
    if not payload:
        return sanicjson({"result": 0, "msg": "Parameters of the abnormal!"})
    user_group_power = payload.get('user_group_power')
    interface_id = payload.get('id')
    interface_name = payload.get('interface_name')
    interface_addr = payload.get('interface_addr')
    group_id = payload.get('user_group_id')

    # 检查旧的接口权限组等级，
    sql = "select u1.group_power from sis_user_group as u1 inner join interface_group as i1 on u1.id=i1.user_group_id where i1.id='%s'" % interface_id
    res = await serverdb.querySearch(sql)
    if len(res) > 0:
        interface_power = res[0].get('group_power')
        if int(interface_power) <= int(user_group_power):
            return sanicjson({'result': 0, 'msg': 'No permission to operate the interface!'})

    # 检查新的接口权限组等级
    sql = "select group_power from sis_user_group where id='%s'" % group_id
    res = await serverdb.querySearch(sql)
    if len(res) > 0:
        # 如果新的权限组等级比当前用户等级高，则失败
        group_power = res[0].get('group_power')
        if int(group_power) <= int(user_group_power):
            return sanicjson(
                {'result': 0, 'msg': 'The new permission level exceeds the current user operation permission!'})
    add_interface_group_sql = "update interface_group set interface_name='%s',interface_addr='%s',user_group_id='%s' where id='%s'" \
                              % (interface_name, interface_addr, group_id, interface_id)
    res = await serverdb.doSQL(add_interface_group_sql)
    if res:
        return sanicjson({'result': 1})
    else:
        return sanicjson({'result': 0, 'msg': 'update error!'})


# <editor-fold desc="内容介绍:展示用户列表">
@user_bp.route('/userList', methods=['POST', 'GET'])
@AuthProtect
async def userList(request):
    '''
    用户列表展示，仅展示比当前登录用户权限低的用户
    :param request:
    :param user_group_power 用户权限
    :param user_name 操作用户
    :return:
    '''
    payload = request.json
    if not payload:
        return sanicjson({"result": 0, "msg": "Parameters of the abnormal!"})
    user_group_power = int(payload.get('user_group_power'))
    user_name = payload.get('user_name')
    user_language = payload.get('user_language')
    warehouse_category_id = int(payload.get('warehouse_category_id'))
    factory_id = payload.get('factory_id')
    # 查询当前用户库位信息
    q_userinfo_sql = "select id,user_name,warehouse_category_id,warehouse_name_id from sis_user where user_name='{}'".format(user_name)
    q_userinfo_res = await serverdb.querySearch(q_userinfo_sql)
    if len(q_userinfo_res) == 0:
        return sanicjson(basic_return(result=BasicReturnCode.RESPONSE_FAIL, code=BasicReturnCode.USER_NOT_EXIST, language=user_language))
    current_warehouse_category_id = dict(q_userinfo_res[0]).get("warehouse_category_id")
    # 查询低权限用户
    query_sql = "select u1.id as user_id,u1.user_name,u1.user_number,u1.user_group_id,u2.group_name,u2.group_power," \
                "u1.warehouse_category_id,w2.category_name,u1.warehouse_name_id,w1.warehouse_name,u1.menu_id as menu_id,u1.pda_menu_id as pda_menu_id " \
                "from sis_user u1 left join sis_user_group u2 on u1.user_group_id=u2.id " \
                "left join warehouse_name w1 on u1.warehouse_name_id=w1.id " \
                "left join warehouse_category w2 on u1.warehouse_category_id=w2.id where 1=1 "
    # user_group_power < 2 0/1管理员权限,2库管，3操作员，库管查看当前仓的操作员列表
    if user_group_power < 2:
        query_sql += " and u2.group_power>'%s'" % (user_group_power)
    elif user_group_power == 2:
        query_sql += " and u2.group_power>'%s' and u1.warehouse_category_id=%s" % (user_group_power, current_warehouse_category_id)
    else:
        query_sql += " and u2.group_power>'%s' and u1.warehouse_category_id='%s'" % (
                        user_group_power, current_warehouse_category_id)
    if factory_id:
        query_sql += " and u1.factory_id = '%s'" % factory_id
    query_res = await serverdb.querySearch(query_sql)
    user_list = []
    if len(query_res) > 0:
        for user_info in query_res:
            user_info = dict(user_info)
            pda_menu_id = user_info['pda_menu_id'] if user_info.get('pda_menu_id') else []
            user_info['pda_menu_id'] = pda_menu_id
            if user_language != 'zh':
                user_info['group_name'] = userGroup_zh_2_en.get(user_info['group_name'])
            user_list.append(user_info)
        return sanicjson({'result': 1, 'user_list': user_list})
    else:
        return sanicjson({"result": 0, "msg": "There are no users under this permission!"})


# </editor-fold>


# <editor-fold desc="内容介绍:添加用户">
@user_bp.route('/addUser', methods=['POST'])
@AuthProtect
async def addUser(request):
    '''
    添加用户
    :param request:
    :param op_user_name 操作员用户名
    :param op_user_group_power 操作员用户权限
    :param add_user_name 目标用户名
    :param add_user_passwd 目标用户密码
    :param user_group_id 权限组id
    :param warehouse_category_id  所属仓储类别
    :param warehouse_name_id  所属仓储
    :return:
    '''
    payload = request.json

    op_user_name = payload.get('user_name')
    op_user_group_power = payload.get('user_group_power')
    add_user_name = payload.get('add_user_name')
    add_user_passwd = payload.get('add_user_passwd')
    add_user_number = payload.get('add_user_number')
    user_group_id = payload.get('add_user_group_id')
    warehouse_name_id = payload.get('add_warehouse_name_id', '0')
    warehouse_category_id = payload.get('add_warehouse_category_id', '0')
    factory_id = payload.get('factory_id', 0)
    language = payload.get('user_language')

    await OAuth.createUser(add_user_name, add_user_passwd, add_user_number, op_user_name, user_group_id,
                           op_user_group_power, warehouse_category_id, warehouse_name_id, factory_id)

    return sanicjson(
        basic_return(result=BasicReturnCode.RESPONSE_SUCCESS, code=BasicReturnCode.GET_OK,
                     language=language))


# </editor-fold>


# <editor-fold desc="内容介绍:删除用户">
@user_bp.route('/delUser', methods=['POST'])
@AuthProtect
async def delUser(request):
    '''
    :param request:
    :param del_user_id 要删除的用户id
    :param user_name 当前操作用户
    :param user_group_power 当前操作用户权限
    :return:
    '''
    payload = request.json
    if not payload:
        return sanicjson({"result": 0, "msg": "Parameters of the abnormal!"})
    op_user_name = payload.get('user_name')
    op_user_group_power = payload.get('user_group_power')
    del_user_id = payload.get('del_user_id')
    language = payload.get('user_language')
    await OAuth.delUser(user_id=del_user_id, op_user_name=op_user_name, op_user_group_power=op_user_group_power)

    return sanicjson(
        basic_return(result=BasicReturnCode.RESPONSE_SUCCESS, code=BasicReturnCode.DELETE_OK,
                     language=language))


# </editor-fold>


# <editor-fold desc="内容介绍:修改个人密码">
@user_bp.route('/changeUserPasswd', methods=['POST'])
@AuthProtect
async def changeUserPasswd(request):
    '''
    修改用户密码
    :param request:
    :param user_name 用户名
    :param user_group_power 权限等级
    :param old_passwd 旧密码
    :param new_passwd 新密码
    :param user_id 用户id
    :return:
    '''
    payload = request.json
    user_id = payload.get('user_id')
    old_passwd = payload.get('old_passwd')
    new_passwd = payload.get('new_passwd')
    language = payload.get('user_language')

    await OAuth.updatePasswordByOwn(user_id=user_id, old_password=old_passwd, new_password=new_passwd)

    return sanicjson(
        basic_return(result=BasicReturnCode.RESPONSE_SUCCESS, code=BasicReturnCode.USER_UPDATE_SUCCESS,
                     language=language))


# </editor-fold>
@user_bp.route('/passwordVerify', methods=['POST'])
@AuthProtect
async def passwordVerify(request):
    payload = request.json
    password = payload.get('password')
    language = payload.get('user_language')
    await OAuth.passwordVerify(password)
    return sanicjson(
        basic_return(result=BasicReturnCode.RESPONSE_SUCCESS, code=BasicReturnCode.GET_OK,
                     language=language))


# <editor-fold desc="内容介绍:管理员修改普通用户密码">
@user_bp.route('/adminChangeUserInfo', methods=['POST'])
@AuthProtect
async def adminChangeUserInfo(request):
    payload = request.json
    if not payload:
        return sanicjson({"result": 0, "msg": "Parameters of the abnormal!"})
    # print(payload)
    op_user_name = payload.get('user_name')
    op_user_group_power = int(payload.get('user_group_power'))
    op_warehouse_category_id = int(payload.get('warehouse_category_id'))
    target_user_id = int(payload.get('target_user_id'))
    target_user_name = payload.get('target_user_name')
    target_user_new_passwd = payload.get('target_user_new_passwd')
    target_user_group_id = int(payload.get('target_user_group_id'))
    target_user_warehouse_category_id = int(payload.get('target_user_warehouse_category_id', 0))
    target_user_warehouse_name_id = int(payload.get('target_user_warehouse_name_id'))
    if not op_user_name or op_user_group_power > 2:
        return sanicjson({'result': 0, 'msg': 'Parameter error!'})
    query_target_user_sql = "select * from sis_user u1 left join sis_user_group u2 on u1.user_group_id=u2.id " \
                            "where u1.id='%s' and u1.user_name='%s'" % (target_user_id, target_user_name)
    query_target_user_res = await serverdb.querySearch(query_target_user_sql)
    new_target_user_group_power_sql = "select group_power from sis_user_group where id='%s'" % (target_user_group_id)
    new_target_user_group_power_res = await serverdb.querySearch(new_target_user_group_power_sql)
    new_target_user_group_power = int(new_target_user_group_power_res[0].get('group_power'))
    if len(query_target_user_res) > 0:
        target_user_info = dict(query_target_user_res[0])
        # 检查操作员权限
        if op_user_group_power > 1 and int(target_user_info['warehouse_category_id']) != int(op_warehouse_category_id):
            return sanicjson({'result': 0, 'msg': 'Authority level exceeds current user operation authority!'})
        # 检查目标用户的权限是否比操作员权限大
        if int(target_user_info['group_power']) <= int(
                op_user_group_power) or new_target_user_group_power <= op_user_group_power:
            return sanicjson({'result': 0, 'msg': 'Authority level exceeds current user operation authority!'})
        if target_user_new_passwd:
            await OAuth.updatePasswordByOther(user_id=target_user_id, new_password=target_user_new_passwd, op_user_name=op_user_name,
                                              op_user_group_power=op_user_group_power)
            update_target_user_info_sql = "update sis_user set user_group_id='%s',warehouse_category_id='%s',warehouse_name_id='%s' " \
                                          "where id='%s' and user_name='%s';" % (
                                              target_user_group_id,
                                              target_user_warehouse_category_id, target_user_warehouse_name_id,
                                              target_user_id, target_user_name)
        else:
            update_target_user_info_sql = "update sis_user set user_group_id='%s',warehouse_category_id='%s',warehouse_name_id='%s' " \
                                          "where id='%s' and user_name='%s';" % (
                                              target_user_group_id, target_user_warehouse_category_id,
                                              target_user_warehouse_name_id, target_user_id, target_user_name)
        update_target_user_info_res = await serverdb.doSQL(update_target_user_info_sql)
        add_user_log_sql = "insert into sis_user_log(op_name,op_code,target_name,target_group_id,target_category_id,target_warehouse_id,target_comment) " \
                           "values('%s','%s','%s','%s','%s','%s','%s')" \
                           % (
                               op_user_name, 6, target_user_name, target_user_group_id,
                               target_user_warehouse_category_id,
                               target_user_warehouse_name_id, 'Change user info!')
        await serverdb.doSQL(add_user_log_sql)
        return sanicjson({'result': 1})
    else:
        return sanicjson({'result': 0, 'msg': 'User does not exist!'})


# </editor-fold>


# <editor-fold desc="内容介绍:管理员修改普通用户密码">
@user_bp.route('/adminChangeUserPasswd', methods=['POST'])
@AuthProtect
async def adminChangeUserPasswd(request):
    '''
    管理员修改普通用户密码
    :param request:
    :param user_name 用户名
    :param user_group_power 用户权限
    :param new_passwd 新密码
    :param user_id 目标用户id
    :return:
    '''
    payload = request.json
    if not payload:
        return sanicjson({"result": 0, "msg": "Parameters of the abnormal!"})
    user_id = payload.get('user_id')
    user_name = payload.get('user_name')
    user_group_power = payload.get('user_group_power')
    new_passwd = payload.get('new_passwd')
    language = payload.get('user_language')

    await OAuth.updatePasswordByOther(user_id=user_id, new_password=new_passwd, op_user_name=user_name,
                                      op_user_group_power=user_group_power)

    return sanicjson(
        basic_return(result=BasicReturnCode.RESPONSE_SUCCESS, code=BasicReturnCode.USER_UPDATE_SUCCESS,
                     language=language))


# </editor-fold>


# <editor-fold desc="内容介绍:管理员修改用户所属区域">
@user_bp.route('/adminChangeUserRegion', methods=['POST'])
@AuthProtect
async def adminChangeUserRegion(request):
    '''
    :param request:
    :param user_id 目标用户id
    :param user_name 操作员
    :param user_group_power 操作员权限
    :param region_id 区域id
    :param warehouse_name_id 仓储类别id
    :return:
    '''
    payload = request.json
    if not payload:
        return sanicjson({"result": 0, "msg": "Parameters of the abnormal!"})
    user_id = payload.get('user_id')
    user_name = payload.get('user_name')
    user_group_power = payload.get('user_group_power')
    region_id = payload.get('region_id')
    warehouse_name_id = payload.get('warehouse_name_id')
    query_passwd_sql = "select * from sis_user where id='%s'" % (user_id)
    res = await serverdb.querySearch(query_passwd_sql)
    if len(res) > 0:
        user = dict(res[0])
        # print(user)
        # 检查目标用户的权限是否比操作员权限大
        check_group_power_sql = "select group_power from sis_user_group where id='%s'" % user.get("user_group_id")
        check_group_power_res = await serverdb.querySearch(check_group_power_sql)
        if len(check_group_power_res) > 0:
            # print(check_group_power_res)
            group_power = check_group_power_res[0].get('group_power')
            if int(group_power) <= int(user_group_power):
                return sanicjson({'result': 0, 'msg': 'Authority level exceeds current user operation authority!'})
        update_passwd_sql = "update sis_user set region_id='%s',warehouse_name_id='%s' where id='%s'" % (
            region_id, warehouse_name_id, user_id)
        res = await serverdb.doSQL(update_passwd_sql)

        add_user_log_sql = "insert into sis_user_log(op_name,op_code,target_name,target_group_id,target_region_id,target_warehouse_id,target_comment) " \
                           "values('%s','%s','%s','%s','%s','%s','%s')" \
                           % (
                               user_name, 5, user.get('user_name'), user.get('user_group_id'), region_id,
                               warehouse_name_id,
                               'admin change region!')
        await serverdb.doSQL(add_user_log_sql)
        return sanicjson({'result': 1})
    else:
        return sanicjson({'result': 0, 'msg': 'no data!'})


# </editor-fold>


# <editor-fold desc="内容介绍:管理员修改用户权限组">
@user_bp.route('/adminChangeUserGroup', methods=['POST'])
@AuthProtect
async def adminChangeUserGroup(request):
    '''
    :param request:
    :param user_id 目标用户id
    :param user_name 操作员
    :param user_group_power 操作员权限
    :param user_group_id 权限组id
    :return:
    '''
    payload = request.json
    if not payload:
        return sanicjson({"result": 0, "msg": "Parameters of the abnormal!"})
    user_id = payload.get('user_id')
    user_name = payload.get('user_name')
    user_group_power = payload.get('user_group_power')
    user_group_id = payload.get('user_group_id')
    query_passwd_sql = "select * from sis_user where id='%s'" % (user_id)
    res = await serverdb.querySearch(query_passwd_sql)
    if len(res) > 0:
        user = dict(res[0])
        # 检查目标用户的旧权限是否比操作员权限大
        check_group_power_sql = "select group_power from sis_user_group where id='%s'" % user.get("user_group_id")
        check_group_power_res = await serverdb.querySearch(check_group_power_sql)
        if len(check_group_power_res) > 0:
            group_power = check_group_power_res[0].get('group_power')
            if int(group_power) <= int(user_group_power):
                return sanicjson({'result': 0, 'msg': 'Authority level exceeds current user operation authority!'})

        # 检查目标用户的新权限是否比操作员权限大
        check_group_power_sql = "select group_power from sis_user_group where id='%s'" % user_group_id
        check_group_power_res = await serverdb.querySearch(check_group_power_sql)
        if len(check_group_power_res) > 0:
            group_power = check_group_power_res[0].get('group_power')
            if int(group_power) <= int(user_group_power):
                return sanicjson({'result': 0, 'msg': 'Authority level exceeds current user operation authority!'})

        update_passwd_sql = "update sis_user set user_group_id='%s' where id='%s'" % (user_group_id, user_id)
        res = await serverdb.doSQL(update_passwd_sql)

        add_user_log_sql = "insert into sis_user_log(op_name,op_code,target_name,target_group_id,target_region_id,target_warehouse_id,target_comment) " \
                           "values('%s','%s','%s','%s','%s','%s','%s')" \
                           % (user_name, 4, user.get('user_name'), user_group_id, user.get('region_id'),
                              user.get('warehouse_name_id'), 'admin change region!')
        await serverdb.doSQL(add_user_log_sql)
        return sanicjson({'result': 1})
    else:
        return sanicjson({'result': 0, 'msg': 'no data!'})


# </editor-fold>


# <editor-fold desc="用户回溯">
# 用户回溯
@user_bp.route('/userActionRecord', methods=['POST'])
@AuthProtect
async def userActionRecord(request):
    payload = request.json
    if not payload:
        return sanicjson({"result": 0, "msg": "Parameters of the abnormal!"})
    start_time = payload.get("start_time", '')
    end_time = payload.get("end_time", '')
    select_user_name = payload.get("select_user_name")
    # 查询仓储相关
    query_warehouse_log_sql = "SELECT w1.in_time,w1.shelf_id,w1.position,w1.save_id,w1.label_code,w1.op_code,s1.position_info FROM warehouse_log w1 " \
                              "left join shelf_position_relation s1 on w1.shelf_id=s1.shelf_id and w1.position=s1.shelf_position WHERE w1.op_name='%s'" % (
                                  select_user_name)
    # 查询料架相关
    query_shelf_log_sql = "SELECT in_time,shelf_id,op_code FROM shelf_log WHERE op_name='%s'" % (select_user_name)
    # 查询用户操作相关
    query_user_log_sql = "SELECT in_time,op_code,target_name,target_comment FROM sis_user_log WHERE op_name='%s'" % (
        select_user_name)

    if start_time:
        query_warehouse_log_sql += " AND w1.in_time BETWEEN '%s' AND '%s' ORDER BY w1.in_time DESC " % (
            start_time, end_time)
        query_shelf_log_sql = query_shelf_log_sql + " AND in_time BETWEEN '%s' AND '%s' ORDER BY in_time DESC " % (
            start_time, end_time)
        query_user_log_sql = query_user_log_sql + " AND in_time BETWEEN '%s' AND '%s' ORDER BY in_time DESC " % (
            start_time, end_time)
    else:
        query_warehouse_log_sql = query_warehouse_log_sql + " ORDER BY in_time DESC"
        query_shelf_log_sql = query_shelf_log_sql + " ORDER BY in_time DESC"
        query_user_log_sql = query_user_log_sql + " ORDER BY in_time DESC"
    send_data = {}
    send_data['warehouse_log'] = []
    send_data['shelf_log'] = []
    send_data['user_log'] = []
    query_warehouse_log_res = await serverdb.querySearch(query_warehouse_log_sql)
    if len(query_warehouse_log_res) > 0:
        for data in query_warehouse_log_res:
            data_dict = dict(data)
            data_dict['in_time'] = utc_time_conversion(data_dict['in_time'])
            send_data['warehouse_log'].append(data_dict)
    query_shelf_log_res = await serverdb.querySearch(query_shelf_log_sql)
    if len(query_shelf_log_res) > 0:
        for data in query_shelf_log_res:
            data_dict = dict(data)
            data_dict['in_time'] = utc_time_conversion(data_dict['in_time'])
            send_data['shelf_log'].append(data_dict)
    query_user_log_res = await serverdb.querySearch(query_user_log_sql)
    if len(query_user_log_res) > 0:
        for data in query_user_log_res:
            data_dict = dict(data)
            data_dict['in_time'] = utc_time_conversion(data_dict['in_time'])
            send_data['user_log'].append(data_dict)
    send_data['result'] = 1
    return sanicjson(send_data)


# 用户回溯下载报表
@user_bp.route('/exportUserRecord', methods=['POST'])
@AuthProtect
async def exportUserRecord(request):
    payload = request.json
    if not payload:
        return sanicjson({"result": 0, "msg": "Parameters of the abnormal!"})
    start_time = payload.get("start_time", '')
    end_time = payload.get("end_time", '')
    select_user_name = payload.get("select_user_name")
    op_type = int(payload.get("op_type"))
    op_name = payload.get("user_name")
    # op_type代表下载的报表类型，1代表仓储，2代表物料架，3代表用户操作记录
    if op_type == 1:
        # 查询仓储相关
        query__sql = "SELECT in_time,shelf_id,position,save_id,label_code,steel_model,op_code FROM warehouse_log WHERE op_name='%s'" % (
            select_user_name)
        rename_ = {"in_time": "时间", "shelf_id": "物料架", "position": "孔位", "label_code": "物料条码",
                   'steel_model': '物料类型', 'op_code': '动作'}
    elif op_type == 2:
        # 查询料架相关
        query__sql = "SELECT in_time,shelf_id,op_code FROM shelf_log WHERE op_name='%s'" % (select_user_name)
        rename_ = {"in_time": "时间", "shelf_id": "物料架", 'op_code': '动作'}
    elif op_type == 3:
        # 查询用户操作相关
        query__sql = "SELECT in_time,op_code,target_name,target_comment FROM sis_user_log WHERE op_name='%s'" % (
            select_user_name)
        rename_ = {"in_time": "时间", "target_name": "操作对象", "target_comment": "操作信息", 'op_code': '动作'}
    else:
        return sanicjson({"result": 0, "msg": "Operation type error!"})

    if start_time:
        query__sql = query__sql + " AND in_time BETWEEN '%s' AND '%s' ORDER BY in_time DESC " % (
            start_time, end_time)
    else:
        query__sql = query__sql + " ORDER BY in_time DESC"
    conn = psycopg2.connect(host=postgres_data['host'], user=postgres_data['user'], password=postgres_data['password'],
                            database=postgres_data['database'])
    df = pd.read_sql_query(query__sql, conn)
    conn.close()        
    df['in_time'] = df['in_time'].apply(
        lambda a: pd.to_datetime(a, utc=True).tz_convert('Asia/Shanghai').strftime("%Y-%m-%d %H:%M:%S"))
    df.rename(columns=rename_, inplace=True)
    # print(df)
    for num in range(0, int(df.shape[0])):
        data = int(df.loc[num, '动作'])
        # 仓储相关
        if op_type == 1:
            if data == 1:
                df.loc[num, '动作'] = "条码枪上料"
            elif data == 2:
                df.loc[num, '动作'] = "条码枪取料"
            elif data == 3:
                df.loc[num, '动作'] = "异常取料"
            elif data == 4:
                df.loc[num, '动作'] = "重复上架弹出"
            elif data == 5:
                df.loc[num, '动作'] = "禁用物料"
            elif data == 6:
                df.loc[num, '动作'] = "API上料"
            elif data == 7:
                df.loc[num, '动作'] = "API取料"
            elif data == 8:
                df.loc[num, '动作'] = "撤消料架亮灯"
            elif data == 9:
                df.loc[num, '动作'] = "工单取料，首套"
            elif data == 10:
                df.loc[num, '动作'] = "工单取料，全套"
            elif data == 11:
                df.loc[num, '动作'] = "站位顺序发料"
            elif data == 12:
                df.loc[num, '动作'] = "库位整理"
            elif data == 13:
                df.loc[num, '动作'] = "物料转移上架"
            elif data == 14:
                df.loc[num, '动作'] = "物料修改数量"
            elif data == 15:
                df.loc[num, '动作'] = "解除物料冻结"
            elif data == 16:
                df.loc[num, '动作'] = "物料报废"
            elif data == 17:
                df.loc[num, '动作'] = "物料回复使用"
            elif data == 19:
                df.loc[num, '动作'] = "冻结物料发出"
        # 物料架操作记录
        elif op_type == 2:
            if data == 1:
                df.loc[num, '动作'] = "上料超时"
            elif data == 2:
                df.loc[num, '动作'] = "报警"
            elif data == 3:
                df.loc[num, '动作'] = "取消报警"
            elif data == 4:
                df.loc[num, '动作'] = "绑定物料架"
            elif data == 5:
                df.loc[num, '动作'] = "解绑物料架"
            elif data == 6:
                df.loc[num, '动作'] = "清空物料架数据"
            elif data == 7:
                df.loc[num, '动作'] = "删除物料架"
        # 用户操作记录
        elif op_type == 3:
            if data == 1:
                df.loc[num, '动作'] = "添加用户"
            elif data == 2:
                df.loc[num, '动作'] = "删除用户"
            elif data == 3:
                df.loc[num, '动作'] = "修改密码"
            elif data == 4:
                df.loc[num, '动作'] = "修改用户权限组"
            elif data == 5:
                df.loc[num, '动作'] = "修改用户区域"
            elif data == 6:
                df.loc[num, '动作'] = "管理员修改用户信息"
    filename = "用户回溯信息记录.csv"
    # print(df)
    file = os.path.join(export_file_path, filename)
    df.to_csv(file, index=False, encoding="utf_8_sig")
    export_sql = "insert into export_log(file_type, op_name) values(5, '%s')" % op_name
    await serverdb.doSQL(export_sql)
    return await response.file(filename=filename, location=file)


# </editor-fold>


# <editor-fold desc="权限配置相关接口">
# 前端页面ID接收保存
@user_bp.route('/saveMenuID', methods=['POST'])
@AuthProtect
async def saveMenuID(request):
    payload = request.json
    if not payload:
        return sanicjson({"result": 0, "msg": "Parameters of the abnormal!"})
    target_user_id = payload.get("target_user_id")
    user_name = payload.get("user_name")
    target_user_name = payload.get("target_user_name")
    user_group_power = int(payload.get("user_group_power"))
    menu_id = payload.get('menu_id', []) or []
    if user_group_power > 0:
        return sanicjson({"result": 0, "msg": "权限不足!"})
    if menu_id:
        update_sql = "update sis_user set menu_id=array%s where id='%s' and user_name='%s';" % (
            menu_id, target_user_id, target_user_name)
    else:
        update_sql = "update sis_user set menu_id='{}' where id='%s' and user_name='%s';" % (
            target_user_id, target_user_name)
    update_res = await serverdb.doSQL(update_sql)
    if update_res == 0:
        return sanicjson({"result": 0, "msg": "权限配置失败!"})
    return sanicjson({"result": 1})


# </editor-fold>

# 前端页面ID接收保存
@user_bp.route('/savePdaMenuID', methods=['POST'])
@AuthProtect
async def savePdaMenuID(request):
    payload = request.json
    if not payload:
        return sanicjson({"result": 0, "msg": "Parameters of the abnormal!"})
    target_user_id = payload.get("target_user_id")
    user_name = payload.get("user_name")
    target_user_name = payload.get("target_user_name")
    user_group_power = int(payload.get("user_group_power"))
    menu_id = payload.get('pda_menu_id', []) or []
    if user_group_power > 0:
        return sanicjson({"result": 0, "msg": "权限不足!"})
    if menu_id:
        update_sql = "update sis_user set pda_menu_id=array%s where id='%s' and user_name='%s';" % (
            menu_id, target_user_id, target_user_name)
    else:
        update_sql = "update sis_user set pda_menu_id='[]' where id='%s' and user_name='%s';" % (
            target_user_id, target_user_name)
    update_res = await serverdb.doSQL(update_sql)
    if update_res == 0:
        return sanicjson({"result": 0, "msg": "权限配置失败!"})
    return sanicjson({"result": 1})


# 定义登出时间
@user_bp.route('/logOutStaticTime', methods=['POST'])
@AuthProtect
async def logOutStaticTime(request):
    payload = request.json
    if not payload:
        return sanicjson(
            basic_return(result=BasicReturnCode.RESPONSE_FAIL, code=BasicReturnCode.PARAMS_LOST))
    language = payload.get("user_language")
    LogoutStaticTime = await OAuth.getLogoutStaticTime()
    return sanicjson(
        basic_return(result=BasicReturnCode.RESPONSE_SUCCESS, code=BasicReturnCode.GET_OK,
                     language=language, data=LogoutStaticTime))
