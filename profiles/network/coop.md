# Co-op

Implement server-authoritative game state with explicit peer ownership and
validated commands. Define join, disconnect/rejoin, synchronization of enemies,
damage, inventory, objectives and revive states. Document transport and lobby
scope. Test at least two actual Godot processes, retain both logs, exercise
latency/disconnect and reject invalid peer commands. Do not substitute two local
bots. The network scenario must satisfy pipeline/qa-contract.json. Internet
matchmaking/NAT services require their own explicit scope and configuration.
