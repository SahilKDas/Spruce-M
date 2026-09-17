extends Node3D

const RIDERS := ["Kai", "Zuri", "Riptide", "Pip", "Marina", "Bolt", "Mochi", "Ink"]
const CRAFT_NAMES := ["NEEDLE", "SURGE", "LEVIATHAN"]
const TEAL := Color("39d9c8")
const INK := Color("081c2b")
const MUTED := Color("a4bdc8")
var racers: Array[HydroCraft] = []
var player: HydroCraft
var camera: Camera3D
var water_material: ShaderMaterial
var water_time := 0.0
var race_time := 0.0
var lap_limit := 3
var recovery_count := 0
var mode := "menu"
var countdown := 3.0
var chosen_rider := 0
var chosen_craft := 0
var quality := 0
var time_trial := false
var root_ui: Control
var menu_panel: PanelContainer
var pause_panel: PanelContainer
var results_panel: PanelContainer
var hud: Control
var speed_label: Label
var race_label: Label
var time_label: Label
var status_label: Label
var telemetry_label: Label
var boost_bar: ProgressBar
var center_label: Label
var toast_label: Label
var toast_time := 0.0
var rider_buttons: Array[Button] = []
var craft_buttons: Array[Button] = []
var reset_count := 0
var sun: DirectionalLight3D
var engine_audio: AudioStreamPlayer
var engine_playback: AudioStreamGeneratorPlayback
var audio_phase := 0.0
var muted := false
var benchmark := false
var smoke := false
var benchmark_duration := 90.0
var benchmark_elapsed := 0.0
var benchmark_warmup := 10.0
var last_frame_us := 0
var minimap: Control
var samples: Array[float] = []
var slow_frames: Array[Dictionary] = []
var memory_peak := 0.0
var draw_peak := 0
var primitive_peak := 0
var capture_done := false
var race_finishes := 0
var pickup_count := 0
var rng := RandomNumberGenerator.new()
var hud_update := 0.0
var pickup_nodes: Array[Node3D] = []
var pickup_cooldowns: Array[float] = []
var settings := ConfigFile.new()

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	Engine.max_fps = 60
	rng.seed = 1709
	_parse_args()
	_bind_inputs()
	_load_settings()
	_build_environment()
	_build_course()
	_build_ui()
	_apply_quality(quality)
	_make_preview()
	if benchmark or smoke:
		start_race()
		player.automated = true
		if smoke:
			Engine.time_scale = 4.0
			Engine.physics_ticks_per_second = 240
			Engine.max_fps = 0
	else:
		Engine.max_fps = 60
	get_window().size_changed.connect(func(): _resolution_scale())
	print("HYDRO_READY renderer=%s adapter=%s" % [RenderingServer.get_current_rendering_method(),RenderingServer.get_video_adapter_name()])
	last_frame_us = Time.get_ticks_usec()

func _parse_args() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--benchmark="):
			benchmark = true
			benchmark_duration = float(arg.get_slice("=",1))
		if arg == "--smoke":
			smoke = true
			benchmark_duration = 60.0
		if arg.begins_with("--quality="):
			quality = int(arg.get_slice("=",1))
		if arg == "--one-lap":
			lap_limit = 1

func _bind_inputs() -> void:
	var keys := {"accelerate":[KEY_W,KEY_UP],"brake":[KEY_S,KEY_DOWN],"steer_left":[KEY_A,KEY_LEFT],"steer_right":[KEY_D,KEY_RIGHT],"drift":[KEY_SHIFT],"boost":[KEY_CTRL,KEY_E],"hop":[KEY_SPACE],"reset":[KEY_R],"pause":[KEY_ESCAPE],"mute":[KEY_M],"telemetry":[KEY_F3],"fullscreen":[KEY_F11]}
	for action in keys:
		if not InputMap.has_action(action):
			InputMap.add_action(action,.15)
		for key in keys[action]:
			var event := InputEventKey.new()
			event.physical_keycode = key
			InputMap.action_add_event(action,event)
	var buttons := {"hop":JOY_BUTTON_A,"boost":JOY_BUTTON_X,"drift":JOY_BUTTON_RIGHT_SHOULDER,"reset":JOY_BUTTON_Y,"pause":JOY_BUTTON_START}
	for action in buttons:
		var button := InputEventJoypadButton.new()
		button.button_index = buttons[action]
		InputMap.action_add_event(action,button)
	for spec in [["steer_left",JOY_AXIS_LEFT_X,-1.0],["steer_right",JOY_AXIS_LEFT_X,1.0],["accelerate",JOY_AXIS_TRIGGER_RIGHT,1.0],["brake",JOY_AXIS_TRIGGER_LEFT,1.0]]:
		var axis := InputEventJoypadMotion.new()
		axis.axis = spec[1]
		axis.axis_value = spec[2]
		InputMap.action_add_event(spec[0],axis)

