import bpy
import functools


def _render_previews_worker(assets: list[bpy.types.ID]):
    if bpy.app.is_job_running('RENDER_PREVIEW'):
        return 0.2

    while assets:  # Check if all previews have been generated
        asset = assets.pop()
        asset.asset_generate_preview()
        return 0.2

    bpy.ops.wm.save_mainfile(check_existing=False)
    print('RENDER_DONE')

    return None


def render_previews():
    for obj in bpy.data.objects:
        if obj.asset_data is not None:
            obj.asset_generate_preview()


def is_finished():
    for obj in bpy.data.objects:
        if obj.asset_data is not None:
            if obj.preview is None or obj.id_data.preview is None:
                return False

            if obj.id_data.preview.image_size[0] == 0:
                return False

    return True
