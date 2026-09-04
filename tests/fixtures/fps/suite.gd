extends RefCounted

func run_tests() -> Dictionary:
	var rules: RefCounted = load("res://domain/rules.gd").new()
	var failures: Array = []
	if not rules.fire() or rules.ammo != 5:
		failures.append("Firing must consume one round")
	for i: int in range(5):
		rules.fire()
	if rules.fire() or rules.shots != 6 or rules.ammo != 0:
		failures.append("Empty weapon must not fire")
	return {"assertions": 2, "failures": failures}