func _load_settings() -> void:
	if OS.get_cmdline_args().has("--script"):return
	if settings.load("user://settings.cfg") == OK and not benchmark and not smoke:
		chosen_rider = clampi(int(settings.get_value("game","rider",0)),0,7)
		chosen_craft = clampi(int(settings.get_value("game","craft",0)),0,2)
		quality = clampi(int(settings.get_value("graphics","quality",0)),0,2)
		muted = bool(settings.get_value("audio","muted",false))

func _save_settings() -> void:
	if benchmark or smoke or OS.get_cmdline_args().has("--script"):return
	settings.set_value("game","rider",chosen_rider)
	settings.set_value("game","craft",chosen_craft)
	settings.set_value("graphics","quality",quality)
	settings.set_value("audio","muted",muted)
	settings.save("user://settings.cfg")

func _material(color: Color, rough: float = .75) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = rough
	return material

func _mesh(mesh: Mesh, material: Material, p: Vector3, size: Vector3 = Vector3.ONE) -> MeshInstance3D:
	var instance := MeshInstance3D.new()
	instance.mesh = mesh
	instance.material_override = material
	instance.position = p
	instance.scale = size
	add_child(instance)
	return instance

func _build_environment() -> void:
	var world := WorldEnvironment.new()
	var env := Environment.new()
	var sky := Sky.new()
	var atmosphere := ProceduralSkyMaterial.new()
	atmosphere.sky_top_color = Color("388bab")
	atmosphere.sky_horizon_color = Color("c4e5e6")
	atmosphere.ground_bottom_color = Color("244556")
	atmosphere.ground_horizon_color = Color("bddbd7")
	atmosphere.sky_curve = .25
	sky.sky_material = atmosphere
	env.sky = sky
	env.background_mode = Environment.BG_SKY
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = .8
	env.reflected_light_source = 0
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.fog_enabled = true
	env.fog_light_color = Color("a4d0d6")
	env.fog_density = .0014
	world.environment = env
	add_child(world)
	sun = DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-48,-35,0)
	sun.light_color = Color("fff0d0")
	sun.light_energy = 1.6
	sun.shadow_enabled = true
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
	sun.directional_shadow_max_distance = 75.0
	add_child(sun)
	camera = Camera3D.new()
	camera.fov = 64
	camera.far = 480
	camera.near = .15
	add_child(camera)
	var ocean := PlaneMesh.new()
	ocean.size = Vector2(700,700)
	ocean.subdivide_width = 150
	ocean.subdivide_depth = 150
	water_material = ShaderMaterial.new()
	water_material.shader = load("res://materials/water.gdshader")
	var sea := _mesh(ocean,water_material,Vector3.ZERO)
	sea.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var generator := AudioStreamGenerator.new()
	generator.mix_rate = 22050
	generator.buffer_length = .12
	engine_audio = AudioStreamPlayer.new()
	engine_audio.stream = generator
	engine_audio.volume_db = -18
	add_child(engine_audio)
	engine_audio.play()
	engine_playback = engine_audio.get_stream_playback() as AudioStreamGeneratorPlayback

