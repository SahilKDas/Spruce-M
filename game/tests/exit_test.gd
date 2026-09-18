extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var game: Node3D = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game.time_trial = true
	game.start_race()
	game._toggle_pause()
	game._request_exit()
	assert(paused and game.exit_dialog.visible)
	game.exit_dialog.get_ok_button().pressed.emit()
	await create_timer(2.0,true,false,true).timeout
	push_error("Exit confirmation did not quit the application")
	quit(1)
