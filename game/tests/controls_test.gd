extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _steps(count: int) -> void:
	for i in count:
		await physics_frame

func _check(condition: bool, message: String) -> bool:
	if condition:return true
	push_error(message)
	quit(1)
	return false

func _run() -> void:
	var game: Node3D = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game.time_trial=true
	game.start_race()
	game.countdown=.01
	Engine.time_scale=4
	Engine.physics_ticks_per_second=240
	Engine.max_fps=0
	await _steps(20)
	Input.action_press("accelerate")
	await _steps(150)
	if not _check(game.player.speed_kph>35,"Throttle did not accelerate the player"):return
	var energy: float=game.player.boost
	Input.action_press("boost")
	await _steps(45)
	if not _check(game.player.boost<energy-8,"Boost did not consume energy"):return
	Input.action_release("boost")
	Input.action_press("steer_left")
	Input.action_press("drift")
	await _steps(50)
	if not _check(game.player.drifting and game.player.drift_charge>.15,"Drift did not charge"):return
	energy=game.player.boost
	Input.action_release("drift")
	Input.action_release("steer_left")
	await _steps(3)
	if not _check(game.player.boost>energy+3,"Drift release did not award boost"):return
	game.player.respawn()
	await _steps(45)
	Input.action_press("hop")
	await _steps(3)
	if not _check(game.player.linear_velocity.y>.5,"Hop did not lift the craft"):return
	Input.action_release("hop")
	Input.action_release("accelerate")
	game._toggle_pause()
	var paused_time: float=game.race_time
	var paused_position: Vector3=game.player.position
	await create_timer(.5,true,false,true).timeout
	if not _check(game.race_time==paused_time and game.player.position.is_equal_approx(paused_position),"Pause did not freeze race and physics"):return
	game._toggle_pause()
	print("HYDRO_CONTROLS_OK throttle, boost spending, drift reward, hop, pause freezes time/physics")
	quit()
