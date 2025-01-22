# Copyright (c) 2025 mmz-bin
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from __future__ import annotations

from os.path import dirname, join
from typing import Any, Dict, List, NotRequired, Self, TypedDict

import tomllib

class Config:
    """Manage configurations."""
    __instance: Self | None = None
    __is_initialized: bool = False

    class Items(TypedDict):
        is_debug_mode: bool
        disabled: NotRequired[List[str]]
        priorities: NotRequired[List[str]]
        exclude_patterns: NotRequired[List[str]]

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, path: str | None = None) -> None:
        if self.__class__.__is_initialized:
            return
        self.__class__.__is_initialized = True

        self.__path: str = path if path is not None else join(dirname(__file__), "data", "config.toml")

        # 初期データ
        self.__data: Config.Items = {
            "is_debug_mode": False
        }

        self.load()

    def load(self) -> None:
        """Loads configurations from the file system."""
        with open(join(dirname(dirname(__file__)), 'blender_manifest.toml'), "rb") as file:
            self.__manifest = tomllib.load(file)

        try:
            with open(self.__path, "rb") as file:
                self.__data = tomllib.load(file) # type: ignore
        except FileNotFoundError:
            self.write() # ファイルが存在しなければ作成する

    def write(self) -> None:
        with open(self.__path, "w", encoding="utf-8") as file:
            file.write(self.__data_to_toml())

    @property
    def data(self) -> Config.Items:
        """Returns configuration data in dictionary format."""
        return self.__data

    @property
    def manifest(self) -> Dict[str, Any]:
        """Returns the manifest data."""
        return self.__manifest

    def __data_to_toml(self) -> str:
        result: str = ""
        for key, value in self.__data.items():
            result += f"{key} = {str(value).lower()}\n"

        return result
