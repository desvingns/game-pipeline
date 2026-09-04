extends Node
## Install as the GPExportQA autoload. Ordinary launches do nothing.
## In exported QA runs the normal main scene stays loaded. Its gp_run(context)
## must exercise the real game and return the required smoke checks.

func _ready() -> void:
	var options: Dictionary = {}
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--gp-") and "=" in arg:
			var pair: PackedStringArray = arg.split("=", true, 1)
			options[pair[0].trim_prefix("--gp-")] = pair[1]
	if not options.has("scenario") or options.get("export-smoke") != "1":
		return
	await get_tree().process_frame
	await get_tree().process_frame
	var main: Node = get_tree().current_scene
	var result: Variant = {}
	if main != null and main.has_method("gp_run"):
		result = await main.gp_run({"scenario": options["scenario"], "seed": int(options.get("seed", "4242")), "run_id": options.get("run-id", "")})
	var checks: Array = result.get("checks", []) if result is Dictionary else []
	var passed: bool = not checks.is_empty()
	for check: Variant in checks:
		passed = passed and check is Dictionary and check.get("pass") == true
	print("GP_QA_RESULT=" + JSON.stringify({"schema_version": 1, "run_id": options.get("run-id", ""),
		"scenario": options["scenario"], "seed": int(options.get("seed", "4242")), "pass": passed, "checks": checks}))
	get_tree().quit(0)
