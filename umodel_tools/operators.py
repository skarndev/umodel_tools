import enum
import sys
import typing as t
import os
import shutil
import traceback
import numpy as np
import mathutils as mu

from io_import_scene_unreal_psa_psk_280 import pskimport
import bpy

from . import utils
from . import asset_db
from . import props_txt_parser


class TextureMapTypes(enum.Enum):
    """All texture map types supported by the material generator.
    """

    Diffuse = enum.auto()
    Normal = enum.auto()
    SRO = enum.auto()
    MROH = enum.auto()
    MRO = enum.auto()


class SpecialBlendingMode(enum.Enum):
    """List of special blenbing modes that require additional node generation.
    """

    #: Final color = Source color + Dest color.
    Add = enum.auto()

    #: Final color = Source color x Dest color.
    Mod = enum.auto()


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
    "MRO/SRO Map": TextureMapTypes.MRO,
    "MRO Map": TextureMapTypes.MRO,

    "Diffuse A": TextureMapTypes.Diffuse,
    "Normal A": TextureMapTypes.Normal,
    "SRO A": TextureMapTypes.SRO,
    "MRO/SRO A": TextureMapTypes.SRO,
    "MROH A": TextureMapTypes.MROH,
    "MROH/SROH A": TextureMapTypes.MROH,
    "MRO/SRO A": TextureMapTypes.MRO,
    "MRO A": TextureMapTypes.MROH,

    "Diffuse Map A": TextureMapTypes.Diffuse,
    "Normal Map A": TextureMapTypes.Normal,
    "SRO Map A": TextureMapTypes.SRO,
    "MRO/SRO Map A": TextureMapTypes.SRO,
    "MROH Map A": TextureMapTypes.MROH,
    "MROH/SROH Map A": TextureMapTypes.MROH,
    "MRO/SRO Map A": TextureMapTypes.MRO,
    "MRO Map A": TextureMapTypes.MROH
}


def _get_object_aabb_verts(obj: bpy.types.Object) -> list[tuple[float, float, float]]:
    return [obj.matrix_world @ mu.Vector(corner) for corner in obj.bound_box]


