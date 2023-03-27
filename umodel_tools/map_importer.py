import json
import math
import os
import typing as t

import mathutils as mu
import bpy
import tqdm

from . import asset_db
from . import asset_importer
from . import utils


def split_object_path(object_path):
    # For some reason ObjectPaths end with a period and a digit.
    # This is kind of a sucky way to split that out.

    path_parts = object_path.split(".")

    if len(path_parts) > 1:
        # Usually works, but will fail If the path contains multiple periods.
        return path_parts[0]

    # Nothing to do
    return object_path


class InstanceTransform:
    pos: tuple[float, float, float]
    rot_euler: tuple[float, float, float]
    scale: tuple[float, float, float]

    def __init__(self,
                 pos: tuple[float, float, float] = (0.0, 0.0, 0.0),
                 rot_euler: tuple[float, float, float] = (0.0, 0.0, 0.0),
                 scale: tuple[float, float, float] = (1.0, 1.0, 1.0)) -> None:
        self.pos = pos
        self.rot_euler = rot_euler
        self.scale = scale

    @property
    def matrix_4x4(self) -> mu.Matrix:
        return mu.Matrix.LocRotScale(mu.Vector(self.pos),
                                     mu.Euler(self.rot_euler, 'XYZ'),
                                     mu.Vector(self.scale))


