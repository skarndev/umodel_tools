import bpy


class UMODELTOOLS_PT_scene_properties(bpy.types.Panel):
    bl_region_type = 'WINDOW'
    bl_space_type = 'PROPERTIES'
    bl_context = "scene"
    bl_label = "UModel Tools"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.scene is not None

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.prop(data=context.scene.umodel_tools, property='umodel_export_dir')
        layout.prop(data=context.scene.umodel_tools, property='asset_dir')


class UModelTools_PG_scene_properties(bpy.types.PropertyGroup):
    umodel_export_dir: bpy.props.StringProperty(
        name="UModel Export Directory",
        description="Path to the UModel export directory with game assets",
        subtype='DIR_PATH'
    )

    asset_dir: bpy.props.StringProperty(
        name="Asset Directory",
        description="Path to the directory where the assets for current project are stored",
        subtype='DIR_PATH'
    )


def bl_register():
    bpy.types.Scene.umodel_tools = bpy.props.PointerProperty(type=UModelTools_PG_scene_properties)
    bpy.types.Object.umodel_tools_asset = bpy.props.BoolProperty(default=False)

def bl_unregister():
    del bpy.types.Scene.umodel_tools
    del bpy.types.Object.umodel_tools_asset