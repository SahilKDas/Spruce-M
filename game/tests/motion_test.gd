extends SceneTree

class TickMover extends Node:
	var body: HydroCraft
	func _physics_process(delta: float) -> void:
		body.position.x += delta*10.0

func _initialize() -> void:
	create_timer(10.0,true,false,true).timeout.connect(func():push_error("Motion test timed out");quit(1))
	call_deferred("_run")

func _run() -> void:
	var game: Node3D = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game.time_trial = true
	game.start_race()
	game.mode = "race"
	game.player.freeze = true
	game.player.set_physics_process(false)
	Engine.physics_ticks_per_second = 10
	Engine.max_fps = 60
	var mover := TickMover.new()
	mover.body = game.player
	game.add_child(mover)
	await create_timer(.3).timeout
	var physical_moves := 0
	var presented_moves := 0
	var raw: Vector3 = game.player.global_position
	var shown: Vector3 = game.player.get_global_transform_interpolated().origin
	for i in 90:
		await process_frame
		var next_raw: Vector3 = game.player.global_position
		var next_shown: Vector3 = game.player.get_global_transform_interpolated().origin
		if next_raw.distance_to(raw)>.001:physical_moves+=1
		if next_shown.distance_to(shown)>.001:presented_moves+=1
		assert(game.camera.global_position.is_finite(),"Camera became invalid")
		raw = next_raw
		shown = next_shown
	assert(presented_moves>physical_moves*2,"Presentation still steps at the physics tick rate")
	mover.set_physics_process(false)
	game.player.respawn()
	await process_frame
	assert(game.player.get_global_transform_interpolated().origin.distance_to(game.player.global_position)<.01,"Recovery interpolates across the course")
	game._toggle_pause()
	var paused_water: float = game.water_time
	await create_timer(.2,true,false,true).timeout
	assert(game.water_time==paused_water,"Water physics clock advances while paused")
	game._request_exit()
	assert(paused and game.exit_dialog.visible,"Exit confirmation did not keep the race paused")
	game._toggle_pause()
	assert(paused and not game.exit_dialog.visible,"Canceling exit resumed the race unexpectedly")
	game._toggle_pause()
	assert(not paused,"Resume failed after canceling exit")
	print("HYDRO_MOTION_OK physical_moves=",physical_moves," presented_moves=",presented_moves," recovery reset, paused water, exit cancel")
	quit()