func _build_course() -> void:
	_prop("Sunbeam_Island",Vector3.ZERO,1.0,0.0)
	var solid := StaticBody3D.new()
	var collision := CollisionShape3D.new()
	var outline := PackedVector3Array()
	for i in 28:
		var a := float(i)/28*TAU
		outline.append(Vector3(cos(a)*39,-3,sin(a)*61))
		outline.append(Vector3(cos(a)*39,1.6,sin(a)*61))
	var hull := ConvexPolygonShape3D.new()
	hull.points = outline
	collision.shape = hull
	solid.add_child(collision)
	add_child(solid)
	for i in 26:
		var a := float(i)/26*TAU
		var p := Vector3(cos(a)*(33+rng.randf_range(-5,4)),.5,sin(a)*(52+rng.randf_range(-4,4)))
		_prop("Palm_tree",p,rng.randf_range(1.6,2.8),a)
	for i in 13:
		var a := float(i)/13*TAU
		_prop("Coastal_rocks",Vector3(cos(a)*43,-.1,sin(a)*66),2.4,a)
	for i in 6:
		_prop("Beach_umbrella",Vector3(40,1.0,-22+i*7),1.4,i)
	_prop("Dock_3m",Vector3(49,0,12),2.0,PI*.5)
	var buoy_scene := (load("res://art/Course_buoy.glb") as PackedScene).instantiate()
	var buoy_mesh: Mesh = (buoy_scene.find_children("*","MeshInstance3D",true,false)[0] as MeshInstance3D).mesh
	var buoys := MultiMesh.new()
	buoys.transform_format = MultiMesh.TRANSFORM_3D
	buoys.mesh = buoy_mesh
	buoys.instance_count = 120
	for i in 60:
		var a := float(i)/60*TAU
		var side := HydroCourse.tangent(a).cross(Vector3.UP)
		for edge in 2:
			var p := HydroCourse.point(a)+side*(HydroCourse.WIDTH*.55)*(1 if edge==0 else -1)
			p.y = .06
			buoys.set_instance_transform(i*2+edge,Transform3D(Basis.IDENTITY,p))
	var buoy_batch := MultiMeshInstance3D.new()
	buoy_batch.multimesh = buoys
	buoy_scene.free()
	add_child(buoy_batch)
	_start_arch()
	for i in [4,11,16]:
		var a := float(i)/HydroCourse.GATES*TAU
		var p := HydroCourse.point(a)+HydroCourse.tangent(a).cross(Vector3.UP)*5.0
		_ramp(p,a)
	for i in [3,7,12,17]:
		var p := HydroCourse.gate(i)
		var pickup := Node3D.new()
		pickup.position = p+Vector3.UP*1.3
		add_child(pickup)
		var ring := TorusMesh.new()
		ring.inner_radius = .50
		ring.outer_radius = .66
		ring.rings = 16
		ring.ring_segments = 8
		var visual := MeshInstance3D.new()
		visual.mesh = ring
		visual.material_override = _material(TEAL,.22)
		visual.rotation.x = PI*.5
		pickup.add_child(visual)
		var battery := MeshInstance3D.new()
		var battery_mesh := BoxMesh.new()
		battery_mesh.size = Vector3(.28,.65,.28)
		battery.mesh = battery_mesh
		battery.material_override = _material(Color("fff0a4"),.25)
		pickup.add_child(battery)
		pickup_nodes.append(pickup)
		pickup_cooldowns.append(0.0)

func _prop(asset: String, p: Vector3, size: float, yaw: float) -> void:
	var scene_resource := load("res://art/%s.glb" % asset) as PackedScene
	if not scene_resource:
		return
	var prop := scene_resource.instantiate() as Node3D
	prop.position = p
	if asset in ["Palm_tree","Coastal_rocks","Beach_umbrella"]:
		prop.position.y = _terrain_height(p)-.08
	prop.scale = Vector3.ONE*size
	prop.rotation.y = yaw
	add_child(prop)
	for mesh in prop.find_children("*","MeshInstance3D",true,false):
		mesh.visibility_range_end = 220.0
		mesh.visibility_range_end_margin = 15.0

func _start_arch() -> void:
	var p := HydroCourse.point(0)
	var direction := HydroCourse.tangent(0)
	var side := direction.cross(Vector3.UP)
	var material := _material(INK,.3)
	for sign_value in [-1,1]:
		var pillar := CylinderMesh.new()
		pillar.top_radius = .23
		pillar.bottom_radius = .34
		pillar.height = 5
		_mesh(pillar,_material(TEAL),p+side*sign_value*11+Vector3.UP*2.5)
	var beam := BoxMesh.new()
	beam.size = Vector3(22.5,1.1,.7)
	var header := _mesh(beam,material,p+Vector3.UP*4.9)
	header.rotation.y = atan2(-direction.x,-direction.z)
	var title := Label3D.new()
	title.text = "HYDRO DRIFT"
	title.font_size = 120
	title.pixel_size = .013
	title.modulate = Color.WHITE
	title.outline_size = 8
	title.position = p-direction*.4+Vector3.UP*4.95
	title.rotation.y = header.rotation.y
	add_child(title)

func _ramp(p: Vector3, angle: float) -> void:
	var body := StaticBody3D.new()
	body.position = p
	var direction := HydroCourse.tangent(angle)
	body.rotation.y = atan2(-direction.x,-direction.z)
	add_child(body)
	var points := PackedVector3Array([Vector3(-2.5,0,4),Vector3(2.5,0,4),Vector3(-2.5,0,-4),Vector3(2.5,0,-4),Vector3(-2.5,1.4,-4),Vector3(2.5,1.4,-4)])
	var shape := ConvexPolygonShape3D.new()
	shape.points = points
	var collision := CollisionShape3D.new()
	collision.shape = shape
	body.add_child(collision)
	var model := (load("res://art/Jump_ramp.glb") as PackedScene).instantiate() as Node3D
	model.rotation.y = PI
	body.add_child(model)

