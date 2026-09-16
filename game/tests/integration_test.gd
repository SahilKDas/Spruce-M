extends SceneTree

var game: Node3D
var completed := 0
var simulation_seconds := 0.0
var finish_target := 20
var wall_start := 0
var finishing := false

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	game = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	await process_frame
	assert(game.mode=="menu" and game.menu_panel.visible)
	assert(game.rider_buttons.size()==8 and game.craft_buttons.size()==3)
	for rider in 8:
		game.chosen_rider=rider
		game._make_preview()
		await process_frame
		assert(is_instance_valid(game.player.rider_near),"Rider export missing")
	game.chosen_rider=0
	game.start_race()
	assert(game.racers.size()==8)
	game._toggle_pause()
	assert(paused and game.pause_panel.visible)
	game._toggle_pause()
	assert(not paused)
	game.player.next_gate=7
	game.player.passed=6
	game.player.position=Vector3(1000,-10,1000)
	game.player.respawn()
	assert(game.player.position.distance_to(HydroCourse.gate(6))<6)
	assert(game.player.next_gate==7 and game.player.passed==6,"Respawn changed checkpoint progress")
	game.racer_finished(game.player)
	assert(game.mode=="results" and game.results_panel.visible)
	game._return_to_menu()
	assert(game.mode=="menu" and game.menu_panel.visible and not game.hud.visible)
	game.time_trial=true
	game.start_race()
	assert(game.racers.size()==1)
	game.time_trial=false
	game.lap_limit=1
	game.smoke=true
	game.benchmark_duration=1000000
	game.race_finishes=0
	game.start_race()
	game.player.automated=true
	game.countdown=.1
	Engine.time_scale=8.0
	Engine.physics_ticks_per_second=480
	Engine.max_fps=0
	wall_start=Time.get_ticks_msec()
	print("HYDRO_UI_OK all 8 riders, race/time trial, pause, recovery, results, return to menu")
	while game.race_finishes<finish_target and simulation_seconds<1800:
		await process_frame
		simulation_seconds+=game.get_process_delta_time()
		if game.race_finishes>completed:
			completed=game.race_finishes
			print("HYDRO_RACE_OK ",completed,"/",finish_target)
	var result := {"automated_races_completed":game.race_finishes,"target":finish_target,"wall_seconds":(Time.get_ticks_msec()-wall_start)/1000.0,"simulated_seconds":simulation_seconds,"all_riders_loaded":true,"ui_flow_checks":true,"respawn_progress_preserved":true,"mode":"headless, 8x simulation, one-lap eight-racer races; no GPU performance measurement"}
	var output := FileAccess.open("res://../benchmarks/integration.json",FileAccess.WRITE)
	output.store_string(JSON.stringify(result,"\t"))
	if game.race_finishes<finish_target:
		push_error("Automated races did not reach target")
		quit(1)
		return
	print("HYDRO_INTEGRATION_OK ",JSON.stringify(result))
	quit()
