from typing import TYPE_CHECKING

import logging

from ..config import Config

if TYPE_CHECKING:
    from ..addon_manager import AddonManager

class Logger:
    class LogConstructor:
        def __init__(self, level: int) -> None:
            self.__message: str = ""
            self.__level = level

        def add(self, message: str, indent: int=0, newline: bool=True) -> None:
            self.__message += Logger.message_with_indent(indent, message) + '\n' if newline else ''

        def print(self) -> None:
            # The log is not output as intended. Unknown cause.
            Logger.LOGGER.warning(self.__message)
            match self.__level:
                case logging.DEBUG:
                    Logger.LOGGER.debug(self.__message)
                case logging.INFO:
                    Logger.LOGGER.info(self.__message)
                case logging.WARNING:
                    Logger.LOGGER.warning(self.__message)
                case logging.ERROR:
                    Logger.LOGGER.error(self.__message)
                case logging.CRITICAL:
                    Logger.LOGGER.critical(self.__message)
                case _:
                    raise ValueError("The errorlevel value is invalid.")

    @classmethod
    def init(cls, addon: 'AddonManager') -> None:
        cls.ADDON = addon

        cls.LOGGER = logging.getLogger(cls.ADDON.ADDON_FOLDER_NAME)

        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG if Config().data["is_debug_mode"] else logging.INFO)

        formatter = logging.Formatter('%(name)s - %(levelname)s - %(asctime)s - %(message)s')
        handler.setFormatter(formatter)

        cls.LOGGER.addHandler(handler)

    @staticmethod
    def message_with_indent(level: int, message: str, width: int=4) -> str:
        return (f"{' ' * width * level}{message}")