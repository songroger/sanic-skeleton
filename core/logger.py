import os
import logging.handlers
from settings import settings


class ServerLogger(object):
    _loggerInstance = None
    _loggerInit = False

    def __new__(cls, *args, **kwargs):
        if not cls._loggerInstance:
            cls._loggerInstance = super(ServerLogger, cls).__new__(cls, *args, **kwargs)
        return cls._loggerInstance

    def __init__(self):
        if not self._loggerInit:
            log_dir_path = settings.log_file_path
            handlers = {
                logging.DEBUG: "Debug/debug.log",
                logging.INFO: "Info/service.log",
                logging.WARNING: "Warning/warning.log",
                logging.ERROR: "Error/error.log",
                logging.CRITICAL: "Critical/critical.log",
            }
            self.__loggers = {}
            logLevels = handlers.keys()
            fmt = logging.Formatter(
                '%(asctime)s - ThreadName:%(threadName)s(ID:%(thread)d)[%(levelname)s]:%(message)s')
            for level in logLevels:
                # 创建logger
                logger = logging.getLogger(str(level))
                logger.setLevel(level)
                # 输出到控制台
                stream_handler = logging.StreamHandler()
                stream_handler.setLevel(level)
                # 设置控制台的输出格式
                stream_handler.setFormatter(fmt)
                # 将控制台处理器添加dao日志器中
                logger.addHandler(stream_handler)

                # 创建hander用于写日日志文件
                logPath = os.path.join(log_dir_path, handlers[level])
                dirPath = os.path.dirname(logPath)
                if not os.path.exists(dirPath):
                    os.makedirs(dirPath)
                fileHandler = logging.handlers.RotatingFileHandler(filename=logPath, maxBytes=1024 * 50 * 1024,
                                                                   backupCount=50, encoding="utf-8", delay=False)

                # 定义日志的输出格式
                fileHandler.setFormatter(fmt)
                fileHandler.setLevel(level)
                logger.addHandler(fileHandler)
                self.__loggers.update({level: logger})
            self._loggerInit = True

    def info(self, message, *args, **kwargs):
        self.__loggers[logging.INFO].info(message, *args, **kwargs)

    def debug(self, message, *args, **kwargs):
        self.__loggers[logging.DEBUG].debug(message, *args, **kwargs)

    def error(self, message, exc_info=True, *args, **kwargs):
        self.__loggers[logging.ERROR].error(message, exc_info=exc_info, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        self.__loggers[logging.WARNING].warning(message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        self.__loggers[logging.CRITICAL].critical(message, *args, **kwargs)


logger = ServerLogger()
