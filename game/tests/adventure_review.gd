extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var game = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game.start_exploration()
	game.adventure.cooldown = 1000
	for index in [1,2,3]:
		game.player.position = game.adventure.CENTERS[index]+Vector3(80,1,40)
		game.player.rotation.y = PI/2
		game.player.linear_velocity = Vector3.ZERO
		game.player.reset_physics_interpolation()
		game.reset_chase_camera()
		await create_timer(1.5).timeout
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://../benchmarks/adventure_%d.png" % index)
	print("HYDRO_ADVENTURE_RENDER_OK")
	quit()