func _terrain_height(p: Vector3) -> float:
	var r := Vector2(p.x/54.0,p.z/83.0).length()
	var radii := [0.0,.4,.65,.82,.95,1.0,1.18]
	var heights := [2.65,2.5,1.8,.9,.2,-.08,-1.0]
	for i in range(1,radii.size()):
		if r<=radii[i]:return lerpf(heights[i-1],heights[i],inverse_lerp(radii[i-1],radii[i],r))
	return -1.0

func _style(color: Color, radius: int = 10) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = color
	s.corner_radius_top_left = radius
	s.corner_radius_top_right = radius
	s.corner_radius_bottom_left = radius
	s.corner_radius_bottom_right = radius
	s.content_margin_left = 16
	s.content_margin_right = 16
	s.content_margin_top = 12
	s.content_margin_bottom = 12
	return s

func _label(text: String, size: int, color: Color = Color.WHITE) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size",size)
	label.add_theme_color_override("font_color",color)
	return label

func _button(text: String, callback: Callable, accent: bool = false) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size.y = 44
	button.add_theme_stylebox_override("normal",_style(TEAL if accent else Color("163747"),7))
	button.add_theme_stylebox_override("hover",_style(Color("54e9d4") if accent else Color("245063"),7))
	button.add_theme_stylebox_override("pressed",_style(Color("298d86"),7))
	button.add_theme_stylebox_override("focus",_style(Color(.2,.65,.65,.28),7))
	button.add_theme_color_override("font_color",INK if accent else Color.WHITE)
	button.add_theme_font_size_override("font_size",17)
	button.pressed.connect(callback)
	return button

func _column(parent: Node, separation: int = 12) -> VBoxContainer:
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation",separation)
	parent.add_child(column)
	return column

