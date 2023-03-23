"""This module holds configuration for the supported games.
   Each supported game must define its own material handling code.
   In order to add a game, enter its name in the following list and implement
   a material generation specifics module using the provided name.
   Nothing else should be needed to support a game.

   The format is: ``('module_name', "Game Name for UI", "Game description for UI", number)``
   The module must implement the ``GameHandler`` protocol.
"""
import os
import importlib
import traceback
import typing as t

import bpy
import lark


@t.runtime_checkable
class GameHandler(t.Protocol):
    """Modules adding support for specific games must implement this protocol.
    """

    def process_material(mat: bpy.types.Material, desc_ast: lark.Tree, use_pbr: bool) -> None:
        """Does all sorts of unspecified processing on the material prior to texture imports.

        :param mat: Blender material we are processing.
        :desc_ast: Lark AST tree representing the corresponding material descriptor. Can be used to obtain
        any additional information required to implement game specifics.
        :use_pbr: True if material is imported in a PBR mode.
        """
        ...

    def do_process_texture(tex_type: str) -> bool:
        """Determines whether to process the texture or not.

        :param tex_type: Texture type string retrieved from .props.txt.
        :return: True if should process, False if should discard.
        """
        ...

    def is_diffuse_tex_type(tex_type: str) -> bool:
        """Identifies if the texture is a diffuse color map.
        Used for special logic.

        :param tex_type: Texture type string retrieved from .props.txt.
        :return: True if texture is a diffuse map, else False.
        """
        ...

    def handle_material_texture_pbr(mat: bpy.types.Material,
                                    tex_type: str,
                                    img_node: bpy.types.ShaderNodeTexImage,
                                    ao_mix_node: bpy.types.ShaderNodeMix,
                                    bsdf_node: bpy.types.ShaderNodeBsdfPrincipled,
                                    out_node: bpy.types.ShaderNodeOutputMaterial) -> None:
        """Handles adding texture maps to a PBR material.

        :param mat: Currently processed material.
        :param tex_type: Current texture type.
        :param img_node: Image node in the material's node tree.
        :param ao_mix_node: Ambient Occlusion mixing node in the material's node tree.
        :param bsdf_node: PrincipledBSDF node in the material's node tree.
        :param out_node: Material output node in the material's node tree.
        """
        ...

    def handle_material_texture_simple(mat: bpy.types.Material,
                                       tex_type: str,
                                       img_node: bpy.types.ShaderNodeTexImage,
                                       bsdf_node: bpy.types.ShaderNodeBsdfDiffuse) -> None:
        """Handles adding texture maps to a simplified material. Only diffuse maps will be processed by this
        function.

        :param mat: Currently processed material.
        :param tex_type: Current texture type.
        :param img_node: Image node in the material's node tree.
        :param bsdf_node: DiffuseBSDF node in the material's node tree.
        """
        ...

    def end_process_material(mat: bpy.types.Material) -> None:
        """Called at the end of the material processing, can be used to cleanup state (if any is kept).

        :param: mat: Material that was processed.
        """
        ...


#: List of all game profiles supported by the addon.
SUPPORTED_GAMES: list[tuple[str, str, str, int]] = [
    ('hogwarts_legacy', "Hogwarts Legacy", "Hogwarts Legacy (2023) by Portkey Games", 0),
]


#: List of all implemented game handlers (populated automatically).
GAME_HANDLERS: dict[str, GameHandler] = {}
for element in os.listdir(profile_path := os.path.dirname(__file__)):
    if not os.path.isfile(os.path.join(profile_path, element)) or not element.endswith('.py') or element == "__init__.py":
        continue

    impl_name = os.path.splitext(element)[0]
    found, impl_index = next(((True, i) for i, x in enumerate(SUPPORTED_GAMES) if x[0] == impl_name), (None, -1))

    if found is None:
        print(f"Game handler \"{impl_name}.py\" was found, but is not listed among the supported games. "
              "Forgot to add it to the config?")
        continue

    try:
        game_profile = importlib.import_module(f'.{impl_name}', package='umodel_tools.game_profiles')

        if not isinstance(game_profile, GameHandler):
            print(f"Error: handler \"{impl_name}.py\" does not satisfy the GameHandler protocol.")
            continue

        GAME_HANDLERS[impl_name] = game_profile

    except ImportError:
        print(f"Error: handler \"{impl_name}.py\" for the game \"{SUPPORTED_GAMES[impl_index][1]}\" failed importing.")
        traceback.print_exc()


__all__ = (
    'SUPPORTED_GAMES',
    'GAME_HANDLERS',
    'GameHandler'
)
