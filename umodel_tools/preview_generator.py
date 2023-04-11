import os
import time

import bpy
import tqdm
import pexpect
import pexpect.popen_spawn


def spawn_preview_worker(blend_paths: str) -> None:

    proc = pexpect.popen_spawn.PopenSpawn(f"\"{bpy.app.binary_path}\" "
                                          "-b --python-console --factory-startup")
    proc.logfile = open('C:/Users/Skarn/Desktop/mylogfilename.txt', 'wb')
    proc.expect_exact('>>>')
    proc.sendline("import bpy; import umodel_tools.preview_generator as g;")
    proc.expect_exact('>>>')

    for bl_path in tqdm.tqdm(blend_paths, desc="Rendering previews", ascii=True):
        proc.sendline(f"g.render_previews(r\"{bl_path}\")")
        if not proc.expect_exact(["False", "True"]):
            proc.expect_exact(">>>")
            continue

        proc.expect_exact(">>>")

        """
        proc.sendline("g.is_render_done()")

        while not bool(proc.expect_exact(['False', 'True'])):
            proc.expect_exact('>>>')
            time.sleep(2)
            proc.sendline("g.is_render_done()")

        proc.expect_exact('>>>')

        """

        time.sleep(5)

        proc.sendline(f"g.save_blend(r\"{bl_path}\")")
        proc.expect_exact('>>>')


def save_blend(blend_path: str) -> None:
    bpy.ops.wm.save_mainfile(filepath=blend_path, check_existing=False)


def is_render_done() -> bool:
    for obj in bpy.data.objects:
        if obj.asset_data is not None:
            if obj.preview is None or obj.id_data.preview is None:
                return False

            if obj.id_data.preview.image_size[0] == 0:
                return False

    if bpy.app.is_job_running('RENDER_PREVIEW') or bpy.app.is_job_running('RENDER'):
        return False

    return True


def render_previews(blend_path: str) -> bool:
    if not os.path.exists(blend_path):
        return False

    bpy.ops.wm.open_mainfile(filepath=blend_path, check_existing=False)

    for obj in bpy.data.objects:
        if obj.asset_data is not None:
            with bpy.context.temp_override(id=obj):
                bpy.ops.ed.lib_id_generate_preview()
    return True
