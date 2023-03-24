"""This module implements support for Hogarts Legacy (2023) game.
Known issues:
    - Blended materials are not properly supported. Currently the first texture is used.
"""

import enum
import typing as t
import dataclasses

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
    MSK = enum.auto()


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
    "Color Mask": TextureMapTypes.MSK,
    "Worn Diffuse": TextureMapTypes.Diffuse,
    "Worn Normal": TextureMapTypes.Normal,
    "Worn SRO": TextureMapTypes.SRO,
    "Worn MRO": TextureMapTypes.MRO,
    "Worn MROH": TextureMapTypes.MROH,
    "Worn MROH/SROH": TextureMapTypes.MROH,
    "Worn MRO/SRO": TextureMapTypes.MRO,
}


@dataclasses.dataclass
class MaterialContext:
    bsdf_node: t.Optional[bpy.types.ShaderNodeBsdfPrincipled | bpy.types.ShaderNodeBsdfDiffuse]
    desc_ast: lark.Tree
    use_pbr: bool
    msk_index: int = dataclasses.field(default=0)


_state_buffer: dict[bpy.types.Material, MaterialContext] = {}


def process_material(mat: bpy.types.Material, desc_ast: lark.Tree, use_pbr: bool):  # pylint: disable=unused-argument
    _state_buffer[mat] = MaterialContext(bsdf_node=None, desc_ast=desc_ast, use_pbr=use_pbr)


def do_process_texture(tex_type: str) -> bool:
    return tex_type in TEXTURE_PARAM_NAME_TRS


def is_diffuse_tex_type(tex_type: str) -> bool:
    return TEXTURE_PARAM_NAME_TRS.get(tex_type) in {TextureMapTypes.Diffuse, TextureMapTypes.MSK}


def handle_material_texture_pbr(mat: bpy.types.Material,
                                tex_type: str,
                                img_node: bpy.types.ShaderNodeTexImage,
                                ao_mix_node: bpy.types.ShaderNodeMix,
                                bsdf_node: bpy.types.ShaderNodeBsdfPrincipled,
                                out_node: bpy.types.ShaderNodeOutputMaterial):
    # Note: we presume MROH and SRO are mutually exclusive and never appear together.
    # This is not validated.
    mat_ctx = _state_buffer[mat]
    mat_ctx.bsdf_node = bsdf_node

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

        case TextureMapTypes.MSK:
            mat_ctx = _state_buffer[mat]
            mask_colors = _get_mask_colors(ast=mat_ctx.desc_ast)

            color1 = mask_colors.get(f'color {mat_ctx.msk_index + 1}')
            color2 = mask_colors.get(f'color {mat_ctx.msk_index + 2}')
            color3 = mask_colors.get(f'color {mat_ctx.msk_index + 3}')

            msk_split = mat.node_tree.nodes.new('ShaderNodeSeparateColor')

            b_mix = mat.node_tree.nodes.new('ShaderNodeMix')
            b_mix.data_type = 'RGBA'
            b_mix.blend_type = 'MIX'
            b_mix.inputs[6].default_value = color1 if color1 is not None else (0, 0, 1, 1)
            b_mix.inputs[7].default_value = (0, 0, 0, 1)

            g_mix = mat.node_tree.nodes.new('ShaderNodeMix')
            g_mix.data_type = 'RGBA'
            g_mix.blend_type = 'MIX'
            g_mix.inputs[7].default_value = color2 if color2 is not None else (0, 1, 0, 1)

            r_mix = mat.node_tree.nodes.new('ShaderNodeMix')
            r_mix.data_type = 'RGBA'
            r_mix.blend_type = 'MIX'
            r_mix.inputs[7].default_value = color3 if color3 is not None else (1, 0, 0, 1)

            mat.node_tree.links.new(img_node.outputs['Color'], msk_split.inputs['Color'])
            mat.node_tree.links.new(msk_split.outputs['Red'], r_mix.inputs[0])
            mat.node_tree.links.new(msk_split.outputs['Green'], g_mix.inputs[0])
            mat.node_tree.links.new(msk_split.outputs['Blue'], b_mix.inputs[0])

            # connect mix nodes
            mat.node_tree.links.new(b_mix.outputs[2], g_mix.inputs[6])
            mat.node_tree.links.new(g_mix.outputs[2], r_mix.inputs[6])
            mat.node_tree.links.new(r_mix.outputs[2], ao_mix_node.inputs[6])
            mat.node_tree.links.new(img_node.outputs['Alpha'], bsdf_node.inputs['Alpha'])
            img_node.select = True
            mat.node_tree.nodes.active = img_node

            mat_ctx.msk_index += 1


def handle_material_texture_simple(mat: bpy.types.Material,
                                   _: str,
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


Color: t.TypeAlias = tuple[float, float, float]


def _get_mask_colors(ast: lark.Tree) -> dict[str, Color]:
    """Get MSK colors from texture parameters.

    :param ast: .props.txt AST
    :return: dictionary mapping color names to values.
    """

    colors = {}

    for child in ast.children:
        assert child.data == 'definition'
        def_name, array_qual, value = child.children

        match def_name:
            case 'VectorParameterValues':
                assert array_qual is not None
                assert value.data == 'structured_block'

                for tex_param_def in value.children:
                    _, _, tex_param = tex_param_def.children
                    param_info, param_val, _ = tex_param.children  # ParameterInfo, ParameterValue, ParameterName
                    _, _, color_vec = param_val.children

                    color_name = param_info.children[2].children[0].children[2].children[0].value.strip()

                    # ignore unused materials
                    if color_vec.data != 'structured_block':
                        continue

                    color = {
                        'r': 0.0,
                        'g': 0.0,
                        'b': 0.0,
                        'a': 1.0
                    }

                    not_a_color = False
                    for channel_def in color_vec.children:
                        channel_name, _, channel = channel_def.children
                        channel_name = channel_name.lower()

                        if channel_name not in {'r', 'g', 'b', 'a'}:
                            not_a_color = True
                            continue

                        color[channel_name] = float(channel.children[0].value)

                    if not_a_color:
                        continue

                    colors[color_name.lower()] = (color['r'], color['g'], color['b'], color['a'])

    return colors
