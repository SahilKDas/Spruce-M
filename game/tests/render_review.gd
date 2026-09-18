extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _capture(name: String) -> void:
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://../benchmarks/"+name+".png")

func _run() -> void:
	var game: Node3D = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	await create_timer(3).timeout
	await _capture("menu")
	print("HYDRO_DISPLAY output=",root.get_texture().get_size()," viewport=",root.size," ui=",root.get_visible_rect().size," scale3d=",root.scaling_3d_scale," fullscreen=",root.mode," cap=",Engine.max_fps)
	print("HYDRO_TEXT antialiasing=",game.root_ui.theme.default_font.antialiasing," subpixel=",game.root_ui.theme.default_font.subpixel_positioning," MSAA=",root.msaa_3d," FXAA=",root.screen_space_aa)
	game.start_race()
	game.player.automated=true
	await create_timer(7).timeout
	await _capture("race")
	game._toggle_pause()
	await create_timer(.2).timeout
	await _capture("pause")
	game._request_exit()
	await create_timer(.2).timeout
	await _capture("exit_confirmation")
	game._toggle_pause()
	game._toggle_pause()
	game.racer_finished(game.player)
	await create_timer(.2).timeout
	await _capture("results")
	quit()
