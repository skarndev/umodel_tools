"""This module implements a generic algorithm to provide basic support to the majority of UE games.
"""

import enum
import typing as t
import dataclasses

import bpy
import lark


GAME_NAME = "Generic"
GAME_DESCRIPTION = "Provides basic support for any Unreal Engine game"


class TextureMapTypes(enum.Enum):
    """All texture map types supported by the material generator.
    """
    Diffuse = enum.auto()
    Normal = enum.auto()
    SRO = enum.auto()
    MROH = enum.auto()
    MRO = enum.auto()


#: Suffixes of textures for automatic texture purpose guessing (lowercase only)
SUFFIX_MAP = {
    'd': TextureMapTypes.Diffuse,
    'n': TextureMapTypes.Normal,
    'mro': TextureMapTypes.MRO,
    'sro': TextureMapTypes.SRO,
    'mroh': TextureMapTypes.MROH,
    'mroa': TextureMapTypes.MRO,  # TODO: figure out what MROA means.
    'sroh': TextureMapTypes.MROH,  # TODO: verify, just in case, if SROH is actually a thing.
}


@dataclasses.dataclass
class MaterialContext:
    bsdf_node: t.Optional[bpy.types.ShaderNodeBsdfPrincipled | bpy.types.ShaderNodeBsdfDiffuse]
    desc_ast: lark.Tree
    use_pbr: bool
    linked_maps: set[TextureMapTypes.Diffuse] = dataclasses.field(default_factory=set)


_state_buffer: dict[bpy.types.Material, MaterialContext] = {}


def process_material(mat: bpy.types.Material, desc_ast: lark.Tree, use_pbr: bool):  # pylint: disable=unused-argument
    _state_buffer[mat] = MaterialContext(bsdf_node=None, desc_ast=desc_ast, use_pbr=use_pbr)


def do_process_texture(tex_type: str, tex_short_name: str) -> bool:  # pylint: disable=unused-argument
    return bool(_short_name_to_tex_type(tex_short_name))


def is_diffuse_tex_type(tex_type: str, tex_short_name: str) -> bool:  # pylint: disable=unused-argument
    return _short_name_to_tex_type(tex_short_name) == TextureMapTypes.Diffuse


def handle_material_texture_pbr(mat: bpy.types.Material,
                                tex_type: str,  # pylint: disable=unused-argument
                                tex_short_name: str,
                                img_node: bpy.types.ShaderNodeTexImage,
                                ao_mix_node: bpy.types.ShaderNodeMix,
                                bsdf_node: bpy.types.ShaderNodeBsdfPrincipled,
                                out_node: bpy.types.ShaderNodeOutputMaterial):
    # Note: we presume MROH and SRO are mutually exclusive and never appear together.
    # This is not validated.
    mat_ctx = _state_buffer[mat]
    mat_ctx.bsdf_node = bsdf_node

    bl_tex_type = _short_name_to_tex_type(tex_short_name)

    # do not connect the same texture twice
    if bl_tex_type in mat_ctx.linked_maps:
        return

    # remember that we processed a texture of that type
    mat_ctx.linked_maps.add(bl_tex_type)

    match bl_tex_type:
        case TextureMapTypes.Diffuse:
            mat.node_tree.links.new(img_node.outputs['Color'], ao_mix_node.inputs[6])
            mat.node_tree.links.new(img_node.outputs['Alpha'], bsdf_node.inputs['Alpha'])
            img_node.select = True
            mat.node_tree.nodes.active = img_node

        case TextureMapTypes.Normal:
            normal_map_node = mat.node_tree.nodes.new('ShaderNodeNormalMap')
            mat.node_tree.links.new(normal_map_node.outputs['Normal'],
                                    bsdf_node.inputs['Normal'])
            mat.node_tree.links.new(img_node.outputs['Color'],
                                    normal_map_node.inputs['Color'])
        case TextureMapTypes.SRO:
            sro_split = mat.node_tree.nodes.new('ShaderNodeSeparateColor')
            mat.node_tree.links.new(sro_split.outputs['Red'], bsdf_node.inputs['Specular'])
            mat.node_tree.links.new(sro_split.outputs['Green'], bsdf_node.inputs['Roughness'])
            mat.node_tree.links.new(sro_split.outputs['Blue'], ao_mix_node.inputs[7])
            mat.node_tree.links.new(img_node.outputs['Color'], sro_split.inputs['Color'])
        case TextureMapTypes.MROH:
            # MRO components
            mroh_split = mat.node_tree.nodes.new('ShaderNodeSeparateColor')
            mat.node_tree.links.new(mroh_split.outputs['Red'], bsdf_node.inputs['Metallic'])
            mat.node_tree.links.new(mroh_split.outputs['Green'], bsdf_node.inputs['Roughness'])
            mat.node_tree.links.new(mroh_split.outputs['Blue'], ao_mix_node.inputs[7])
            mat.node_tree.links.new(img_node.outputs['Color'], mroh_split.inputs['Color'])

            # height component
            displacement_node = mat.node_tree.nodes.new('ShaderNodeDisplacement')
            mat.node_tree.links.new(displacement_node.outputs['Displacement'],
                                    out_node.inputs['Displacement'])
            mat.node_tree.links.new(img_node.outputs['Alpha'],
                                    displacement_node.inputs['Height'])
        case TextureMapTypes.MRO:
            mro_split = mat.node_tree.nodes.new('ShaderNodeSeparateColor')
            mat.node_tree.links.new(mro_split.outputs['Red'], bsdf_node.inputs['Metallic'])
            mat.node_tree.links.new(mro_split.outputs['Green'], bsdf_node.inputs['Roughness'])
            mat.node_tree.links.new(mro_split.outputs['Blue'], ao_mix_node.inputs[7])
            mat.node_tree.links.new(img_node.outputs['Color'], mro_split.inputs['Color'])


def handle_material_texture_simple(mat: bpy.types.Material,
                                   tex_type: str,  # pylint: disable=unused-argument
                                   tex_short_name: str,  # pylint: disable=unused-argument
                                   img_node: bpy.types.ShaderNodeTexImage,
                                   bsdf_node: bpy.types.ShaderNodeBsdfDiffuse):
    _state_buffer[mat].bsdf_node = bsdf_node

    mat.node_tree.links.new(img_node.outputs['Color'], bsdf_node.inputs['Color'])
    img_node.select = True
    mat.node_tree.nodes.active = img_node


def end_process_material(mat: bpy.types.Material):
    mat_ctx = _state_buffer[mat]

    if mat_ctx.use_pbr and mat_ctx.bsdf_node is not None:
        # set defaults
        mat_ctx.bsdf_node.inputs[4].default_value = 1.01  # Subsurface IOR
        mat_ctx.bsdf_node.inputs[7].default_value = 0.0  # Specular
        mat_ctx.bsdf_node.inputs[9].default_value = 0.0  # Roughness
        mat_ctx.bsdf_node.inputs[13].default_value = 0.0  # Sheen Tint
        mat_ctx.bsdf_node.inputs[15].default_value = 0.0  # Clearcoat roughness

    del _state_buffer[mat]


# Non-interface functions below

def _short_name_to_tex_type(tex_short_name: str) -> t.Optional[TextureMapTypes]:
    """Convert short texture name to a recognized texture map type if possible.

    :return: TextureMapType or None.
    """
    return SUFFIX_MAP.get(tex_short_name.lower().split('_')[-1])
