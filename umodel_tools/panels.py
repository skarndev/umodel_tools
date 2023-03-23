import bpy

from .preferences import get_addon_preferences


class UMODELTOOLS_PT_asset(bpy.types.Panel):
    bl_region_type = 'WINDOW'
    bl_space_type = 'PROPERTIES'
    bl_context = "object"
    bl_label = "UModel Tools Asset"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return (context.scene is not None
                and context.object is not None
                and context.object.type == 'MESH')

    def draw_header(self, context: bpy.types.Context):
        return self.layout.prop(data=context.object.umodel_tools_asset, property='enabled', text="")

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.enabled = context.object.umodel_tools_asset.enabled

        layout.prop(data=context.object.umodel_tools_asset, property='asset_path')


class UMODELTOOLS_PG_asset(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name="Enabled",
        description="Toggles whether the object is treated as an Unreal asset",
        default=False
    )

    asset_path: bpy.props.StringProperty(
        name="Asset path",
        description="Path of the asset in the Unreal engine game"
    )


def topbar_menu_func(menu: bpy.types.Menu, context: bpy.types.Context):
    if context.region.alignment != 'RIGHT':
        return

    prefs = get_addon_preferences()

    if not prefs.display_cur_profile:
        return

    cur_profile = prefs.get_active_profile()
    menu.layout.label(text=f"UMT Active profile: {cur_profile.name if cur_profile else None}")


def bl_register() -> None:
    bpy.types.Object.umodel_tools_asset = bpy.props.PointerProperty(type=UMODELTOOLS_PG_asset)
    bpy.types.TOPBAR_HT_upper_bar.append(topbar_menu_func)


def bl_unregister() -> None:
    del bpy.types.Object.umodel_tools_asset
    bpy.types.TOPBAR_HT_upper_bar.remove(topbar_menu_func)
