extends RefCounted

func replay(replay_seed: int) -> Dictionary:
	var rules: RefCounted = load("res://domain/rules.gd").new()
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = replay_seed
	for i: int in range(20):
		if rng.randi_range(0, 1) == 1:
			rules.fire()
	return {"ammo": rules.ammo, "shots": rules.shots, "seed": replay_seed}
