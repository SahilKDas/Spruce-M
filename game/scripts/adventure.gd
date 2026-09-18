extends Node3D

const CENTERS := [Vector3.ZERO,Vector3(310,0,-210),Vector3(-300,0,-230),Vector3(30,0,340)]
const COLORS := [Color("edc778"),Color("55734a"),Color("423f50"),Color("b5e9eb")]
const NAMES := ["Sunbeam Shores","Mangrove Reach","Ember Atoll","Frostwater Bay"]
var race: Node3D
var boxes: Array[Node3D] = []
var relics: Array[Node3D] = []
var discovered: Array[int] = []
var collected: Array[int] = []
var completed: Array[int] = []
var cooldown := 2.0
var safe_position := Vector3(95,1,10)

func _ready() -> void:
	for i in CENTERS.size():
		if i>0:_island(i)
		var marker := Node3D.new()
		marker.position = CENTERS[i]+Vector3(91,0,0)
		add_child(marker)
		boxes.append(marker)
		for side in [-1,1]:
			_box(marker,Vector3(side*7,.2,0),Vector3(.3,.25,14),Color("39d9c8"))
			_box(marker,Vector3(0,.2,side*7),Vector3(14,.25,.3),Color("39d9c8"))
		# Checkered flags identify enter-to-race boxes without text prompts.
		_box(marker,Vector3(-7,3,-7),Vector3(.16,6,.16),Color.WHITE)
		for x in 4:
			for y in 3:_box(marker,Vector3(-7+x*.55,5+y*.45,-7),Vector3(.55,.45,.08),Color.WHITE if (x+y)%2==0 else Color("152333"))
		for j in 3:
			var relic := Node3D.new()
			relic.position = CENTERS[i]+Vector3(-22+j*22,4,18 if j!=1 else -28)
			if i>0:relic.position.y = height(relic.position,CENTERS[i])+1.8
			add_child(relic)
			var ring := TorusMesh.new()
			ring.inner_radius = .7
			ring.outer_radius = 1.05
			ring.rings = 20
			ring.ring_segments = 8
			var visual := MeshInstance3D.new()
			visual.mesh = ring
			visual.material_override = race._material(Color("ffd769"),.2)
			visual.rotation.x = PI/2
			relic.add_child(visual)
			relics.append(relic)
	load_progress()

func _box(parent: Node3D, p: Vector3, dimensions: Vector3, color: Color) -> void:
	var mesh := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = dimensions
	mesh.mesh = box
	mesh.material_override = race._material(color)
	mesh.position = p
	parent.add_child(mesh)

func height(p: Vector3, center: Vector3) -> float:
	var q := p-center
	var radius := Vector2(q.x/60.0,q.z/76.0).length()
	var base := -2.0+6.0*clampf(1.0-radius,0.0,1.0)+sin(q.x*.10)*sin(q.z*.09)*.5*clampf(1-radius,0,1)
	if center==CENTERS[2]:base += 10.0*exp(-pow(Vector2(q.x,q.z).length()-15.0,2.0)/45.0)
	return base

func _island(index: int) -> void:
	var center: Vector3 = CENTERS[index]
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for x in 40:
		for z in 48:
			var a := center+Vector3(-80+x*4,0,-96+z*4)
			for offset in [Vector3.ZERO,Vector3(0,0,4),Vector3(4,0,0),Vector3(4,0,0),Vector3(0,0,4),Vector3(4,0,4)]:
				var p: Vector3 = a+offset
				p.y = height(p,center)
				surface.set_color(COLORS[index].lerp(Color("e6ce91"),clampf(1-p.y,.0,.8)))
				surface.add_vertex(p)
	surface.generate_normals()
	var terrain := MeshInstance3D.new()
	terrain.mesh = surface.commit()
	var material: StandardMaterial3D = race._material(Color.WHITE)
	material.vertex_color_use_as_albedo = true
	terrain.material_override = material
	add_child(terrain)
	terrain.create_trimesh_collision()
	# Sparse biome silhouettes reuse meshes rather than large texture downloads.
	for j in 18:
		var a := j*2.39996
		var p := center+Vector3(cos(a)*32,0,sin(a)*42)
		p.y = height(p,center)
		if index in [1,2]:
			var asset := "Palm_tree" if index==1 else "Coastal_rocks"
			var prop := (load("res://art/%s.glb" % asset) as PackedScene).instantiate() as Node3D
			prop.position = p
			prop.scale = Vector3.ONE*(2.4 if index==1 else 2.0)
			prop.rotation.y = a
			add_child(prop)
			for child in prop.find_children("*","MeshInstance3D",true,false):child.visibility_range_end = 220.0
			continue
		var mesh := MeshInstance3D.new()
		var shape := CylinderMesh.new()
		shape.bottom_radius = 1.5 if index!=1 else .45
		shape.top_radius = .1
		shape.height = 5.0+float(j%4)
		shape.radial_segments = 8
		mesh.mesh = shape
		mesh.material_override = race._material(Color("779b62") if index==1 else (Color("e77b40") if index==2 else Color("90dbe7")))
		mesh.position = p+Vector3.UP*shape.height*.5
		mesh.visibility_range_end = 240
		add_child(mesh)
	if index==2:
		var lava := MeshInstance3D.new()
		var pool := CylinderMesh.new()
		pool.top_radius = 8
		pool.bottom_radius = 8
		pool.height = .1
		pool.radial_segments = 32
		lava.mesh = pool
		lava.material_override = race._material(Color("ed6a2e"))
		lava.position = center+Vector3.UP*4.3
		add_child(lava)
	# Low tidal causeway: passable dry at low tide, submerged at high tide.
	var bar := StaticBody3D.new()
	bar.position = center+Vector3(0,-.15,95)
	add_child(bar)
	var collision := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(16,.5,55)
	collision.shape = shape
	bar.add_child(collision)
	_box(bar,Vector3.ZERO,shape.size,COLORS[index])

func update(delta: float) -> void:
	for marker in boxes:marker.position.y = HydroCourse.tide(race.water_time)
	if race.mode!="explore":return
	cooldown = maxf(0,cooldown-delta)
	var p: Vector3 = race.player.global_position
	for i in CENTERS.size():
		if p.distance_to(CENTERS[i])<135 and not i in discovered:
			discovered.append(i)
			safe_position = boxes[i].position+Vector3(20,1,0)
			save_progress()
	for i in relics.size():
		if i in collected:continue
		var relic := relics[i]
		relic.rotation.y += delta
		if p.distance_to(relic.position)<4.5:
			collected.append(i)
			relic.hide()
			race.player.boost = 100
			race.toast_time = 1.2
			save_progress()
	if cooldown<=0:
		for i in boxes.size():
			var q: Vector3 = p-boxes[i].position
			if absf(q.x)<7 and absf(q.z)<7 and absf(q.y)<5:
				race.enter_event(i)
				return

func save_progress() -> void:
	if OS.get_cmdline_args().has("--script") or race.benchmark:return
	var data := ConfigFile.new()
	data.set_value("world","discovered",discovered)
	data.set_value("world","relics",collected)
	data.set_value("world","races",completed)
	data.save("user://adventure.cfg")

func load_progress() -> void:
	if OS.get_cmdline_args().has("--script"):return
	var data := ConfigFile.new()
	if data.load("user://adventure.cfg")!=OK:return
	discovered.assign(data.get_value("world","discovered",[]))
	collected.assign(data.get_value("world","relics",[]))
	completed.assign(data.get_value("world","races",[]))
	for i in collected:
		if i>=0 and i<relics.size():relics[i].hide()