class UMODELTOOLS_OT_recover_unreal_asset(bpy.types.Operator):
    bl_idname = "umodel_tools.recover_unreal_asset"
    bl_label = "Recover Unreal Asset"
    bl_description = "Replaces selected object with an Unreal Engine asset from UModel dir, or attempts " \
                     "to transfer data to it, such as UV maps and materials"
    bl_options = {'REGISTER', 'UNDO'}

    asset_path: bpy.props.StringProperty(
        name="Asset path",
        description="Path to an alleged asset within the game"
    )

    load_pbr_maps: bpy.props.BoolProperty(
        name="Load PBR textures",
        description="Load normal maps, specular, roughness, etc into materials. Experimental",
        default=False
    )

    import_backface_culling: bpy.props.BoolProperty(
        name="Use backface culling",
        description="If this setting is checked, material settings for backface culling will be kept, "
                    "otherwise backface culling is always off",
        default=False
    )

    texture_format: bpy.props.EnumProperty(
        name="Texture format",
        description="Format of textures expected to be in the UModel export directory.",
        items=[
            ('.png', '.png', '', 0),
            ('.dds', '.dds', '', 0),
            ('.tga', '.tga', '', 0)
        ],
        default='.png'
    )

    def _op_message(self, type: t.Literal['INFO'] | t.Literal['ERROR'] | t.Literal['WARNING'], msg: str):
        """Print operator message and return the associated status-code.

        :param type: Type of message.
        :param msg: Message text.
        :raises NotImplementedError: Raise when an incorrect ``type`` is passed.
        :return: Blender operator error code.
        """
        self.report(type={type, }, message=msg)
        match type:
            case 'INFO':
                return {'FINISHED'}
            case 'ERROR':
                return {'CANCELLED'}
            case 'WARNING':
                return {'FINISHED'}
            case _:
                raise NotImplementedError()

    def _load_asset(self,
                    context: bpy.types.Context,
                    asset_dir: str,
                    asset_path: str,
                    umodel_export_dir: str
                    ) -> bpy.types.Object | None:
        """Loads the asset from library dir, or adds it to library and loads it.

        :param context: Current Blender context.
        :param asset_dir: Asset library directory.
        :param asset_path: Asset path in game format.
        :param umodel_export_dir: UModel output directory.
        :return: Object reference or None (if object was not found or failed loading due to filesystem errors).
        """
        asset_path_abs_no_ext = os.path.join(asset_dir, os.path.splitext(asset_path)[0])
        asset_path_abs = asset_path_abs_no_ext + '.blend'

        try:
            if not os.path.isfile(asset_path_abs):
                self._import_asset_to_library(context=context, asset_library_dir=asset_dir, asset_path=asset_path,
                                              umodel_export_dir=umodel_export_dir)

            with bpy.data.libraries.load(asset_path_abs, link=True) as (data_from, data_to):
                data_to.objects = [obj for obj in data_from.objects]
                assert len(data_to.objects) == 1

            return data_to.objects[0]

        except RuntimeError as e:
            traceback.print_exc()
            return None

    def _import_image_to_library(self, tex_path: str, tex_lib_path: str, tex_umodel_path: str, db: asset_db.AssetDB):
        """Import image texture to asset library from UModel output.

        :param tex_path: Path to texture in game format.
        :param tex_lib_path: Path to texture in the library dir (absolute).
        :param tex_umodel_path: Path to texture in the UModel output dir (absolute).
        """
        # copy file to library dir
        os.makedirs(os.path.dirname(tex_lib_path), exist_ok=True)
        shutil.copyfile(tex_umodel_path, tex_lib_path)

        img = bpy.data.images.load(filepath=tex_lib_path)
        img.asset_mark()
        img.asset_data.catalog_id = db.uid_for_entry(os.path.dirname(tex_path))
        # img.asset_generate_preview()

        tex_lib_blend_path = os.path.splitext(tex_lib_path)[0] + '.blend'

        # write texture library
        bpy.data.libraries.write(tex_lib_blend_path, {img, }, fake_user=True, compress=True)

        # remove original datablock
        bpy.data.images.remove(img, do_unlink=True)

    def _import_material_to_library(self,
                                    material_name: str,
                                    material_path_local: str,
                                    db: asset_db.AssetDB,
                                    umodel_export_dir: str,
                                    asset_library_dir: str
                                    ) -> None:
        """Import material to asset library from UModel output.

        :param material_name: Short name of material.
        :param material_path_local: Path to material properties (.props.txt) in game format.
        :param db: Blender AssetDB.
        :param umodel_export_dir: UModel export directory.
        :param asset_library_dir: Asset library directory.
        :raises OSError: Raised when material properties (.props.txt) file was not found or failed to open.
        """
        material_path_local_no_ext = os.path.splitext(os.path.splitext(material_path_local)[0])[0]  # remove .props.txt

        # load texture infos, may throw OSError if file is not found.
        texture_infos, base_prop_overrides = props_txt_parser.parse_props_txt(os.path.join(umodel_export_dir,
                                                                              material_path_local),
                                                                              mode='MATERIAL')

        new_mat = bpy.data.materials.new(material_name)
        new_mat.asset_mark()
        new_mat.asset_data.catalog_id = db.uid_for_entry(material_path_local_no_ext)
        new_mat.use_nodes = True
        new_mat.node_tree.links.clear()
        new_mat.node_tree.nodes.clear()

        out = new_mat.node_tree.nodes.new('ShaderNodeOutputMaterial')

        if self.load_pbr_maps:
            special_blend_mode = None

            # set various material parameters
            if base_prop_overrides is not None:

                if (blend_mode := base_prop_overrides.get('BlendMode')) is not None:
                    match blend_mode:
                        case 'BLEND_Opaque':
                            pass
                        case 'BLEND_Additive':
                            special_blend_mode = SpecialBlendingMode.Add
                            new_mat.blend_method = 'BLEND'
                        case 'BLEND_Translucent':
                            new_mat.blend_method = 'BLEND'
                        case 'BLEND_Modulate':
                            special_blend_mode = SpecialBlendingMode.Mod
                            new_mat.blend_method = 'BLEND'
                        case 'BLEND_Masked':
                            new_mat.blend_method = 'CLIP'
                        case _:
                            self._op_message('WARNING', f"Unknown blending mode \'{blend_mode}\' found on importing "
                                                        f"material \"{material_name}\".")

                if self.import_backface_culling and (two_sided := base_prop_overrides.get('TwoSided')) is not None:
                    new_mat.use_backface_culling = False if two_sided else True

                if (alpha_threshold := base_prop_overrides.get('OpacityMaskClipValue')) is not None:
                    new_mat.alpha_threshold = alpha_threshold

            elif self.import_backface_culling:
                new_mat.use_backface_culling = True

            # create basic shader nodes and set their default values

            bsdf = new_mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
            # set defaults
            bsdf.inputs[4].default_value = 1.01  # Subsurface IOR
            bsdf.inputs[7].default_value = 0.0  # Specular
            bsdf.inputs[9].default_value = 0.0  # Roughness
            bsdf.inputs[13].default_value = 0.0  # Sheen Tint
            bsdf.inputs[15].default_value = 0.0  # Clearcoat roughness

            ao_mix = new_mat.node_tree.nodes.new('ShaderNodeMix')
            ao_mix.data_type = 'RGBA'
            ao_mix.blend_type = 'MULTIPLY'
            ao_mix.inputs[6].default_value = (1, 1, 1, 1)
            ao_mix.inputs[7].default_value = (1, 1, 1, 1)
            new_mat.node_tree.links.new(ao_mix.outputs[2], bsdf.inputs['Base Color'])

            # in order to simulate some blending modes special node logic is required
            match special_blend_mode:
                case None:
                    new_mat.node_tree.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
                case SpecialBlendingMode.Add:
                    transparent_bsdf = new_mat.node_tree.nodes.new('ShaderNodeBsdfTransparent')
                    add_shader = new_mat.node_tree.nodes.new('ShaderNodeAddShader')

                    new_mat.node_tree.links.new(bsdf.outputs['BSDF'], add_shader.inputs[0])
                    new_mat.node_tree.links.new(transparent_bsdf.outputs['BSDF'], add_shader.inputs[1])
                    new_mat.node_tree.links.new(add_shader.outputs[0], out.inputs['Surface'])

                case SpecialBlendingMode.Mod:
                    shader_to_rgb = new_mat.node_tree.nodes.new('ShaderNodeShaderToRGB')
                    transparent_bsdf = new_mat.node_tree.nodes.new('ShaderNodeBsdfTransparent')
                    new_mat.node_tree.links.new(bsdf.outputs['BSDF'], shader_to_rgb.inputs[0])
                    new_mat.node_tree.links.new(shader_to_rgb.outputs['Color'], transparent_bsdf.inputs['Color'])
                    new_mat.node_tree.links.new(transparent_bsdf.outputs['BSDF'], out.inputs['Surface'])
        else:
            bsdf = new_mat.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
            new_mat.node_tree.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

        for tex_type, tex_path_and_name in texture_infos.items():
            # skip the texture if we don't know what to do with it
            if (tex_type := TEXTURE_PARAM_NAME_TRS.get(tex_type)) is None:
                continue

            # skip non-diffuse textures if we do not import PBR
            if not self.load_pbr_maps and tex_type is not TextureMapTypes.Diffuse:
                continue

            tex_path_no_ext, _ = os.path.splitext(tex_path_and_name)

            # normalize path from config
            tex_path_no_ext = os.path.normpath(tex_path_no_ext)

            # remove leading separator
            tex_path_no_ext = tex_path_no_ext[1:] if tex_path_no_ext.startswith(os.sep) else tex_path_no_ext

            tex_path = tex_path_no_ext + self.texture_format
            tex_path_abs = os.path.join(umodel_export_dir, tex_path)

            tex_lib_path = os.path.join(asset_library_dir, tex_path)
            tex_lib_blend_path = os.path.splitext(tex_lib_path)[0] + '.blend'

            # check if texture is not already in the library
            if not os.path.isfile(tex_lib_blend_path):
                if os.path.isfile(tex_path_abs):
                    self._import_image_to_library(tex_path=tex_path,
                                                  tex_lib_path=tex_lib_path,
                                                  tex_umodel_path=tex_path_abs,
                                                  db=db)
                else:
                    self._op_message('WARNING',
                                     f"Material \"{material_name}\" referenced texture \"{tex_path}\" "
                                     ", but it does not exist in the UModel export path.")
                    continue

            # load datablock from the library
            with bpy.data.libraries.load(filepath=tex_lib_blend_path, link=True) as (data_from, data_to):
                # we assume there is exactly one texture we have just written there
                data_to.images = [data_from.images[0]]

            img = data_to.images[0]

            img_node = new_mat.node_tree.nodes.new('ShaderNodeTexImage')
            img_node.image = img

            if self.load_pbr_maps:
                # Note: we presume MROH and SRO are mutually exclusive and never appear together.
                # This is not validated.

                match tex_type:
                    case TextureMapTypes.Diffuse:
                        new_mat.node_tree.links.new(img_node.outputs['Color'], ao_mix.inputs[6])
                    case TextureMapTypes.Normal:
                        normal_map_node = new_mat.node_tree.nodes.new('ShaderNodeNormalMap')
                        new_mat.node_tree.links.new(normal_map_node.outputs['Normal'],
                                                    bsdf.inputs['Normal'])
                        new_mat.node_tree.links.new(img_node.outputs['Color'],
                                                    normal_map_node.inputs['Color'])
                    case TextureMapTypes.SRO:
                        sro_split = new_mat.node_tree.nodes.new('ShaderNodeSeparateColor')
                        new_mat.node_tree.links.new(sro_split.outputs['Red'], bsdf.inputs['Specular'])
                        new_mat.node_tree.links.new(sro_split.outputs['Green'], bsdf.inputs['Roughness'])
                        new_mat.node_tree.links.new(sro_split.outputs['Blue'], ao_mix.inputs[7])
                        new_mat.node_tree.links.new(img_node.outputs['Color'], sro_split.inputs['Color'])
                    case TextureMapTypes.MROH:
                        # MRO components
                        mroh_split = new_mat.node_tree.nodes.new('ShaderNodeSeparateColor')
                        new_mat.node_tree.links.new(mroh_split.outputs['Red'], bsdf.inputs['Metallic'])
                        new_mat.node_tree.links.new(mroh_split.outputs['Green'], bsdf.inputs['Roughness'])
                        new_mat.node_tree.links.new(mroh_split.outputs['Blue'], ao_mix.inputs[7])
                        new_mat.node_tree.links.new(img_node.outputs['Color'], mroh_split.inputs['Color'])

                        # height component
                        displacement_node = new_mat.node_tree.nodes.new('ShaderNodeDisplacement')
                        new_mat.node_tree.links.new(displacement_node.outputs['Displacement'],
                                                    out.inputs['Displacement'])
                        new_mat.node_tree.links.new(img_node.outputs['Alpha'],
                                                    displacement_node.inputs['Height'])
                    case TextureMapTypes.MRO:
                        mro_split = new_mat.node_tree.nodes.new('ShaderNodeSeparateColor')
                        new_mat.node_tree.links.new(mro_split.outputs['Red'], bsdf.inputs['Metallic'])
                        new_mat.node_tree.links.new(mro_split.outputs['Green'], bsdf.inputs['Roughness'])
                        new_mat.node_tree.links.new(mro_split.outputs['Blue'], ao_mix.inputs[7])
                        new_mat.node_tree.links.new(img_node.outputs['Color'], mro_split.inputs['Color'])

            # just simply connect the diffuse map to the shader node, if we do not go the PBR route
            else:
                new_mat.node_tree.links.new(img_node.outputs['Color'], bsdf.inputs['Color'])

        # new_mat.asset_generate_preview()

        material_lib_path = os.path.join(asset_library_dir, material_path_local_no_ext) + '.blend'
        os.makedirs(os.path.dirname(material_lib_path), exist_ok=True)
        bpy.data.libraries.write(filepath=material_lib_path, datablocks={new_mat, }, fake_user=True)
        bpy.data.materials.remove(new_mat, do_unlink=True)

    def _import_asset_to_library(self,
                                 context: bpy.types.Context,
                                 asset_library_dir: str,
                                 asset_path: str,
                                 umodel_export_dir: str
                                 ) -> None:
        """Import asset (mesh) to an assset library from UModel output.

        :param context: Current Blender context.
        :param asset_library_dir: Directory to store the asset, and its dependencies in.
        :param asset_path: Path to the asset in game format.
        :param umodel_export_dir: UModel output directory to source .psk files from.
        :raises OSError: Raised when an asset was not found in the UModel output dir or the failed opening.
        :raises FileNotFounderror: Raised when an asset was not found in the directory.
        :raises RuntimeError: Raised when an asset failed importing due to unknown .psk/.pskx importer issue.
        """

        db = asset_db.AssetDB(asset_library_dir)
        asset_local_dir = os.path.dirname(asset_path)
        catalog_uid = db.uid_for_entry(asset_local_dir) if asset_local_dir else None
        asset_absolute_dir = os.path.join(asset_library_dir, asset_local_dir)
        asset_path_local_noext = os.path.splitext(asset_path)[0]

        os.makedirs(asset_absolute_dir, exist_ok=True)

        # create a temporary scene to perform the PSKX import.
        temp_scene = bpy.data.scenes.new('Temp Scene')

        asset_psk_path_noext = os.path.join(umodel_export_dir, asset_path_local_noext)

        psk_ctx = utils.ContextWrapper(context.copy())
        psk_ctx.scene = temp_scene
        psk_ctx.collection = temp_scene.collection
        psk_ctx.view_layer = temp_scene.view_layers[0]

        if os.path.isfile(pskx_path := asset_psk_path_noext + '.pskx'):
            if not pskimport(filepath=pskx_path,
                             context=psk_ctx,
                             bImportbone=False):
                bpy.data.scenes.remove(temp_scene, do_unlink=True)
                raise RuntimeError(f"Failed importing asset f{asset_psk_path_noext + '.pskx'} due to unknown reason.")

            animated = False
        elif os.path.isfile(psk_path := asset_psk_path_noext + '.psk'):
            if not pskimport(filepath=psk_path,
                             context=psk_ctx,
                             bImportbone=False):
                bpy.data.scenes.remove(temp_scene, do_unlink=True)
                raise RuntimeError(f"Failed importing asset f{asset_psk_path_noext + '.psk'} due to unknown reason.")
            animated = True

        else:
            bpy.data.scenes.remove(temp_scene, do_unlink=True)
            raise FileNotFoundError(f"Failed importing asset f{asset_psk_path_noext} was not found (.psk/.pskx).")

        # we presume that if the object is succesfully imported, there is exactly one object in the scene collection
        obj = temp_scene.collection.objects[0]
        assert len(temp_scene.collection.objects) == 1  # TODO: check if this presumption is valid

        # mark object as asset
        obj.asset_mark()
        obj.asset_data.catalog_id = catalog_uid

        # handle materials
        # - read material descriptor file and identify associated materials
        try:
            mat_descriptors_paths = props_txt_parser.parse_props_txt(asset_psk_path_noext + '.props.txt', mode='MESH')
        except OSError:
            self._op_message('WARNING', f"Loading material descriptor {asset_psk_path_noext + '.props.txt'} failed. "
                             "Materials might not be avaialble for the imported object.")
        else:
            # attempt to obtain materials manually if descriptor is not available
            mat_desc_order_map = {mat.name: None for mat in obj.data.materials}

            if animated and not mat_descriptors_paths:
                if os.path.isdir(mat_dir := os.path.join(os.path.dirname(psk_path), 'Materials')):
                    for root, _, files in os.walk(mat_dir):
                        for file in files:
                            if not file.endswith('.props.txt'):
                                continue

                            file_abs = os.path.splitext(os.path.splitext(os.path.join(root, file))[0])[0]
                            mat_name = os.path.basename(file_abs)

                            if mat_name not in mat_desc_order_map:
                                self._op_message('WARNING', f"Found extra material {mat_name} in the Materials dir. "
                                                 "It won't be imported.")
                                continue

                            mat_desc_order_map[mat_name] = f"{os.path.relpath(file_abs, umodel_export_dir)}.{mat_name}"

                    if any(mat_desc is None for mat_desc in mat_desc_order_map.values()):
                        self._op_message('ERROR', "Material count mistmatch.")
                        raise FileNotFoundError()

                    mat_descriptors_paths = list(mat_desc_order_map.values())

            # replace materials
            old_materials = [mat for mat in obj.data.materials]

            new_materials = []

            # initialize each material and populate it with data
            for mat_desc_path in mat_descriptors_paths:
                material_path_local_no_ext, material_name = os.path.splitext(mat_desc_path)
                material_name = material_name[1:]  # removing the .

                # normalize path from config
                material_path_local_no_ext = os.path.normpath(material_path_local_no_ext)

                # remove leading separator
                material_path_local_no_ext = material_path_local_no_ext[1:] \
                    if material_path_local_no_ext.startswith(os.sep) else material_path_local_no_ext

                material_path_local = material_path_local_no_ext + '.props.txt'
                material_lib_path = os.path.join(asset_library_dir, material_path_local_no_ext) + '.blend'

                try:
                    # add material to asset library if does not exist
                    if not os.path.isfile(material_lib_path):
                        self._import_material_to_library(material_name=material_name,
                                                         material_path_local=material_path_local,
                                                         db=db,
                                                         umodel_export_dir=umodel_export_dir,
                                                         asset_library_dir=asset_library_dir)

                    # load material from the library
                    with bpy.data.libraries.load(filepath=material_lib_path, link=True) as (data_from, data_to):

                        # we presume there is exactly one material in the library, no validation performed
                        data_to.materials = [data_from.materials[0]]

                    new_mat = data_to.materials[0]
                except OSError:
                    new_mat = bpy.data.materials.new(f"{material_name}_Placeholder")
                    self._op_message('WARNING',
                                     f"Material \"{material_name}\" failed to load, placeholder used instead.")

                new_materials.append(new_mat)

            for i, mat in enumerate(new_materials):
                obj.data.materials[i] = mat

            # remove original materials
            for mat in old_materials:
                bpy.data.materials.remove(mat, do_unlink=True)

        # obj.asset_generate_preview()

        asset_abs_lib_path = os.path.join(asset_library_dir, asset_path_local_noext) + '.blend'
        os.makedirs(os.path.dirname(asset_abs_lib_path), exist_ok=True)
        bpy.data.libraries.write(asset_abs_lib_path, {obj, }, fake_user=True)

        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.scenes.remove(temp_scene, do_unlink=True)

        db.save_db()

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[int] | set[str]:
        wm: bpy.types.WindowManager = context.window_manager

        return wm.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not self.asset_path:
            return self._op_message('ERROR', "Asset path was not provided.")

        scene: bpy.types.Scene = context.scene
        selected_objects: t.Sequence[selected_objects] = context.selected_objects
        umodel_export_dir: str = scene.umodel_tools.umodel_export_dir

        if not umodel_export_dir:
            return self._op_message('ERROR', "You need to specify a UModel export dir in Scene properties.")

        if not os.path.isdir(umodel_export_dir):
            return self._op_message('ERROR', f"Path to UModel export dir {umodel_export_dir} does not exist.")

        asset_dir: str = scene.umodel_tools.asset_dir

        if not asset_dir:
            return self._op_message('ERROR', "You need to specify an asset dir in Scene properties.")

        if not os.path.isdir(asset_dir):
            return self._op_message('ERROR', f"Path to asset dir {asset_dir} does not exist.")

        asset_path = os.path.normpath(self.asset_path)
        asset_path = asset_path[1:] if asset_path.startswith(os.sep) else asset_path
        asset = self._load_asset(context=context, asset_dir=os.path.normpath(asset_dir),
                                 asset_path=os.path.normpath(asset_path),
                                 umodel_export_dir=os.path.normpath(umodel_export_dir))

        if asset is None:
            self._op_message('ERROR', "Failed to import asset.")
            return {'CANCELLED'}

        asset_mesh = asset.data

        # attempt replacing selected object with an asset
        if context.selected_objects:
            for obj in context.selected_objects:

                if utils.compare_meshes(asset_mesh, obj.data):
                    vtx_source = np.array([v.co for v in asset_mesh.vertices])
                    vtx_target = np.array([obj.matrix_world @ v.co for v in obj.data.vertices])
                else:
                    vtx_source = np.array(_get_object_aabb_verts(asset))
                    vtx_target = np.array(_get_object_aabb_verts(obj))

                pad = lambda x: np.hstack([x, np.ones((x.shape[0], 1))])
                X = pad(vtx_source)
                Y = pad(vtx_target)

                A, _, _, _ = np.linalg.lstsq(X, Y, rcond=1)

                obj.hide_set(True)

                new_obj = bpy.data.objects.new(name=f"{obj.name}_Replaced", object_data=asset_mesh)
                new_obj.matrix_world = A
                new_obj.umodel_tools_asset.enabled = True
                new_obj.umodel_tools_asset.asset_path = self.asset_path

                context.collection.objects.link(new_obj)

        # import the asset as a new object
        else:
            new_obj = bpy.data.objects.new(name=f"{asset.name}_Instance", object_data=asset_mesh)
            new_obj.umodel_tools_asset.enabled = True
            new_obj.umodel_tools_asset.asset_path = self.asset_path
            new_obj.location = context.scene.cursor.location
            new_obj.scale = (5, 5, 5)
            context.collection.objects.link(new_obj)
            new_obj.select_set(True)

        return {'FINISHED'}


