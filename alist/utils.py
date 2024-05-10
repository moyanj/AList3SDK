from typing import Union


class ToClass:
    def __init__(self, conf: dict):
        self._conf_Dict = conf
        self.__name__ = "<Standard Dictionary>"
        self.update()

    def __getattr__(self, name):
        if name in self._conf_Dict:
            return self._conf_Dict[name]
        else:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

    def update(self, conf: Union[dict, None] = None):
        if conf:
            self._conf_Dict = conf
        # 更新字典
        for k, v in self._conf_Dict.items():
            if isinstance(v, dict):
                setattr(self, k, ToClass(v))
            elif isinstance(v, list):
                setattr(
                    self,
                    k,
                    [ToClass(item) if isinstance(item, dict) else item for item in v],
                )
            else:
                setattr(self, k, v)

    def __str__(self):
        return str(self._conf_Dict)
