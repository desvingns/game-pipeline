extends SceneTree
## Thin host: game-specific scenes exercise the production input/combat interfaces.
## Register scenario -> res://scene.tscn in tests/gp_scenarios.json.

var options: Dictionary = {}
var frame_ms: Array[float] = []
var last_usec: int = 0
var warmup: int = 60
var initial_drawn: int = 0

func _initialize() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--gp-") and "=" in arg:
			var pair: PackedStringArray = arg.split("=", true, 1)
			options[pair[0].trim_prefix("--gp-")] = pair[1]
	call_deferred("_run")

func _sample() -> void:
	var now: int = Time.get_ticks_usec()
	if warmup > 0:
		warmup -= 1
	elif last_usec > 0:
		frame_ms.append(float(now - last_usec) / 1000.0)
	last_usec = now

func _finish(checks: Array, metrics: Dictionary = {}, peers: Array = []) -> void:
	var passed: bool = not checks.is_empty()
	for check: Variant in checks:
		passed = passed and check is Dictionary and check.get("pass") == true
	print("GP_QA_RESULT=" + JSON.stringify({"schema_version": 1, "run_id": options.get("run-id", ""),
		"scenario": options.get("scenario", "smoke"), "seed": int(options.get("seed", "4242")),
		"pass": passed, "checks": checks, "metrics": metrics, "peers": peers}))
	quit(0)

func _run() -> void:
	var scenario: String = options.get("scenario", "smoke")
	var manifest: String = "res://tests/gp_scenarios.json"
	var registry: Variant = JSON.parse_string(FileAccess.get_file_as_string(manifest)) if FileAccess.file_exists(manifest) else null
	if not registry is Dictionary or not registry.has(scenario):
		_finish([{"id": "registration", "pass": false, "observed": "Scenario is not registered: " + scenario}])
		return
	var packed: Variant = load(str(registry[scenario]))
	if not packed is PackedScene:
		_finish([{"id": "registration", "pass": false, "observed": "Scenario is not a PackedScene"}])
		return
	var scene: Node = packed.instantiate()
	root.add_child(scene)
	await process_frame
	if not scene.has_method("gp_run"):
		_finish([{"id": "registration", "pass": false, "observed": "Scene has no gp_run(context) method"}])
		return
	initial_drawn = Engine.get_frames_drawn()
	process_frame.connect(_sample)
	var context: Dictionary = {"seed": int(options.get("seed", "4242")), "scenario": scenario, "run_id": options.get("run-id", "")}
	var result: Variant = await scene.gp_run(context)
	process_frame.disconnect(_sample)
	if not result is Dictionary or not result.get("checks") is Array:
		_finish([{"id": "contract", "pass": false, "observed": "gp_run must return a checks array"}])
		return
	var metrics: Dictionary = result.get("metrics", {})
	if scenario in ["visual", "perf", "ui"]:
		if DisplayServer.get_name() == "headless" or Engine.get_frames_drawn() <= initial_drawn:
			_finish([{"id": "rendering", "pass": false, "observed": "No rendered frames"}])
			return
		await RenderingServer.frame_post_draw
		var shot: Image = root.get_texture().get_image()
		if shot == null or shot.is_empty():
			_finish([{"id": "rendering", "pass": false, "observed": "Empty viewport"}])
			return
		metrics["width"] = shot.get_width()
		metrics["height"] = shot.get_height()
		var saved: Error = shot.save_png(str(options.get("shot", "user://gp-shot.png")))
		if saved != OK:
			_finish([{"id": "rendering", "pass": false, "observed": "PNG save failed"}])
			return
	if scenario == "perf":
		frame_ms.sort()
		var sum_ms: float = 0.0
		for value: float in frame_ms:
			sum_ms += value
		metrics["frames"] = frame_ms.size()
		metrics["fps"] = 1000.0 * frame_ms.size() / sum_ms if sum_ms > 0.0 else 0.0
		metrics["p95_frame_ms"] = frame_ms[mini(frame_ms.size() - 1, int(ceil(frame_ms.size() * 0.95)) - 1)] if not frame_ms.is_empty() else 0.0
		metrics["adapter"] = RenderingServer.get_video_adapter_name()
		metrics["os"] = OS.get_name()
	_finish(result["checks"], metrics, result.get("peers", []))
