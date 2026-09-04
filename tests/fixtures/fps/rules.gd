extends RefCounted
## Tiny production rule used only by the generator's integration fixture.
var ammo: int = 6
var shots: int = 0

func fire() -> bool:
	if ammo <= 0:
		return false
	ammo -= 1
	shots += 1
	return true