class UMODELTOOLS_OT_realign_asset(bpy.types.Operator):
    bl_idname = "umodel_tools.realign_asset"
    bl_label = "Realign Unreal Asset"
    bl_description = "Attempt realigning the asset with a selected object boundary"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: bpy.types.Context) -> set[str]:

        if not len(context.selected_objects) == 2:
            self.report({'ERROR'}, "Exactly 2 objects must be selected.")
            return {'CANCELLED'}

        asset_idx = None
        for i, obj in enumerate(context.selected_objects):
            if obj.umodel_tools_asset.enabled:
                asset_idx = i
                break

        if asset_idx is None:
            self.report({'ERROR'}, "One of the objects must be an Unreal asset.")
            return {'CANCELLED'}

        asset_obj = context.selected_objects[asset_idx]
        target_obj = context.selected_objects[int(not asset_idx)]

        bpy.ops.object.select_all(action='DESELECT')

        asset_obj_copy = utils.copy_object(asset_obj)
        target_obj_copy = utils.copy_object(target_obj)

        context.collection.objects.link(asset_obj_copy)
        context.collection.objects.link(target_obj_copy)

        asset_obj_copy.select_set(True)
        target_obj_copy.select_set(True)

        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        vtx_source = np.array(_get_object_aabb_verts(asset_obj_copy))
        vtx_target = np.array(_get_object_aabb_verts(target_obj_copy))

        pad = lambda x: np.hstack([x, np.ones((x.shape[0], 1))])
        unpad = lambda x: x[:, :-1]
        X = pad(vtx_source)
        Y = pad(vtx_target)

        A, _, _, _ = np.linalg.lstsq(X, Y, rcond=1)

        transform = lambda x: unpad(pad(x) @ A)
        transformed_verts = transform(np.array([v.co for v in asset_obj_copy.data.vertices]))
        vtx_source_local = np.array([v.co for v in asset_obj.data.vertices])

        X = pad(vtx_source_local)
        Y = pad(transformed_verts)

        A, _, _, _ = np.linalg.lstsq(X, Y, rcond=1)

        target_obj.hide_set(True)
        asset_obj.matrix_world = A
        asset_obj.select_set(True)

        bpy.data.objects.remove(asset_obj_copy, do_unlink=True)
        bpy.data.objects.remove(target_obj_copy, do_unlink=True)

        return {'FINISHED'}


def menu_func(menu: bpy.types.Menu, _: bpy.types.Context) -> None:
    menu.layout.operator(UMODELTOOLS_OT_recover_unreal_asset.bl_idname)
    menu.layout.operator(UMODELTOOLS_OT_realign_asset.bl_idname)


def bl_register():
    bpy.types.VIEW3D_MT_object.append(menu_func)


def bl_unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_func)