func _build_ui() -> void:
	var canvas := CanvasLayer.new()
	add_child(canvas)
	root_ui = Control.new()
	root_ui.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root_ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
	canvas.add_child(root_ui)
	var theme := Theme.new()
	var font := SystemFont.new()
	font.font_names = PackedStringArray(["Bahnschrift","Segoe UI"])
	theme.default_font = font
	root_ui.theme = theme
	menu_panel = PanelContainer.new()
	menu_panel.position = Vector2(44,32)
	menu_panel.custom_minimum_size = Vector2(450,0)
	menu_panel.add_theme_stylebox_override("panel",_style(Color(.025,.075,.105,.95),18))
	root_ui.add_child(menu_panel)
	var menu := _column(menu_panel,10)
	menu.add_child(_label("SUNBEAM LAGOON  /  FIRST RIDE",13,TEAL))
	menu.add_child(_label("HYDRO DRIFT",45))
	menu.add_child(_label("Steel armor. Salt water.",19,MUTED))
	menu.add_child(HSeparator.new())
	menu.add_child(_label("01   CHOOSE YOUR KNIGHT",13,MUTED))
	var grid := GridContainer.new()
	grid.columns = 4
	grid.add_theme_constant_override("h_separation",8)
	grid.add_theme_constant_override("v_separation",8)
	menu.add_child(grid)
	for i in RIDERS.size():
		var b := _button(RIDERS[i],func(): chosen_rider=i;_make_preview();_refresh_choices())
		b.custom_minimum_size.x = 97
		grid.add_child(b)
		rider_buttons.append(b)
	menu.add_child(_label("02   CHOOSE YOUR CRAFT",13,MUTED))
	var crafts := HBoxContainer.new()
	crafts.add_theme_constant_override("separation",8)
	menu.add_child(crafts)
	for i in 3:
		var b := _button(CRAFT_NAMES[i],func(): chosen_craft=i;_make_preview();_refresh_choices())
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		crafts.add_child(b)
		craft_buttons.append(b)
	menu.add_child(_label("Needle: agile     Surge: balanced     Leviathan: power",12,MUTED))
	var graphics := OptionButton.new()
	graphics.add_item("Performance · 720p internal",0)
	graphics.add_item("Balanced · 900p internal",1)
	graphics.add_item("Native · 1080p internal",2)
	graphics.selected = quality
	graphics.custom_minimum_size.y = 36
	graphics.item_selected.connect(_apply_quality)
	menu.add_child(graphics)
	menu.add_child(_button("RACE   /   8 KNIGHTS",func():time_trial=false;start_race(),true))
	menu.add_child(_button("TIME TRIAL",func():time_trial=true;start_race()))
	menu.add_child(_label("WASD / arrows · steer & throttle\nSHIFT · drift    CTRL / E · boost    SPACE · hop\nR · recover    ESC · pause    F3 · stats    F11 · fullscreen",13,MUTED))
	menu.add_child(_label("Controller: triggers · throttle/brake   RB · drift   X · boost",11,MUTED))
	var quit := _button("EXIT",func():get_tree().quit())
	quit.custom_minimum_size.y = 30
	menu.add_child(quit)
	hud = Control.new()
	hud.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root_ui.add_child(hud)
	hud.hide()
	minimap = load("res://scripts/minimap.gd").new()
	minimap.race = self
	minimap.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
	minimap.position = Vector2(-226,-240)
	minimap.custom_minimum_size = Vector2(200,214)
	hud.add_child(minimap)
	var top := PanelContainer.new()
	top.position = Vector2(26,22)
	top.custom_minimum_size = Vector2(390,0)
	top.add_theme_stylebox_override("panel",_style(Color(.02,.07,.10,.88)))
	hud.add_child(top)
	var info := _column(top,3)
	race_label = _label("LAP 1 / 3    ·    1 / 8",22)
	info.add_child(race_label)
	time_label = _label("00:00.00    SUNBEAM LAGOON",13,MUTED)
	info.add_child(time_label)
	status_label = _label("Next gate: 01",12,TEAL)
	info.add_child(status_label)
	var bottom := PanelContainer.new()
	bottom.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	bottom.position = Vector2(26,-143)
	bottom.custom_minimum_size = Vector2(270,0)
	bottom.add_theme_stylebox_override("panel",_style(Color(.02,.07,.10,.9)))
	hud.add_child(bottom)
	var speed_box := _column(bottom,4)
	speed_label = _label("0  KM/H",38)
	speed_box.add_child(speed_label)
	boost_bar = ProgressBar.new()
	boost_bar.custom_minimum_size = Vector2(238,11)
	boost_bar.show_percentage = false
	boost_bar.add_theme_stylebox_override("background",_style(Color("20404b"),4))
	boost_bar.add_theme_stylebox_override("fill",_style(TEAL,4))
	speed_box.add_child(boost_bar)
	speed_box.add_child(_label("BOOST    CTRL / E       DRIFT    SHIFT",11,MUTED))
	center_label = _label("",64)
	center_label.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	center_label.position = Vector2(-240,-80)
	center_label.custom_minimum_size = Vector2(480,140)
	center_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	center_label.add_theme_color_override("font_shadow_color",Color(.01,.03,.05,.8))
	center_label.add_theme_constant_override("shadow_offset_x",3)
	center_label.add_theme_constant_override("shadow_offset_y",3)
	hud.add_child(center_label)
	toast_label = _label("",22,TEAL)
	toast_label.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP)
	toast_label.position = Vector2(-260,122)
	toast_label.custom_minimum_size.x = 520
	toast_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hud.add_child(toast_label)
	telemetry_label = _label("",13,Color("e3f2c8"))
	telemetry_label.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	telemetry_label.position = Vector2(-325,25)
	telemetry_label.add_theme_color_override("font_shadow_color",Color.BLACK)
	telemetry_label.add_theme_constant_override("shadow_offset_x",1)
	telemetry_label.add_theme_constant_override("shadow_offset_y",1)
	telemetry_label.visible = benchmark or smoke
	root_ui.add_child(telemetry_label)
	pause_panel = PanelContainer.new()
	pause_panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	pause_panel.position = Vector2(-180,-160)
	pause_panel.custom_minimum_size = Vector2(360,300)
	pause_panel.add_theme_stylebox_override("panel",_style(Color(.02,.07,.10,.98)))
	root_ui.add_child(pause_panel)
	var pause_box := _column(pause_panel)
	pause_box.add_child(_label("TAKE A BREATHER",28))
	pause_box.add_child(_button("RESUME",_toggle_pause,true))
	pause_box.add_child(_button("RESTART RACE",func():get_tree().paused=false;start_race()))
	pause_box.add_child(_button("RIDER SELECT",_return_to_menu))
	pause_box.add_child(_button("MUTE / UNMUTE",func():muted=not muted;_save_settings()))
	pause_panel.hide()
	results_panel = PanelContainer.new()
	results_panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	results_panel.position = Vector2(-250,-200)
	results_panel.custom_minimum_size = Vector2(500,350)
	results_panel.add_theme_stylebox_override("panel",_style(Color(.02,.07,.10,.98)))
	root_ui.add_child(results_panel)
	results_panel.hide()
	_refresh_choices()

func _refresh_choices() -> void:
	for i in rider_buttons.size():
		rider_buttons[i].add_theme_stylebox_override("normal",_style(Color("28766f") if i==chosen_rider else Color("163747"),7))
	for i in craft_buttons.size():
		craft_buttons[i].add_theme_stylebox_override("normal",_style(Color("28766f") if i==chosen_craft else Color("163747"),7))
	_save_settings()