class StaticMesh:
    static_mesh_types = [
        'StaticMeshComponent',
        'InstancedStaticMeshComponent',
        'HierarchicalInstancedStaticMeshComponent'
    ]

    entity_name: str = ""
    asset_path: str = ""
    transform: InstanceTransform
    instance_transforms: list[InstanceTransform]

    # these are just properties to help with debugging
    no_entity: bool = False
    no_mesh: bool = False
    no_path: bool = False
    no_per_instance_data: bool = False
    base_shape: bool = False
    is_instanced: bool = False
    not_rendered: bool = False
    invisible: bool = False

    def __init__(self, json_entity: t.Any, entity_type: str) -> None:
        self.entity_name = json_entity.get("Outer", 'Error')
        self.instance_transforms = []

        if not (props := json_entity.get("Properties", None)):
            self.no_entity = True
            return

        if not props.get("StaticMesh", None):
            self.no_mesh = True
            return

        if not (object_path := props.get("StaticMesh").get("ObjectPath", None)) or object_path == '':
            self.no_path = True
            return

        if 'BasicShapes' in object_path:
            # What is a BasicShape? Do we need these?
            self.base_shape = True
            return

        if (render_in_main_pass := props.get("bRenderInMainPass", None)) is not None and not render_in_main_pass:
            self.not_rendered = True
            return

        if (is_visbile := props.get("bVisible", None)) is not None and not is_visbile:
            self.invisible = True

        objpath = split_object_path(object_path)

        self.asset_path = os.path.normpath(objpath + ".uasset")
        self.asset_path = self.asset_path[1:] if self.asset_path.startswith(os.sep) else self.asset_path

        match entity_type:
            case 'StaticMeshComponent':
                trs = InstanceTransform()

                if (pos := props.get("RelativeLocation", None)) is not None:
                    trs.pos = (pos.get("X") / 100, pos.get("Y") / -100, pos.get("Z") / 100)

                if (rot := props.get("RelativeRotation", None)) is not None:
                    trs.rot_euler = (math.radians(rot.get("Roll")),
                                     math.radians(rot.get("Pitch") * -1),
                                     math.radians(rot.get("Yaw") * -1))

                if (scale := props.get("RelativeScale3D", None)) is not None:
                    trs.scale = (scale.get("X", 1), scale.get("Y", 1), scale.get("Z", 1))

                self.transform = trs

            case 'InstancedStaticMeshComponent' | 'HierarchicalInstancedStaticMeshComponent':
                self.is_instanced = True

                if (instances := json_entity.get("PerInstanceSMData", None)) is None:
                    self.no_per_instance_data = True
                    return

                trs = InstanceTransform()

                if (pos := props.get("RelativeLocation", None)) is not None:
                    trs.pos = (pos.get("X") / 100, pos.get("Y") / -100, pos.get("Z") / 100)

                if (rot := props.get("RelativeRotation", None)) is not None:
                    trs.rot_euler = (math.radians(rot.get("Roll")),
                                     math.radians(rot.get("Pitch") * -1),
                                     math.radians(rot.get("Yaw") * -1))

                if (scale := props.get("RelativeScale3D", None)) is not None:
                    trs.scale = (scale.get("X", 1), scale.get("Y", 1), scale.get("Z", 1))

                self.transform = trs

                for instance in instances:
                    trs = InstanceTransform()

                    if (trs_data := instance.get("TransformData", None)) is not None:
                        if (pos := trs_data.get("Translation", None)) is not None:
                            trs.pos = (pos.get("X") / 100, pos.get("Y") / -100, pos.get("Z") / 100)

                        if (rot := trs_data.get("Rotation", None)) is not None:
                            rot_quat = mu.Quaternion((rot.get("W"), rot.get("X"), rot.get("Y"), rot.get("Z")))
                            quat_to_euler: mu.Euler = rot_quat.to_euler()  # pylint: disable=no-value-for-parameter
                            trs.rot_euler = (-quat_to_euler.x, quat_to_euler.y, -quat_to_euler.z)

                        if (scale := trs_data.get("Scale3D", None)) is not None:
                            trs.scale = (scale.get("X", 1), scale.get("Y", 1), scale.get("Z", 1))

                    self.instance_transforms.append(trs)

    @property
    def invalid(self):
        return (self.no_path or self.no_entity or self.base_shape or self.no_mesh or self.no_per_instance_data
                or self.not_rendered or self.invisible)

    def link_object_instance(self,
                             obj: bpy.types.Object,
                             collection: bpy.types.Collection) -> list[bpy.types.Object]:
        if self.invalid:
            print(f'Refusing to import {self.entity_name} due to failed checks.')
            return []

        objects = []
        trs = self.transform

        if self.is_instanced:
            for instance_trs in self.instance_transforms:
                mat_world = trs.matrix_4x4 @ instance_trs.matrix_4x4
                new_obj = bpy.data.objects.new(obj.name, object_data=obj.data)
                new_obj.rotation_mode = 'XYZ'
                new_obj.matrix_world = mat_world
                collection.objects.link(new_obj)
                objects.append(new_obj)

        else:
            new_obj = bpy.data.objects.new(obj.name, object_data=obj.data)
            new_obj.scale = (trs.scale[0], trs.scale[1], trs.scale[2])
            new_obj.location = (trs.pos[0], trs.pos[1], trs.pos[2])
            new_obj.rotation_mode = 'XYZ'
            new_obj.rotation_euler = mu.Euler((trs.rot_euler[0], trs.rot_euler[1], trs.rot_euler[2]), 'XYZ')
            collection.objects.link(new_obj)
            objects.append(new_obj)

        return objects


