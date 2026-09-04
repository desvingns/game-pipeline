extends SceneTree
## The game supplies an engine-free RefCounted replay(seed) in tests/gp_replay.gd.
func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var replay_seed: int = 4242
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--gp-seed="):
			replay_seed = int(arg.trim_prefix("--gp-seed="))
	var script: Variant = load("res://tests/gp_replay.gd")
	if script == null:
		quit(1)
		return
	var harness: Variant = script.new()
	if not harness is RefCounted or not harness.has_method("replay"):
		quit(1)
		return
	var result: Variant = harness.replay(replay_seed)
	if not result is Dictionary or result.is_empty():
		quit(1)
		return
	# JSON.stringify sorts dictionary keys; report only the domain state hash.
	print("GP_REPLAY_RESULT=" + JSON.stringify({"seed": replay_seed, "hash": JSON.stringify(result, "", true).sha256_text()}))
	quit(0)
