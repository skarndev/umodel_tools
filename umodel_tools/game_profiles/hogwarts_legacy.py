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
    WEAR_MSK = enum.auto()


#: Translates names retrieved from .props.txt into sensible texture map types
TEXTURE_PARAM_NAME_TRS = {
    "diffuse": TextureMapTypes.Diffuse,
    "normal": TextureMapTypes.Normal,
    "sro": TextureMapTypes.SRO,
    "mro": TextureMapTypes.MRO,
    "mroh": TextureMapTypes.MROH,
    "mroh/sroh": TextureMapTypes.MROH,
    "mro/sro": TextureMapTypes.MRO,

    "diffuse map": TextureMapTypes.Diffuse,
    "normal map": TextureMapTypes.Normal,
    "mro/sro map": TextureMapTypes.SRO,
    "sro map": TextureMapTypes.SRO,
    "mroh map": TextureMapTypes.MROH,
    "mroh/sroh map": TextureMapTypes.MROH,
    "mro map": TextureMapTypes.MRO,

    "diffuse a": TextureMapTypes.Diffuse,
    "normal a": TextureMapTypes.Normal,
    "sro a": TextureMapTypes.SRO,
    "mroh a": TextureMapTypes.MROH,
    "mroh/sroh a": TextureMapTypes.MROH,
    "mro/sro a": TextureMapTypes.MRO,
    "mro a": TextureMapTypes.MROH,

    "diffuse map a": TextureMapTypes.Diffuse,
    "normal map a": TextureMapTypes.Normal,
    "sro map a": TextureMapTypes.SRO,
    "mroh map a": TextureMapTypes.MROH,
    "mroh/sroh map a": TextureMapTypes.MROH,
    "mro/sro map a": TextureMapTypes.MRO,
    "mro map a": TextureMapTypes.MROH,

    "diffuse a map": TextureMapTypes.Diffuse,
    "normal a map": TextureMapTypes.Normal,
    "sro a map": TextureMapTypes.SRO,
    "mro/sro a map": TextureMapTypes.SRO,
    "mroh a map": TextureMapTypes.MROH,
    "mroh/sroh a map": TextureMapTypes.MROH,
    "mro a map": TextureMapTypes.MROH,

    # Weird stuff goes here
    "color glass": TextureMapTypes.Diffuse,
    "base color": TextureMapTypes.Diffuse,
    "mroa": TextureMapTypes.MRO,  # TODO: A stands for what?,
    "color mask": TextureMapTypes.MSK,
    "wear mask": TextureMapTypes.WEAR_MSK,
    "worn diffuse": TextureMapTypes.Diffuse,
    "worn normal": TextureMapTypes.Normal,
    "worn sro": TextureMapTypes.SRO,
    "worn mro": TextureMapTypes.MRO,
    "worn mroh": TextureMapTypes.MROH,
    "worn mroh/sroh": TextureMapTypes.MROH,
    "worn mro/sro": TextureMapTypes.MRO,
    "window_surface_diffuse": TextureMapTypes.Diffuse,
    "window_surface_normal": TextureMapTypes.Normal,
    "window_surface_mro": TextureMapTypes.MRO,
    "window_surface_mroh": TextureMapTypes.MROH,
    "window_surface_sro": TextureMapTypes.SRO
}

@dataclasses.dataclass
class MaterialContext:
    bsdf_node: t.Optional[bpy.types.ShaderNodeBsdfPrincipled | bpy.types.ShaderNodeBsdfDiffuse]
    desc_ast: lark.Tree
    use_pbr: bool
    msk_index: int = dataclasses.field(default=0)
    diffuse_connected: bool = dataclasses.field(default=False)
    linked_maps: set[TextureMapTypes.Diffuse] = dataclasses.field(default_factory=set)


_state_buffer: dict[bpy.types.Material, MaterialContext] = {}


def process_material(mat: bpy.types.Material, desc_ast: lark.Tree, use_pbr: bool):  # pylint: disable=unused-argument
    _state_buffer[mat] = MaterialContext(bsdf_node=None, desc_ast=desc_ast, use_pbr=use_pbr)


def do_process_texture(tex_type: str, tex_short_name: str) -> bool:  # pylint: disable=unused-argument
    return tex_type.lower() in TEXTURE_PARAM_NAME_TRS


def is_diffuse_tex_type(tex_type: str, tex_short_name: str) -> bool:  # pylint: disable=unused-argument
    return TEXTURE_PARAM_NAME_TRS.get(tex_type.lower()) in {TextureMapTypes.Diffuse, TextureMapTypes.MSK}


def handle_material_texture_pbr(mat: bpy.types.Material,
                                tex_type: str,
                                tex_short_name: str,  # pylint: disable=unused-argument
                                img_node: bpy.types.ShaderNodeTexImage,
                                ao_mix_node: bpy.types.ShaderNodeMix,
                                bsdf_node: bpy.types.ShaderNodeBsdfPrincipled,
                                out_node: bpy.types.ShaderNodeOutputMaterial):
    # Note: we presume MROH and SRO are mutually exclusive and never appear together.
    # This is not validated.
    mat_ctx = _state_buffer[mat]
    mat_ctx.bsdf_node = bsdf_node

    bl_tex_type = TEXTURE_PARAM_NAME_TRS.get(tex_type.lower())

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
            mat_ctx.diffuse_connected = True

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

        case TextureMapTypes.WEAR_MSK:
            mat_ctx.msk_index += 1

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

            if not mat_ctx.diffuse_connected:
                mat.node_tree.links.new(r_mix.outputs[2], ao_mix_node.inputs[6])
                mat.node_tree.links.new(img_node.outputs['Alpha'], bsdf_node.inputs['Alpha'])
                img_node.select = True
                mat.node_tree.nodes.active = img_node

            mat_ctx.msk_index += 1


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