func _apply_quality(index: int) -> void:
	quality = clampi(index,0,2)
	if is_instance_valid(sun):
		sun.directional_shadow_max_distance = [65.0,90.0,115.0][quality]
	get_viewport().msaa_3d = Viewport.MSAA_2X if quality>0 else Viewport.MSAA_DISABLED
	_resolution_scale()
	if is_instance_valid(root_ui):
		_save_settings()

func _resolution_scale() -> void:
	var actual := maxf(1,float(get_viewport().size.y))
	get_viewport().scaling_3d_scale = clampf([720.0,900.0,1080.0][quality]/actual,.5,1.5)

func _clear_racers() -> void:
	for racer in racers:
		remove_child(racer)
		racer.queue_free()
	racers.clear()

func _spawn_racer(index: int, rider: String, craft: int, is_player: bool) -> HydroCraft:
	var racer := HydroCraft.new()
	racer.race = self
	racer.pilot_index = index
	racer.rider_name = rider
	racer.craft_index = craft
	racer.human = is_player
	var direction := HydroCourse.tangent(0)
	var side := direction.cross(Vector3.UP)
	racer.position = HydroCourse.point(0) - direction*(9.0+floori(index/2.0)*5.0) + side*((index%2)*4.5-2.25)+Vector3.UP*.7
	racer.rotation.y = atan2(-direction.x,-direction.z)
	racer.process_mode = Node.PROCESS_MODE_PAUSABLE
	add_child(racer)
	racers.append(racer)
	return racer

func _make_preview() -> void:
	if mode != "menu":
		return
	_clear_racers()
	player = _spawn_racer(0,RIDERS[chosen_rider],chosen_craft,true)
	player.freeze = true
	player.position = HydroCourse.point(0)+Vector3(0,-.14,-2)

func start_race() -> void:
	get_tree().paused = false
	mode = "countdown"
	race_time = 0.0
	countdown = 3.2
	recovery_count = 0
	menu_panel.hide()
	pause_panel.hide()
	results_panel.hide()
	hud.show()
	_clear_racers()
	player = _spawn_racer(0,RIDERS[chosen_rider],chosen_craft,true)
	for i in range(1,1 if time_trial else 8):
		_spawn_racer(i,RIDERS[(chosen_rider+i)%8],i%3,false)
	for racer in racers:
		racer.active = false
		racer.freeze = true
	for i in pickup_cooldowns.size():
		pickup_cooldowns[i] = 0.0
	camera.global_position = player.global_position + player.global_basis.z*9.0 + Vector3.UP*4.5
	camera.look_at(player.global_position+Vector3.UP*1.0)
	_save_settings()

func _return_to_menu() -> void:
	get_tree().paused = false
	mode = "menu"
	menu_panel.show()
	pause_panel.hide()
	results_panel.hide()
	hud.hide()
	_make_preview()

func _toggle_pause() -> void:
	if mode not in ["race","countdown"]:
		return
	get_tree().paused = not get_tree().paused
	pause_panel.visible = get_tree().paused

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause"):
		_toggle_pause()
	if event.is_action_pressed("mute"):
		muted = not muted
		_save_settings()
	if event.is_action_pressed("telemetry"):
		telemetry_label.visible = not telemetry_label.visible
	if event.is_action_pressed("fullscreen"):
		get_window().mode = Window.MODE_WINDOWED if get_window().mode==Window.MODE_FULLSCREEN else Window.MODE_FULLSCREEN

func _process(delta: float) -> void:
	if get_tree().paused:
		_update_audio()
		return
	water_time += delta
	water_material.set_shader_parameter("wave_time",water_time)
	if mode == "countdown":
		countdown -= delta
		center_label.text = str(ceili(countdown)) if countdown>0 else "GO!"
		if countdown <= 0:
			mode = "race"
			for racer in racers:
				racer.freeze = false
				racer.active = true
	if mode == "race":
		race_time += delta
		center_label.text = "GO!" if race_time<.8 else ""
		_update_pickups(delta)
	for racer in racers:
		racer.update_wake(delta)
	_update_camera(delta)
	_update_audio()
	hud_update += delta
	if hud_update >= .10:
		hud_update = 0.0
		_update_hud()
	if toast_time > 0:
		toast_time -= delta
		if toast_time<=0:toast_label.text=""
	if benchmark or smoke:
		_record_benchmark(delta)

