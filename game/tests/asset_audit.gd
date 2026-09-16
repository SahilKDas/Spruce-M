extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	for name in ["Palm_tree","Coastal_rocks","Beach_umbrella","Dock_3m","01_Needle_Agile","Kai_near"]:
		var scene: Node3D = load("res://art/%s.glb" % name).instantiate()
		root.add_child(scene)
		var bounds := AABB()
		var first := true
		var triangles := 0
		for child in scene.find_children("*","MeshInstance3D",true,false):
			var box: AABB = child.global_transform * child.get_aabb()
			bounds = box if first else bounds.merge(box)
			first = false
			for i in child.mesh.get_surface_count():
				var arrays: Array = child.mesh.surface_get_arrays(i)
				triangles += arrays[Mesh.ARRAY_INDEX].size()/3
		print(name," bounds=",bounds," triangles=",triangles)
		scene.free()
	quit()
