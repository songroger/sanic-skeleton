import time
import re
from common.common_config import EXPIRATION_WARNING_DELTA, TOKEN_HEADER, EXPIRATION_DELTA, USER_PASSWORD_REG, \
    USER_LOGOUT_STATIC_TIME
from common import serverdb
from common.constant import BasicReturnCode, USEROpCode
from common.base_func import generate_token, encrypt_msg,parse_token
from common.common_init import redis_conn
from common.sync_db_common_func import getParameterConfig_sync


class OAuthObj:

    # 登录签证
    async def loginAuth(self, user_name, password):
        if not user_name or not password:
            raise Exception(BasicReturnCode.USER_PASSWORD_ERROR)

        user_obj = await self.getUserByName(user_name)
        if not user_obj:
            raise Exception(BasicReturnCode.USER_NOT_EXIST)

        user_password = user_obj.get("user_passwd")
        encrypt_password = encrypt_msg(password)

        if user_password != encrypt_password:
            raise Exception(BasicReturnCode.USER_PASSWORD_ERROR)

        # if self.last_login_expired(user_obj.get("last_login")):
        #     raise Exception(BasicReturnCode.USER_LOGIN_EXPIRED)

        # 生成token
        try:
            current_timestamp = int(time.time())
            user_obj.update(signature_time=current_timestamp)
            token = generate_token(user_obj)
            # 更新登录时间
            await self.updateLoginTime(user_obj.get("user_id"))

            return token
        except Exception:
            raise Exception(BasicReturnCode.USER_LOGIN_FAIL)

    def last_login_expired(self, last_login):
        if not last_login:
            return False
        current_timestamp = int(time.time())
        _, days = getParameterConfig_sync("login_expired_days")
        delta = 24 * 60 * 60 * int(days)
        if not last_login:
            last_login = int(time.time())
        # print(delta, last_login)
        if current_timestamp > int(last_login) + delta:
            return True
        return False

    async def updateLoginTime(self, uid):
        # current_timestamp = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        current_timestamp = int(time.time())
        update_passwd_sql = f"update sis_user set last_login_time='{current_timestamp}' where id='{uid}'"
        res = await serverdb.doSQL(update_passwd_sql)
        return res

    # 查询用户信息
    async def getUserByName(self, user_name):
        _sql = "select a.id as user_id,user_name,user_passwd,factory_id,b.group_power as user_group_power,a.last_login_time as last_login from sis_user a left join" \
               " sis_user_group b on a.user_group_id = b.id where user_name = '%s'" % user_name
        _res = await serverdb.querySearch(_sql)
        if len(_res) == 0:
            user_obj = {}
        else:
            user_obj = dict(_res[0])
        return user_obj

    # 查看用户信息
    async def getUserById(self, user_id):
        _sql = "select  *  from  sis_user  where id = '%s'" % user_id
        _res = await serverdb.querySearch(_sql)
        if len(_res) == 0:
            user_obj = {}
        else:
            user_obj = dict(_res[0])
        return user_obj

    # 刷新token
    async def signatureToken(self, request, token_info):
        try:
            # 判定Token是否在重新签发时间内
            header_payload = request.headers
            old_token = header_payload.get(TOKEN_HEADER)
            if not token_info:
                token_info = parse_token(old_token)
            old_signature_time = token_info.get("signature_time")
            current_timestamp = int(time.time())
            if (current_timestamp + EXPIRATION_WARNING_DELTA) >= (EXPIRATION_DELTA + old_signature_time):
                token_info.update(signature_time=current_timestamp)
                token = generate_token(token_info)
            else:
                token = old_token
            return token
        except Exception:
            raise Exception(BasicReturnCode.USER_TOKEN_SIGNATURE_FAIL)


    # 获取用户信息
    # 基础函数，验证用户是否合法
    async def getUserInfo(self, user_id, factory_id):
        '''
        通过传入的用户名和密码，检验用户是否合法
        :param username
        :return: 验证通过：
        '''
        _user_sql = "select u1.id as user_id, u1.user_number as user_number,u1.user_name,u1.user_group_id,u1.factory_id,u2.group_power as " \
                    "user_group_power,u1.warehouse_category_id,u1.warehouse_name_id, u1.menu_id as menu_id,u1.pda_menu_id as pda_menu_id  " \
                    "from sis_user as u1 inner join sis_user_group as u2 on u1.user_group_id=u2.id " \
                    "where u1.id='%s'" % user_id
        _user_res = await serverdb.querySearch(sql_str=_user_sql)
        # 接口信息
        _interface_sql = "select i1.id as interface_id,i1.interface_name,i1.interface_addr,i1.user_group_id,u2.group_power " \
                         "from interface_group as i1 inner join sis_user_group as u2 on i1.user_group_id=u2.id"
        _interface_res = await serverdb.querySearch(sql_str=_interface_sql)

        # 工厂车间信息
        factory_info = []
        if factory_id:
            _factory_sql = "select factory_name,factory_code from factory where id = '%s'" % factory_id
            _factory_res = await serverdb.querySearch(_factory_sql)
            if len(_factory_res) > 0:
                for _temp_info in _factory_res:
                    info = dict(_temp_info)
                    factory_info.append(info)

        if len(_user_res) > 0:
            # 用户存在
            user_data = dict(_user_res[0])
            user_data['pda_menu_id'] = user_data['pda_menu_id'] if user_data['pda_menu_id'] else []
            interface_group_list = []
            if len(_interface_res) > 0:
                for i in _interface_res:
                    interface_group_list.append(dict(i))
            user_data['interface_group'] = interface_group_list
            user_data['factory_info'] = factory_info
        else:
            # 用户不存在
            raise Exception(BasicReturnCode.USER_NOT_EXIST)
        return user_data

    # 添加用户
    async def createUser(self, add_user_name, add_user_passwd, add_user_number, op_user_name, user_group_id,
                         op_user_group_power, warehouse_category_id, warehouse_name_id, factory_id=0):
        # 检查用户名是否重名
        exist_check_flag = await self.existCheckByName(add_user_name)
        if exist_check_flag:
            raise Exception(BasicReturnCode.USER_EXIST)

        # 检查新权限是否超出用户的权限
        permission_check_flag = await self.permissionOperateCheck(user_group_id, op_user_group_power)
        if not permission_check_flag:
            raise Exception(BasicReturnCode.USER_PERMISSION_DENY)
        try:
            # 密码加密
            encrypt_password = encrypt_msg(add_user_passwd)
            # 用户添加
            add_user_sql_ = "insert into sis_user(user_name,user_passwd,user_group_id,warehouse_category_id," \
                            "warehouse_name_id,user_number,factory_id) values('%s','%s','%s','%s','%s','%s','%s')" % \
                            (add_user_name, encrypt_password, user_group_id, warehouse_category_id, warehouse_name_id,
                             add_user_number, factory_id)
            res = await serverdb.doSQL(add_user_sql_)
            if not res:
                raise Exception(BasicReturnCode.USER_ADD_FAIL)
        except Exception:
            raise Exception(BasicReturnCode.USER_ADD_FAIL)

        # 添加操作日志
        await self.addUserManageLog(op_user_name, USEROpCode.ADD_USER, add_user_name, add_user_number, user_group_id,
                                    warehouse_category_id, warehouse_name_id, USEROpCode.ADD_USER_COMMENT)

    # 删除用户
    async def delUser(self, user_id, op_user_name, op_user_group_power):
        user = await self.getUserById(user_id)
        if not user:
            raise Exception(BasicReturnCode.USER_NOT_EXIST)

        # 获取用户信息
        user_group_id = user.get("user_group_id")

        permission_check_flag = await self.permissionOperateCheck(user_group_id, op_user_group_power)
        if not permission_check_flag:
            raise Exception(BasicReturnCode.USER_PERMISSION_DENY)

        del_user_sql = "delete from sis_user where id='%s'" % user_id
        res = await serverdb.doSQL(del_user_sql)
        if not res:
            raise Exception(BasicReturnCode.DELETE_FAIL)

        add_user_name = user.get("user_name")
        add_user_number = user.get("user_number")
        warehouse_category_id = user.get("warehouse_category_id")
        warehouse_name_id = user.get("warehouse_name_id")

        # 添加操作日志
        await self.addUserManageLog(op_user_name, USEROpCode.DEL_USER, add_user_name, add_user_number, user_group_id,
                                    warehouse_category_id, warehouse_name_id, USEROpCode.DEL_USER_COMMENT)

    # 更新密码
    async def updatePasswordByOwn(self, user_id, old_password, new_password):
        user = await self.getUserById(user_id)
        if not user:
            raise Exception(BasicReturnCode.USER_NOT_EXIST)

        if not all([new_password, old_password]):
            raise Exception(BasicReturnCode.PARAMS_LOST)

        # 密码加密
        db_password = user.get("user_passwd")
        encrypt_old_password = encrypt_msg(old_password)
        if db_password != encrypt_old_password:
            raise Exception(BasicReturnCode.USER_PASSWORD_ERROR)

        encrypt_new_password = encrypt_msg(new_password)

        update_passwd_sql = "update sis_user set user_passwd='%s' where id='%s'" % (encrypt_new_password, user_id)
        res = await serverdb.doSQL(update_passwd_sql)

        if res:
            # 添加操作日志
            op_user_name = user.get('user_name')
            add_user_name = user.get('add_user_name')
            add_user_number = user.get('user_number')
            user_group_id = user.get('user_group_id')
            warehouse_category_id = user.get('warehouse_category_id')
            warehouse_name_id = user.get('warehouse_name_id')
            await self.addUserManageLog(op_user_name, USEROpCode.CHANGE_PASSWORD, add_user_name, add_user_number,
                                        user_group_id,
                                        warehouse_category_id, warehouse_name_id, USEROpCode.CHANGE_PASSWORD_COMMENT)
        else:
            raise Exception(BasicReturnCode.UPDATE_FAIL)

    async def updatePasswordByOther(self, user_id, new_password, op_user_name, op_user_group_power):
        user = await self.getUserById(user_id)
        if not user:
            raise Exception(BasicReturnCode.USER_NOT_EXIST)

        if not new_password:
            raise Exception(BasicReturnCode.PARAMS_LOST)
        user_group_id = user.get("user_group_id")
        permission_check_flag = await self.permissionOperateCheck(user_group_id, op_user_group_power)
        if not permission_check_flag:
            raise Exception(BasicReturnCode.USER_PERMISSION_DENY)

        # 密码加密
        encrypt_new_password = encrypt_msg(new_password)

        update_passwd_sql = "update sis_user set user_passwd='%s' where id='%s'" % (encrypt_new_password, user_id)
        res = await serverdb.doSQL(update_passwd_sql)

        if res:
            # 添加操作日志
            add_user_name = user.get('add_user_name')
            add_user_number = user.get('user_number')
            user_group_id = user.get('user_group_id')
            warehouse_category_id = user.get('warehouse_category_id')
            warehouse_name_id = user.get('warehouse_name_id')
            await self.addUserManageLog(op_user_name, USEROpCode.CHANGE_PASSWORD, add_user_name, add_user_number,
                                        user_group_id,
                                        warehouse_category_id, warehouse_name_id, USEROpCode.CHANGE_PASSWORD_COMMENT)
        else:
            raise Exception(BasicReturnCode.UPDATE_FAIL)

    # 密码规则校验
    @staticmethod
    async def passwordVerify(password):
        password_rule = redis_conn.get("user_password_rule")
        if not password_rule:
            password_rule = USER_PASSWORD_REG
        if re.match(password_rule, password):
            return True
        else:
            raise Exception(BasicReturnCode.USER_PASSWORD_RULE_ERROR)

    # 获取登录无操作超期
    @staticmethod
    async def getLogoutStaticTime():
        logout_static_time = redis_conn.get("logout_static_time")
        if not logout_static_time:
            logout_static_time = USER_LOGOUT_STATIC_TIME
        return logout_static_time

    # 校验用户权限
    @staticmethod
    async def permissionOperateCheck(user_group_id, op_user_group_power):
        check_group_power_sql = "select group_power from sis_user_group where id='%s'" % user_group_id
        check_group_power_res = await serverdb.querySearch(check_group_power_sql)

        check_flag = True
        if len(check_group_power_res) == 0:
            check_flag = False
        else:
            group_power = check_group_power_res[0].get('group_power')
            if int(group_power) <= int(op_user_group_power):
                check_flag = False
        return check_flag

    # 检测用户是否存在
    @staticmethod
    async def existCheckByName(user_name):
        check_flag = True
        check_user_sql = "select id from sis_user where user_name='%s'" % user_name
        check_user_res = await serverdb.querySearch(check_user_sql)
        if len(check_user_res) == 0:
            check_flag = False
        return check_flag

    @staticmethod
    async def existCheckById(user_id):
        check_flag = True
        check_user_sql = "select id from sis_user where id='%s'" % user_id
        check_user_res = await serverdb.querySearch(check_user_sql)
        if len(check_user_res) == 0:
            check_flag = False
        return check_flag

    # 写入操作日志
    @staticmethod
    async def addUserManageLog(op_user_name, op_code, add_user_name, add_user_number, user_group_id,
                               warehouse_category_id, warehouse_name_id, op_comment):
        try:
            add_user_log_sql = "insert into sis_user_log(op_name,op_code,target_name,target_group_id,target_category_id," \
                               "target_warehouse_id,user_number,target_comment) values('%s','%s','%s','%s','%s','%s'," \
                               "'%s','%s')" % (
                                   op_user_name, op_code, add_user_name, user_group_id,
                                   warehouse_category_id, warehouse_name_id, add_user_number, op_comment)
            await serverdb.doSQL(add_user_log_sql)
        except Exception:
            raise Exception(BasicReturnCode.USER_MANAGE_LOG_FAIL)

    # 校验软件licence
    @staticmethod
    async def checkFactoryExist(factory_code):
        if not factory_code:
            raise Exception(BasicReturnCode.PARAMS_LOST)

        exist_factory_sql = "select id from factory where factory_code='%s' LIMIT 1" % factory_code
        exist_factory_res = await serverdb.querySearch(exist_factory_sql)
        if len(exist_factory_res) == 0:
            raise Exception(BasicReturnCode.USER_FACTORY_NOT_EXIST)


OAuth = OAuthObj()
