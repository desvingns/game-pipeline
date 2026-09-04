# Competitive

Use an authoritative server for movement validation, hits, damage, ammo and
round state. Define prediction/reconciliation, interpolation and any lag
compensation explicitly; never trust client-reported damage. Test two real
processes, ownership, invalid RPCs, join/disconnect/rejoin, latency and round reset.
Retain server/client logs. Offline bots are not a network test. Passing these
scenarios does not prove production anti-cheat or large-scale matchmaking.
