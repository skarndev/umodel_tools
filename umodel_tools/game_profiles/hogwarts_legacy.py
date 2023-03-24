"""This module implements support for Hogarts Legacy (2023) game.
Known issues:
    - Blended materials are not properly supported. Currently the first texture is used.
"""

import enum

import bpy
import lark


GAME_NAME = "Hogwarts Legacy"
GAME_DESCRIPTION = "Hogwarts Legacy (2023) by Portkey Games"


class TextureMapTypes(enum.Enum):
    """All texture map types supported by the material generator.
    """
    Diffuse = enum.auto()
    Normal = enum.auto()
    SRO = enum.auto()
    MROH = enum.auto()
    MRO = enum.auto()


#: Translates names retrieved from .props.txt into sensible texture map types
TEXTURE_PARAM_NAME_TRS = {
    "Diffuse": TextureMapTypes.Diffuse,
    "Normal": TextureMapTypes.Normal,
    "SRO": TextureMapTypes.SRO,
    "MRO": TextureMapTypes.MRO,
    "MROH": TextureMapTypes.MROH,
    "MROH/SROH": TextureMapTypes.MROH,
    "MRO/SRO": TextureMapTypes.MRO,

    "Diffuse Map": TextureMapTypes.Diffuse,
    "Normal Map": TextureMapTypes.Normal,
    "MRO/SRO Map": TextureMapTypes.SRO,
    "SRO Map": TextureMapTypes.SRO,
    "MROH Map": TextureMapTypes.MROH,
    "MROH/SROH Map": TextureMapTypes.MROH,
    "MRO Map": TextureMapTypes.MRO,

    "Diffuse A": TextureMapTypes.Diffuse,
    "Normal A": TextureMapTypes.Normal,
    "SRO A": TextureMapTypes.SRO,
    "MROH A": TextureMapTypes.MROH,
    "MROH/SROH A": TextureMapTypes.MROH,
    "MRO/SRO A": TextureMapTypes.MRO,
    "MRO A": TextureMapTypes.MROH,

    "Diffuse Map A": TextureMapTypes.Diffuse,
    "Normal Map A": TextureMapTypes.Normal,
    "SRO Map A": TextureMapTypes.SRO,
    "MROH Map A": TextureMapTypes.MROH,
    "MROH/SROH Map A": TextureMapTypes.MROH,
    "MRO/SRO Map A": TextureMapTypes.MRO,
    "MRO Map A": TextureMapTypes.MROH,

    "Diffuse A Map": TextureMapTypes.Diffuse,
    "Normal A Map": TextureMapTypes.Normal,
    "SRO A Map": TextureMapTypes.SRO,
    "MRO/SRO A Map": TextureMapTypes.SRO,
    "MROH A Map": TextureMapTypes.MROH,
    "MROH/SROH A Map": TextureMapTypes.MROH,
    "MRO A Map": TextureMapTypes.MROH,

    # Weird stuff goes here
    "Color Glass": TextureMapTypes.Diffuse,
    "Base color": TextureMapTypes.Diffuse,
    "Base Color": TextureMapTypes.Diffuse,
    "MROA": TextureMapTypes.MRO,  # TODO: A stands for what?,
    "Color Mask": TextureMapTypes.Diffuse,
    "Worn Diffuse": TextureMapTypes.Diffuse,
    "Worn Normal": TextureMapTypes.Normal,
    "Worn SRO": TextureMapTypes.SRO,
    "Worn MRO": TextureMapTypes.MRO,
    "Worn MROH": TextureMapTypes.MROH,
    "Worn MROH/SROH": TextureMapTypes.MROH,
    "Worn MRO/SRO": TextureMapTypes.MRO,
}

_state_buffer: dict[bpy.types.Material, tuple[bpy.types.ShaderNodeBsdfPrincipled | bpy.types.ShaderNodeBsdfDiffuse,
                                              bool]] = {}


def process_material(mat: bpy.types.Material, _: lark.Tree, use_pbr: bool):
    _state_buffer[mat] = None, use_pbr


def do_process_texture(tex_type: str) -> bool:
    return tex_type in TEXTURE_PARAM_NAME_TRS


def is_diffuse_tex_type(tex_type: str) -> bool:
    return TEXTURE_PARAM_NAME_TRS.get(tex_type) == TextureMapTypes.Diffuse


def handle_material_texture_pbr(mat: bpy.types.Material,
                                tex_type: str,
                                img_node: bpy.types.ShaderNodeTexImage,
                                ao_mix_node: bpy.types.ShaderNodeMix,
                                bsdf_node: bpy.types.ShaderNodeBsdfPrincipled,
                                out_node: bpy.types.ShaderNodeOutputMaterial):
    # Note: we presume MROH and SRO are mutually exclusive and never appear together.
    # This is not validated.
    _, use_pbr = _state_buffer[mat]
    _state_buffer[mat] = bsdf_node, use_pbr

    bl_tex_type = TEXTURE_PARAM_NAME_TRS.get(tex_type)
    assert bl_tex_type is not None

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
                                   _: str,
                                   img_node: bpy.types.ShaderNodeTexImage,
                                   bsdf_node: bpy.types.ShaderNodeBsdfDiffuse):
    _, use_pbr = _state_buffer[mat]
    _state_buffer[mat] = bsdf_node, use_pbr

    mat.node_tree.links.new(img_node.outputs['Color'], bsdf_node.inputs['Color'])
    img_node.select = True
    mat.node_tree.nodes.active = img_node


def end_process_material(mat: bpy.types.Material):
    bsdf, use_pbr = _state_buffer[mat]

    if use_pbr and bsdf is not None:
        # set defaults
        bsdf.inputs[4].default_value = 1.01  # Subsurface IOR
        bsdf.inputs[7].default_value = 0.0  # Specular
        bsdf.inputs[9].default_value = 0.0  # Roughness
        bsdf.inputs[13].default_value = 0.0  # Sheen Tint
        bsdf.inputs[15].default_value = 0.0  # Clearcoat roughness

    del _state_buffer[mat]
