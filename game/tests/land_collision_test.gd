extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func fail(message: String) -> void:
	push_error(message)
	quit(1)

func _run() -> void:
	var game = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game.start_exploration()
	game.adventure.cooldown = 10000
	await physics_frame
	for index in 4:
		var center: Vector3 = game.adventure.CENTERS[index]
		var probe := center+Vector3(22,0,0)
		var query := PhysicsRayQueryParameters3D.create(probe+Vector3.UP*30,probe-Vector3.UP*5)
		query.exclude = [game.player.get_rid()]
		query.hit_back_faces = false
		var hit: Dictionary = game.get_world_3d().direct_space_state.intersect_ray(query)
		if hit.is_empty() or hit.normal.y<.3:
			fail("Terrain has no upward-facing collider in biome %d" % index)
			return
		game.player.position = hit.position+Vector3.UP*3
		game.player.rotation = Vector3.ZERO
		game.player.linear_velocity = Vector3.ZERO
		game.player.angular_velocity = Vector3.ZERO
		game.player.reset_physics_interpolation()
		for step in 180:await physics_frame
		if game.player.position.y<hit.position.y-.3:
			fail("Craft fell through terrain in biome %d" % index)
			return
		# Approach the shore from water and drive inward; water movement alone must not pass.
		game.player.position = center+Vector3(85,1,0)
		game.player.rotation = Vector3(0,PI/2,0)
		game.player.linear_velocity = Vector3.ZERO
		game.player.angular_velocity = Vector3.ZERO
		game.player.reset_physics_interpolation()
		Input.action_press("accelerate")
		var climbed := false
		for step in 240:
			await physics_frame
			if game.player.position.y>1.4 and absf(game.player.position.x-center.x)<35:climbed = true
		Input.action_release("accelerate")
		if not climbed:
			fail("Water-to-land traversal failed in biome %d" % index)
			return
		print("HYDRO_LAND_OK biome=",index)
	print("HYDRO_LAND_COLLISION_OK all four terrains support falling craft and shoreline traversal")
	quit()

