extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var game = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	Engine.time_scale = 8
	Engine.physics_ticks_per_second = 480
	Engine.max_fps = 0
	for index in [2,0,3,1]:
		game.start_exploration()
		game.enter_event(index)
		game.player.automated = true
		game.countdown = .01
		while game.mode!="results" and game.race_time<180:
			await process_frame
		if game.mode!="results":
			push_error("Regional race timed out: %s" % index)
			quit(1)
			return
		print("HYDRO_REGION_RACE_OK ",index," seconds=",game.race_time)
	print("HYDRO_REGIONAL_RACES_OK")
	quit()
