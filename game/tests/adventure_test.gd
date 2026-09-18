extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var game = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game.start_exploration()
	assert(game.mode=="explore" and game.racers.size()==1)
	assert(game.adventure.boxes.size()==4 and game.adventure.relics.size()==12)
	assert(absf(HydroCourse.tide(45)-HydroCourse.tide(135))>1.7)
	for index in [3,1,2,0]:
		game.adventure.cooldown = 0
		game.player.position = game.adventure.boxes[index].position+Vector3.UP
		game.adventure.update(.016)
		assert(game.mode=="countdown" and game.event_id==index)
		assert(HydroCourse.center==game.adventure.CENTERS[index])
		assert(game.racers.size()==8)
		game.racer_finished(game.player)
		assert(index in game.adventure.completed)
		game.start_exploration()
		assert(game.mode=="explore" and game.adventure.cooldown>0)
	game.player.position = game.adventure.relics[4].position
	game.adventure.update(.016)
	assert(4 in game.adventure.collected and not game.adventure.relics[4].visible)
	game.player.position = game.adventure.CENTERS[1]+Vector3(0,4.8,0)
	game.player.linear_velocity = Vector3.ZERO
	game.player.reset_physics_interpolation()
	game.adventure.cooldown = 100
	for i in 90:await physics_frame
	var initial: Vector3 = game.player.position
	Input.action_press("accelerate")
	for i in 100:await physics_frame
	Input.action_release("accelerate")
	assert(game.player.position.distance_to(initial)>8,"Land driving failed")
	assert(game.player.position.y>-3,"Land collision failed")
	game._toggle_pause()
	assert(paused and game.pause_panel.visible)
	game._toggle_pause()
	print("HYDRO_ADVENTURE_OK four unordered race boxes, return, relics, tides, land driving, pause")
	quit()
