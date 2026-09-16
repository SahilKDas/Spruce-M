extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var game: Node3D=load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game.time_trial=true
	game.start_race()
	game.mode="race"
	game.player.active=true
	game.player.freeze=true
	var player: HydroCraft=game.player
	# Crossing gate 2 before the start line must leave progress untouched.
	var wrong:=HydroCourse.gate(1)
	var direction:=HydroCourse.tangent(TAU/HydroCourse.GATES)
	player.last_position=wrong-direction
	player.position=wrong+direction
	player._physics_process(1.0/60.0)
	assert(player.passed==-1 and player.next_gate==0,"Out-of-order checkpoint advanced the race")
	# Start line, then three complete circuits. No early finish at lap 1 or 2.
	for crossing in 61:
		var index:=crossing%20
		var gate:=HydroCourse.gate(index)
		direction=HydroCourse.tangent(float(index)/20*TAU)
		player.last_position=gate-direction
		player.position=gate+direction
		game.race_time=float(crossing+1)
		player._physics_process(1.0/60.0)
		assert(player.passed==crossing,"Ordered checkpoint was lost")
		assert(player.finished==(crossing==60),"Three-lap race finished at the wrong crossing")
	assert(game.mode=="results" and game.results_panel.visible)
	print("HYDRO_THREE_LAPS_OK rejects out-of-order gate, requires 3 circuits, opens results")
	quit()
