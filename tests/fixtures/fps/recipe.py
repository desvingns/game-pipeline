"""One actual Blender mesh for generator integration; not production game art."""
import bpy


def build(spec):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.7))
    obj = bpy.context.object
    obj.name = "Fixture-convcol"
    material = bpy.data.materials.new("FixtureOrange")
    material.diffuse_color = (0.9, 0.3, 0.04, 1)
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = material.diffuse_color
    principled.inputs["Roughness"].default_value = 0.65
    obj.data.materials.append(material)
