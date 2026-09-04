extends Node3D
## Integration fixture, not a shipped FPS or a visual-quality benchmark.
var player: CharacterBody3D
var camera: Camera3D
var label: Label
var command: Vector3 = Vector3.ZERO
var rules: RefCounted
var model: Node3D
var tick_count: int = 0

func _ready() -> void:
	rules = load("res://domain/rules.gd").new()
	var floor_body: StaticBody3D = StaticBody3D.new()
	var shape: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()
	box.size = Vector3(20, 0.4, 20)
	shape.shape = box
	floor_body.add_child(shape)
	var floor_mesh: MeshInstance3D = MeshInstance3D.new()
	var visual_box: BoxMesh = BoxMesh.new()
	visual_box.size = box.size
	floor_mesh.mesh = visual_box
	floor_body.add_child(floor_mesh)
	add_child(floor_body)
	var wall: StaticBody3D = StaticBody3D.new()
	var wall_collision: CollisionShape3D = CollisionShape3D.new()
	var wall_box: BoxShape3D = BoxShape3D.new()
	wall_box.size = Vector3(8, 3, 0.4)
	wall_collision.shape = wall_box
	wall.add_child(wall_collision)
	wall.position = Vector3(0, 1.5, -4)
	add_child(wall)
	player = CharacterBody3D.new()
	var capsule: CapsuleShape3D = CapsuleShape3D.new()
	capsule.radius = 0.3
	capsule.height = 1.6
	var player_shape: CollisionShape3D = CollisionShape3D.new()
	player_shape.shape = capsule
	player.add_child(player_shape)
	player.position = Vector3(2, 1.1, 2)
	add_child(player)
	camera = Camera3D.new()
	add_child(camera)
	camera.position = Vector3(4, 3, 6)
	camera.look_at(Vector3(0, 0.7, 0))
	camera.current = true
	var sun: DirectionalLight3D = DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-40, -30, 0)
	add_child(sun)
	var layer: CanvasLayer = CanvasLayer.new()
	label = Label.new()
	label.text = "GP integration fixture - Blender GLB / Godot"
	label.position = Vector2(24, 24)
	layer.add_child(label)
	add_child(layer)
	var packed: PackedScene = load("res://assets/models/fixture.glb")
	model = packed.instantiate()
	add_child(model)

func _physics_process(delta: float) -> void:
	if player == null:
		return
	tick_count += 1
	player.velocity.x = command.x * 3.0
	player.velocity.z = command.z * 3.0
	player.velocity.y -= 9.8 * delta
	player.move_and_slide()

func check(id: String, passed: bool, observed: Variant) -> Dictionary:
	return {"id": id, "pass": passed, "observed": str(observed)}

func gp_run(context: Dictionary) -> Dictionary:
	var scenario: String = context.get("scenario", "smoke")
	var checks: Array = []
	if scenario == "smoke":
		checks = [check("main_scene_loaded", is_inside_tree(), get_path()),
			check("player_spawned", is_instance_valid(player), player.position),
			check("hud_visible", label.is_visible_in_tree(), label.text)]
	elif scenario == "movement":
		for i: int in range(30):
			await get_tree().physics_frame
		checks.append(check("grounded", player.is_on_floor(), player.position))
		var start: Vector3 = player.position
		command = Vector3(0, 0, -1)
		for i: int in range(160):
			await get_tree().physics_frame
		command = Vector3.ZERO
		checks.append(check("move", player.position.distance_to(start) > 1.0, player.position))
		checks.append(check("blocked_by_wall", absf(player.position.z + 3.5) < 0.1, player.position.z))
		var ground_y: float = player.position.y
		player.velocity.y = 5.0
		for i: int in range(12):
			await get_tree().physics_frame
		checks.append(check("jump", player.position.y > ground_y + 0.2, player.position.y))
		checks.append(check("no_fall_through", player.position.y > 0, player.position.y))
	elif scenario in ["visual", "perf"]:
		var before: int = tick_count
		for i: int in range(220):
			model.rotation.y += 0.01
			await get_tree().process_frame
		checks.append(check("camera_active", camera.current, camera.get_path()))
		if scenario == "visual":
			checks.append(check("assets_visible", model.is_visible_in_tree(), model.get_path()))
			checks.append(check("hud_readable", label.is_visible_in_tree(), label.text))
		else:
			# The fixture verifies sampling; a real game must supply representative combat.
			checks.append(check("representative_combat", tick_count > before, tick_count - before))
	return {"checks": checks}