func _update_camera(delta: float) -> void:
	if not is_instance_valid(player):
		return
	if mode == "menu":
		player.position.y = HydroCourse.wave(player.position,water_time)-.14
		var angle := water_time*.075 + .60
		var anchor := player.global_position
		camera.position = anchor + Vector3(cos(angle)*4.5,2.3,sin(angle)*4.5)
		var camera_right := Vector3(sin(angle),0,-cos(angle))
		camera.look_at(anchor+Vector3.UP*.8-camera_right*1.25)
		camera.fov = 46
		return
	var behind := player.global_basis.z
	behind.y = 0
	behind = behind.normalized()
	var p := player.global_position
	var desired := p+behind*(6.8+minf(player.speed_kph,110.0)*.012)+Vector3.UP*3.0
	var space := get_world_3d().direct_space_state
	var query := PhysicsRayQueryParameters3D.create(p+Vector3.UP*1.6,desired)
	query.exclude = [player.get_rid()]
	var hit := space.intersect_ray(query)
	if not hit.is_empty():
		desired = hit.position + hit.normal*.6
	camera.global_position = camera.global_position.lerp(desired,1.0-exp(-delta*6.0))
	var focus := p+Vector3.UP*.9 - behind*4.5 + player.global_basis.x*(-player.steer*.7)
	camera.look_at(focus)
	camera.fov = lerpf(camera.fov,65.0+(8.0 if player.boosting else 0.0),1.0-exp(-delta*3.0))

func _update_pickups(delta: float) -> void:
	for i in pickup_nodes.size():
		var pickup := pickup_nodes[i]
		pickup_cooldowns[i] = maxf(0,pickup_cooldowns[i]-delta)
		pickup.visible = pickup_cooldowns[i]<=0.0
		pickup.rotation.y += delta
		pickup.position.y = 1.3+sin(water_time*2.0+i)*.15
		if not pickup.visible:continue
		for racer in racers:
			if racer.global_position.distance_squared_to(pickup.global_position)<15.0:
				racer.boost = minf(100,racer.boost+35.0)
				pickup_cooldowns[i] = 8.0
				if racer==player:
					pickup_count += 1
					toast_label.text = "+35 BOOST"
					toast_time = 1.2
				break

func _update_hud() -> void:
	if not is_instance_valid(player):return
	minimap.queue_redraw()
	var place := 1
	for racer in racers:
		if racer!=player and racer.progress_score()>player.progress_score():place+=1
	race_label.text = "LAP %d / %d    ·    %d / %d" % [mini(lap_limit,1+maxi(0,player.passed)/HydroCourse.GATES),lap_limit,place,racers.size()]
	time_label.text = "%s    SUNBEAM LAGOON" % _time_string(race_time)
	status_label.text = "GATE %02d / %02d   ·   %s" % [player.next_gate+1,HydroCourse.GATES, "DRIFT CHARGING" if player.drifting else ("BOOSTING" if player.boosting else "FIND YOUR LINE")]
	speed_label.text = "%d  KM/H" % roundi(player.speed_kph)
	boost_bar.value = player.boost
	var texture_mb := Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED)/1048576.0
	var buffer_mb := Performance.get_monitor(Performance.RENDER_BUFFER_MEM_USED)/1048576.0
	telemetry_label.text = "%d FPS    %.2f ms CPU\n%.2f ms physics    %d draws\n%d primitives    %.0f MB renderer\n%s" % [Engine.get_frames_per_second(),Performance.get_monitor(Performance.TIME_PROCESS)*1000,Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS)*1000,int(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)),int(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)),texture_mb+buffer_mb,RenderingServer.get_video_adapter_name()]

func _update_audio() -> void:
	if engine_playback == null:return
	var count := mini(engine_playback.get_frames_available(),4096)
	var sounding := mode=="race" and not muted and not get_tree().paused and is_instance_valid(player)
	var frequency := 48.0 + (player.speed_kph*.72 if is_instance_valid(player) else 0.0)
	for i in count:
		audio_phase = fposmod(audio_phase+frequency/22050.0,1.0)
		var value := (sin(audio_phase*TAU)*.5+sin(audio_phase*TAU*2)*.21+sin(audio_phase*TAU*4)*.07)*(.45 if sounding else 0.0)
		engine_playback.push_frame(Vector2(value,value))

func racer_finished(racer: HydroCraft) -> void:
	if racer!=player:return
	race_finishes += 1
	if benchmark or smoke:
		call_deferred("_restart_automated")
		return
	mode = "results"
	center_label.text = ""
	for child in results_panel.get_children():
		results_panel.remove_child(child)
		child.queue_free()
	var box := _column(results_panel,12)
	var position_in_race := 1
	for rival in racers:
		if rival!=player and rival.finished and rival.finish_time<player.finish_time:position_in_race+=1
	box.add_child(_label("RACE COMPLETE",15,TEAL))
	box.add_child(_label("%s PLACE" % ["1ST","2ND","3RD","4TH","5TH","6TH","7TH","8TH"][position_in_race-1],42))
	box.add_child(_label("%s   /   %s" % [RIDERS[chosen_rider],CRAFT_NAMES[chosen_craft]],18,MUTED))
	box.add_child(_label(_time_string(race_time),32))
	var best := float(settings.get_value("records","sunbeam_best",99999.0))
	if time_trial and race_time<best:
		settings.set_value("records","sunbeam_best",race_time)
		_save_settings()
		box.add_child(_label("NEW TIME TRIAL BEST",16,TEAL))
	box.add_child(_button("RACE AGAIN",start_race,true))
	box.add_child(_button("RIDER SELECT",_return_to_menu))
	results_panel.show()