class GameLight:
    light_types = [
        'SpotLightComponent',
        'AnimatedLightComponent',
        'PointLightComponent'
    ]

    type = ""

    entity_name: str = ""
    pos: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rot: tuple[float, float, float] = (0.0, 0.0, 0.0)
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0)

    no_entity = False

    def __init__(self, json_entity):
        self.entity_name = json_entity.get("Outer", 'Error')
        self.type = json_entity.get("SpotLightComponent", "SpotLightComponent")

        props = json_entity.get("Properties", None)
        if not props:
            print(f"Invalid Entity {self.entity_name}. Lacking properties.")
            self.no_entity = True
            return None

        if props.get("RelativeLocation", False):
            pos = props.get("RelativeLocation")
            self.pos = [pos.get("X") / 100, pos.get("Y") / -100, pos.get("Z") / 100]

        if props.get("RelativeRotation", False):
            rot = props.get("RelativeRotation")
            self.rot = [rot.get("Roll"), rot.get("Pitch") * -1, rot.get("Yaw") * -1]

        if props.get("RelativeScale3D", False):
            scale = props.get("RelativeScale3D")
            self.scale = [scale.get("X", 1), scale.get("Y", 1), scale.get("Z", 1)]

        # TODO: expand this method with more properties for the specific light types
        # Problem: I don't know how values for UE lights map to Blender's light types.

        return None

    def import_light(self, collection) -> bool:
        if self.no_entity:
            print(f"Refusing to import {self.entity_name} due to failed checks.")
            return False

        if self.type == 'SpotLightComponent':
            light_data = bpy.data.lights.new(name=self.entity_name, type='SPOT')
        if self.type == 'PointLightComponent':
            light_data = bpy.data.lights.new(name=self.entity_name, type='POINT')

        light_obj = bpy.data.objects.new(name=self.entity_name, object_data=light_data)
        light_obj.scale = (self.scale[0], self.scale[1], self.scale[2])
        light_obj.location = (self.pos[0], self.pos[1], self.pos[2])
        light_obj.rotation_mode = 'XYZ'
        light_obj.rotation_euler = mu.Euler((math.radians(self.rot[0]),
                                             math.radians(self.rot[1]),
                                             math.radians(self.rot[2])),
                                            'XYZ')
        collection.objects.link(light_obj)
        bpy.context.scene.collection.objects.link(light_obj)

        return True


class MapImporter(asset_importer.AssetImporter):
    """Imports Unreal Engine map (FModel .json output). Assets are imported from UModel output directory.
    """

    @staticmethod
    def _library_reload():
        for lib in bpy.data.libraries:
            lib.reload()

    def _import_map(self,
                    context: bpy.types.Context,
                    map_path: str,
                    umodel_export_dir: str,
                    asset_dir: str,
                    game_profile: str,
                    db: t.Optional[asset_db.AssetDB] = None) -> bool:
        """Imports map placements to the current scene.

        :param map_path: Path to FModel .json output representing a .umap file.
        :param umodel_export_dir: UModel output directory.
        :param asset_dir: Asset library directory.
        :param game_profile: Current game profile.
        :param db: Asset database.
        :return: True if succesful, else False.
        """

        if not os.path.exists(map_path):
            print(f"Error: File {map_path} not found. Skipping.")
            return False

        json_filename = os.path.basename(map_path)
        import_collection = bpy.data.collections.new(json_filename)

        bpy.context.scene.collection.children.link(import_collection)

        with open(map_path, mode='r', encoding='utf-8') as file:
            json_object = json.load(file)

            # handle the different entity types (mehses, lights, etc)
            with utils.std_out_err_redirect_tqdm() as orig_stdout:
                for entity in tqdm.tqdm(json_object,
                                        desc=f"Importing map \"{os.path.splitext(os.path.basename(map_path))[0]}\"",
                                        file=orig_stdout,
                                        dynamic_ncols=True,
                                        ascii=True):
                    if not entity.get('Type', None):
                        continue

                    # static meshes
                    if (entity_type := entity.get('Type')) in StaticMesh.static_mesh_types:
                        static_mesh = StaticMesh(entity, entity_type)

                        if static_mesh.invalid:
                            utils.verbose_print(f"Info: Skipping instance of {static_mesh.entity_name}. "
                                                "Invalid property.")
                            continue

                        if (obj := self._load_asset(
                            context=context,
                            asset_dir=asset_dir,
                            asset_path=static_mesh.asset_path,
                            umodel_export_dir=umodel_export_dir,
                            load=True,
                            db=db,
                            game_profile=game_profile
                        )) is None:
                            self._warn_print(f"Warning: Skipping instance of {static_mesh.entity_name} due to import "
                                             "failure.")
                            continue

                        static_mesh.link_object_instance(obj, import_collection)

        # TODO: required due to unknown reason, blender bug? Otherwise, some meshes have None materials.
        bpy.app.timers.register(self._library_reload, first_interval=0.010)

        return True
