import typing as t

import bpy


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


def copy_object(obj: bpy.types.Object) -> bpy.types.Object:
    """Copies an object and its mesh. No linking is performed.

    :param obj: Blender object.
    :return: Copied object.
    """
    copied_obj = obj.copy()
    copied_obj.data = obj.data.copy()
    return copied_obj


def compare_meshes(first: bpy.types.Mesh, second: bpy.types.Mesh) -> bool:
    """Compare two meshes on basic geometric similarity.

    :param first: First mesh.
    :param second: Second mesh.
    :return: Returns True if number of vertices, edges, faces and loops is equal.
    """

    return (len(first.vertices) == len(second.vertices)
            and len(first.polygons) == len(second.polygons)
            and len(first.loops) == len(second.loops)
            and len(first.edges) == len(second.edges))