func _restart_automated() -> void:
	start_race()
	player.automated = true
	countdown = .1

func _time_string(value: float) -> String:
	return "%02d:%05.2f" % [int(value)/60,fmod(value,60.0)]

func _record_benchmark(delta: float) -> void:
	var now := Time.get_ticks_usec()
	var wall_delta := float(now-last_frame_us)/1000000.0
	last_frame_us = now
	benchmark_elapsed += wall_delta
	if benchmark_elapsed>benchmark_warmup:
		samples.append(wall_delta*1000.0)
		if wall_delta>.022 and slow_frames.size()<120:
			slow_frames.append({"elapsed":benchmark_elapsed,"frame_ms":wall_delta*1000.0,"process_ms":Performance.get_monitor(Performance.TIME_PROCESS)*1000.0,"physics_ms":Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS)*1000.0,"draw_calls":Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)})
		memory_peak = maxf(memory_peak,Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED))
		draw_peak = maxi(draw_peak,int(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)))
		primitive_peak = maxi(primitive_peak,int(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)))
	# GPU readback for review belongs in warm-up, outside measured gameplay.
	if not capture_done and benchmark_elapsed>5.0 and DisplayServer.get_name()!="headless":
		capture_done = true
		_capture.call_deferred()
	if benchmark_elapsed>=benchmark_duration:
		_write_benchmark()

func _capture() -> void:
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	var path := ProjectSettings.globalize_path("res://../benchmarks")
	DirAccess.make_dir_recursive_absolute(path)
	image.save_png(path+"/prototype.png")

func _write_benchmark() -> void:
	var total := 0.0
	for sample in samples:total+=sample
	samples.sort()
	var slow_count := maxi(1,ceili(samples.size()*.01))
	var slow := 0.0
	for i in range(maxi(0,samples.size()-slow_count),samples.size()):slow+=samples[i]
	var progress: Array = []
	for racer in racers:
		progress.append({"rider":racer.rider_name,"passed_gates":racer.passed,"next_gate":racer.next_gate,"speed_kph":racer.speed_kph,"position":[racer.position.x,racer.position.y,racer.position.z]})
	var report := {"kind":"headless smoke" if smoke else "rendered benchmark","duration_seconds":benchmark_elapsed,"adapter":RenderingServer.get_video_adapter_name(),"renderer":RenderingServer.get_current_rendering_method(),"resolution":str(get_viewport().get_visible_rect().size),"scale_3d":get_viewport().scaling_3d_scale,"quality":quality,"average_fps":1000.0/maxf(.001,total/maxi(1,samples.size())),"one_percent_low_fps":1000.0/maxf(.001,slow/slow_count),"peak_renderer_memory_bytes":memory_peak,"peak_draw_calls":draw_peak,"peak_primitives":primitive_peak,"race_finishes":race_finishes,"recoveries_current_race":recovery_count,"riders":progress,"notes":"Renderer memory excludes driver/desktop allocations. Headless results do not measure GPU performance."}
	var folder := ProjectSettings.globalize_path("res://../benchmarks")
	report["fps_cap"] = Engine.max_fps
	report["asset_revision"] = 4
	report["warmup_seconds"] = benchmark_warmup
	report["vsync"] = DisplayServer.window_get_vsync_mode()
	report["slow_frames_over_22ms"] = slow_frames
	report["output_pixels"] = str(get_viewport().size)
	report["internal_pixels"] = str(Vector2i(Vector2(get_viewport().size)*get_viewport().scaling_3d_scale))
	report["fullscreen"] = get_window().mode == Window.MODE_FULLSCREEN
	DirAccess.make_dir_recursive_absolute(folder)
	var file := FileAccess.open(folder+("/smoke.json" if smoke else "/performance_%dp.json" % [720,900,1080][quality]),FileAccess.WRITE)
	if file:file.store_string(JSON.stringify(report,"\t"))
	print("HYDRO_BENCHMARK ",JSON.stringify(report))
	get_tree().quit()

func _exit_tree() -> void:
	if is_instance_valid(engine_audio):
		engine_audio.stop()
	engine_playback = null
