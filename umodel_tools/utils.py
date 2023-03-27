import os
import sys
import typing as t
import tempfile
import contextlib

import bpy
import tqdm

from . import preferences


tmphandle, tmppath = tempfile.mkstemp()
#: Determines whether the OS's filesystem is case sensitive or not
FS_CASE_INSENSITIVE = os.path.exists(tmppath.upper())
os.close(tmphandle)
os.remove(tmppath)


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


def compare_paths(first: str, second: str) -> bool:
    """Compares that to paths are identical. Respects OS case sensitivity rules for the filesystem.

    :param first: First path.
    :param second: Second path.
    :return: True if paths are identical, else False.
    """
    first = os.path.realpath(first)
    second = os.path.realpath(second)

    return (first.lower() == second.lower()) if FS_CASE_INSENSITIVE else (first == second)


DataBlock: t.TypeAlias = bpy.types.Object | bpy.types.Material | bpy.types.Image


def linked_libraries_search(lib_filepath: str, dtype: t.Type[DataBlock]) -> t.Optional[DataBlock]:
    """Check already linked libraries for the associated data block and return it.

    :param lib_filepath: Filepath of the library.
    :param dtype: Datablock type.
    :return: None or data-block (if found).
    """

    for lib in bpy.data.libraries:
        if compare_paths(lib.filepath, lib_filepath):
            for id_data in lib.users_id:
                if isinstance(id_data, dtype):
                    return id_data

    return None


def verbose_print(*args: t.Any):
    """Prints to stdout, if addon has verbose setting enabled.

    :args: Arguments to internal print() call.
    """
    if preferences.get_addon_preferences().verbose:
        print(*args)


@contextlib.contextmanager
def std_out_err_redirect_tqdm():
    """Redirect stdout and stderr for tqdm.
    """
    orig_out_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = map(tqdm.contrib.DummyTqdmFile, orig_out_err)
        yield orig_out_err[0]
    # Relay exceptions
    except Exception as exc:
        raise exc
    # Always restore sys.stdout/err if necessary
    finally:
        sys.stdout, sys.stderr = orig_out_err


@contextlib.contextmanager
def redirect_cstdout(to=os.devnull):
    """Redirect stdout from C/C++ parts of Blender and external libaries.
    We use this to suppress library reading and linking messages.

    :param to: _description_, defaults to os.devnull
    :yield: _description_
    """

    # disable the whole redirect in debug mode
    if preferences.get_addon_preferences().debug:
        yield
        return None

    fd = sys.stdout.fileno()

    def _redirect_stdout(to):
        os.dup2(to.fileno(), fd)  # fd writes to 'to' file

    with os.fdopen(os.dup(fd), 'w') as old_stdout:
        with open(to, 'w') as file:  # pylint: disable=unspecified-encoding
            _redirect_stdout(to=file)
        try:
            yield  # allow code to be run with the redirected stdout
        finally:
            _redirect_stdout(to=old_stdout)  # restore stdout

    return None
