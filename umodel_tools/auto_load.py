import typing
import inspect
import pkgutil
import importlib
from pathlib import Path
from ordered_set import OrderedSet

import bpy


__all__ = (
    "init",
    "register",
    "unregister",
)

MODULES_TO_IGNORE = (
    "third_party",
    "test"
)

modules = None
ordered_classes = None


def init():
    # pylint: disable=global-statement

    global modules
    global ordered_classes

    modules = get_all_submodules(Path(__file__).parent)
    ordered_classes = get_ordered_classes_to_register(modules)


def register():
    for cls in ordered_classes:
        bpy.utils.register_class(cls)

    for module in modules:

        if module.__name__ == __name__:
            continue

        if hasattr(module, "bl_register"):
            module.bl_register()


def unregister():
    for cls in reversed(ordered_classes):
        bpy.utils.unregister_class(cls)

    for module in modules:
        if module.__name__ == __name__:
            continue

        if hasattr(module, "bl_unregister"):
            module.bl_unregister()


# Import modules
#################################################

def get_all_submodules(directory):
    return list(iter_submodules(directory, directory.name))


def iter_submodules(path, package_name):
    for name in sorted(iter_submodule_names(path)):
        yield importlib.import_module("." + name, package_name)


def iter_submodule_names(path, root=""):
    for _, module_name, is_package in pkgutil.iter_modules([str(path)]):

        if module_name in MODULES_TO_IGNORE:
            continue

        if is_package:
            sub_path = path / module_name
            sub_root = root + module_name + "."
            yield from iter_submodule_names(sub_path, sub_root)
        else:
            yield root + module_name


# Find classes to register
#################################################

def get_ordered_classes_to_register(py_modules):
    return toposort(get_register_deps_dict(py_modules))


def get_register_deps_dict(py_modules):
    deps_dict = {}
    classes_to_register = OrderedSet(iter_classes_to_register(py_modules))
    for cls in classes_to_register:
        deps_dict[cls] = OrderedSet(iter_own_register_deps(cls, classes_to_register))
    return deps_dict


def iter_own_register_deps(cls, own_classes):
    yield from (dep for dep in iter_register_deps(cls) if dep in own_classes)


def iter_register_deps(cls):
    for value in typing.get_type_hints(cls, {}, {}).values():
        dependency = get_dependency_from_annotation(value)
        if dependency is not None:
            yield dependency


def get_dependency_from_annotation(value):
    if isinstance(value, tuple) and len(value) == 2:
        if value[0] in (bpy.props.PointerProperty, bpy.props.CollectionProperty):
            return value[1]["type"]
    return None


def iter_classes_to_register(py_modules):
    base_types = get_register_base_types()
    for cls in get_classes_in_modules(py_modules):
        if any(base in base_types for base in cls.__bases__):
            yield cls


def get_classes_in_modules(py_modules):
    classes = OrderedSet()
    for module in py_modules:
        for cls in iter_classes_in_module(module):
            classes.add(cls)
    return classes


def iter_classes_in_module(module):
    for value in module.__dict__.values():
        if inspect.isclass(value):
            yield value


def get_register_base_types():
    return OrderedSet(getattr(bpy.types, name) for name in [
        "Panel", "Operator", "PropertyGroup",
        "AddonPreferences", "Header", "Menu",
        "Node", "NodeSocket", "NodeTree",
        "UIList"
    ])


# Find order to register to solve dependencies
#################################################

def toposort(deps_dict):
    sorted_list = []
    sorted_values = OrderedSet()
    while len(deps_dict) > 0:
        unsorted = []
        for value, deps in deps_dict.items():
            if len(deps) == 0:
                sorted_list.append(value)
                sorted_values.add(value)
            else:
                unsorted.append(value)
        deps_dict = {value: deps_dict[value] - sorted_values for value in unsorted}
    return sorted_list
