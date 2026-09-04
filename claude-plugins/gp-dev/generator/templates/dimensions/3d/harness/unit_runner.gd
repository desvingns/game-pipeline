extends SceneTree
## Suites are RefCounted scripts with run_tests() -> {assertions: int, failures: Array}.

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var failures: Array = []
	var assertions: int = 0
	var path: String = "res://tests/gp_suites.json"
	var suites: Variant = JSON.parse_string(FileAccess.get_file_as_string(path)) if FileAccess.file_exists(path) else null
	if not suites is Array or suites.is_empty():
		failures.append("Register nonempty suites in tests/gp_suites.json")
	else:
		for suite_path: Variant in suites:
			var script: Variant = load(str(suite_path))
			if script == null or not script.can_instantiate():
				failures.append("Suite is not instantiable: " + str(suite_path))
				continue
			var suite: Variant = script.new()
			if not suite is RefCounted or not suite.has_method("run_tests"):
				failures.append("Suite must be RefCounted and implement run_tests")
				continue
			var result: Variant = await suite.run_tests()
			if not result is Dictionary or not result.get("assertions") is int or result.get("assertions", 0) < 1 or not result.get("failures") is Array:
				failures.append("Suite returned invalid/empty assertions: " + str(suite_path))
				continue
			assertions += result["assertions"]
			failures.append_array(result["failures"])
	print("GP_TEST_RESULT=" + JSON.stringify({"pass": failures.is_empty() and assertions > 0, "assertions": assertions, "failures": failures}))
	quit(0)
