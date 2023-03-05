import typing as t


class ContextWrapper:
    """Used to wrap context objects copied as dictionary to simulate bpy.types.Context behavior.
    """

    def __init__(self, ctx_dct: dict) -> None:
        self._ctx: dict = ctx_dct

    def __getattr__(self, name: str) -> t.Any:
        if name == '_ctx':
            return object.__getattribute__(self, '_ctx')

        return self._ctx[name]

    def __getitem__(self, name: str) -> t.Any:
        if name == '_ctx':
            return object.__getattribute__(self, '_ctx')

        return self._ctx[name]

    def __setitem__(self, name: str, value: t.Any) -> None:
        if name == '_ctx':
            return object.__setattr__(self, '_ctx', value)

        self._ctx[name] = value

    def __setattr__(self, name: str, value: t.Any) -> None:
        if name == '_ctx':
            return object.__setattr__(self, '_ctx', value)

        self._ctx[name] = value