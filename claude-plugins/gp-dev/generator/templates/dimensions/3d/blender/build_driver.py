"""Called by Blender: recipe defines build(spec); driver owns export and previews."""
import json
import math
from pathlib import Path
import random
import runpy
import sys

import bpy
from mathutils import Vector


def main():
    spec_file, recipe, output = [Path(p) for p in sys.argv[sys.argv.index("--") + 1:]]
    spec = json.loads(spec_file.read_text(encoding="utf-8"))
    random.seed(spec["seed"])
    # This factory-startup process owns these in-memory objects, not user files.
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    sys.path.insert(0, str(recipe.parent))
    module = runpy.run_path(str(recipe))
    if not callable(module.get("build")):
        raise ValueError("Recipe must define build(spec)")
    module["build"](spec)
    inputs = set()
    for item in [*bpy.data.images, *bpy.data.libraries]:
        filepath = getattr(item, "filepath", "")
        if filepath and getattr(item, "source", "FILE") != "GENERATED":
            path = Path(bpy.path.abspath(filepath)).resolve()
            inputs.add(path.relative_to(Path.cwd()).as_posix())
    output.with_suffix(".inputs.json").write_text(json.dumps(sorted(inputs)), encoding="utf-8")
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise ValueError("Recipe produced no meshes")
    # Contract uses meters and Blender Z-up; glTF exporter converts to Godot Y-up.
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    bpy.ops.wm.save_as_mainfile(filepath=str(output.with_suffix(".blend")))
    bpy.ops.export_scene.gltf(filepath=str(output), export_format="GLB", export_animations=True,
                             export_yup=True, export_cameras=False, export_lights=False)
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    center = (low + high) / 2
    radius = max((high - low).length, 0.1)
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    camera_data = bpy.data.cameras.new("GPPreview")
    camera = bpy.data.objects.new("GPPreview", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = radius * 1.2
    for index in range(3):
        angle = math.radians(35 + 120 * index)
        camera.location = center + Vector((math.cos(angle), math.sin(angle), 0.65)) * radius * 2
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(output.with_name(output.stem + "-" + str(index) + ".png"))
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
