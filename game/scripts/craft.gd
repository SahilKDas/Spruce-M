class_name HydroCraft
extends RigidBody3D

var race: Node3D
var pilot_index := 0
var rider_name := "Kai"
var craft_index := 0
var human := false
var automated := false
var active := false
var next_gate := 0
var passed := -1
var finished := false
var finish_time := 0.0
var last_position := Vector3.ZERO
var throttle := 0.0
var steer := 0.0
var drifting := false
var drift_direction := 0.0
var mini_turbo_remaining := 0.0
var on_water := true
var grip_blend := 0.0
var hop_buffer := 0.0
var boosting := false
var boost := 65.0
var drift_charge := 0.0
var jump_request := false
var jump_cooldown := 0.0
var speed_kph := 0.0
var off_course_time := 0.0
var physics_steps := 0
var ai_timer := 0.0
var ai_target := Vector3.ZERO
var sparks: CPUParticles3D
var visual: Node3D
var rider_near: Node3D
var rider_far: Node3D
var wake_mesh := ImmediateMesh.new()
var wake_node: MeshInstance3D
var wake_points: Array[Vector3] = []
var wake_clock := 0.0
var ai_best_passed := -1
var stuck_time := 0.0
const SAMPLE_POINTS := [Vector3(-.40, 0, -.86), Vector3(.40,0,-.86), Vector3(-.40,0,.86), Vector3(.40,0,.86)]
const CRAFT_FILES := ["01_Needle_Agile", "02_Surge_Balanced", "03_Leviathan_Power"]

func _ready() -> void:
	mass = 180.0
	linear_damp = 0.0
	angular_damp = 1.4
	continuous_cd = true
	can_sleep = false
	contact_monitor = true
	max_contacts_reported = 4
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(1.1,.55,3.05)
	shape.shape = box
	shape.position.y = .35
	add_child(shape)
	physics_material_override = PhysicsMaterial.new()
	physics_material_override.friction = .15
	physics_material_override.bounce = .05
	visual = Node3D.new()
	add_child(visual)
	var model := load("res://art/%s%s.glb" % [CRAFT_FILES[craft_index],"" if human else "_far"]) as PackedScene
	if model:
		var craft := model.instantiate() as Node3D
		craft.rotation.y = PI
		visual.add_child(craft)
	if human:
		rider_near = _load_rider("near")
	rider_far = _load_rider("far")
	if rider_near:
		rider_far.visible = false
	wake_node = MeshInstance3D.new()
	wake_node.mesh = wake_mesh
	wake_node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var foam := StandardMaterial3D.new()
	foam.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	foam.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	foam.vertex_color_use_as_albedo = true
	foam.cull_mode = BaseMaterial3D.CULL_DISABLED
	wake_node.material_override = foam
	race.add_child.call_deferred(wake_node)
	last_position = global_position
	if human:_make_sparks()

func _load_rider(detail: String) -> Node3D:
	var resource := load("res://art/%s_%s.glb" % [rider_name,detail]) as PackedScene
	if not resource:
		return null
	var model := resource.instantiate() as Node3D
	model.rotation.y = PI
	visual.add_child(model)
	for node in model.find_children("*", "AnimationPlayer", true, false):
		var animation_player := node as AnimationPlayer
		for animation in animation_player.get_animation_list():
			if animation != "RESET":
				animation_player.play(animation)
				animation_player.seek(0.0, true)
				animation_player.pause()
				break
	return model

func _physics_process(delta: float) -> void:
	physics_steps += 1
	speed_kph = Vector2(linear_velocity.x,linear_velocity.z).length() * 3.6
	jump_cooldown = maxf(0, jump_cooldown - delta)
	if not active or finished:
		throttle = 0.0
		steer = 0.0
		boosting = false
		return
	if human and not automated:
		throttle = Input.get_action_strength("accelerate") - Input.get_action_strength("brake")
		steer = HydroHandling.steering_input(steer,Input.get_axis("steer_right", "steer_left"),delta)
		drifting = Input.is_action_pressed("drift") and speed_kph > 20.0
		boosting = Input.is_action_pressed("boost") and boost > 0.0 and throttle > 0.0
		jump_request = Input.is_action_just_pressed("hop")
	else:
		_drive_ai(delta)
	if jump_request:hop_buffer = .14
	hop_buffer = maxf(0.0,hop_buffer-delta)
	grip_blend = move_toward(grip_blend,1.0 if drifting else 0.0,delta*(7.0 if drifting else 4.0))
	var manual_boost := boosting
	mini_turbo_remaining = maxf(0.0,mini_turbo_remaining-delta)
	if drifting and drift_direction==0.0:
		if on_water and absf(steer)>.20:
			drift_direction = signf(steer)
		else:drifting = false
	if drifting:
		if on_water:drift_charge = minf(1.0,drift_charge+delta*(.32+.18*maxf(0.0,steer*drift_direction)))
	else:
		mini_turbo_remaining = maxf(mini_turbo_remaining,HydroHandling.mini_turbo_duration(drift_charge))
		if drift_charge>.15:boost = minf(100.0,boost+drift_charge*32.0)
		drift_charge = 0.0
		drift_direction = 0.0
	boosting = manual_boost or mini_turbo_remaining>0.0
	if manual_boost:boost = maxf(0.0,boost-delta*25.0)
	else:boost = minf(100.0,boost+delta*3.5)
	if race.mode!="explore" and HydroCourse.crossed_gate(last_position, global_position, next_gate):
		passed += 1
		next_gate = (next_gate + 1) % HydroCourse.GATES
		if passed >= HydroCourse.GATES * race.lap_limit:
			finished = true
			finish_time = race.race_time
			race.racer_finished(self)
	last_position = global_position
	var angle := HydroCourse.nearest_angle(global_position)
	var deviation := global_position.distance_to(HydroCourse.point(angle))
	if (race.mode!="explore" and deviation>32.0) or Vector2(global_position.x,global_position.z).length()>820.0 or global_position.y < -8.0 or global_position.y > 40.0:
		off_course_time += delta
	else:
		off_course_time = 0.0
	if passed > ai_best_passed:
		ai_best_passed = passed
		stuck_time = 0.0
	else:
		stuck_time += delta
	if off_course_time > 5.0 or (not human and stuck_time > 15.0):
		respawn()
	if human and not automated and Input.is_action_just_pressed("reset"):
		respawn()
	visual.rotation.z = lerpf(visual.rotation.z, steer * (-.23 if drifting else -.11), 1.0-exp(-delta*10.0))
	if not human:
		var away := global_position.distance_squared_to(race.camera.global_position)
		visible = away < 260.0 * 260.0

func _drive_ai(delta: float) -> void:
	ai_timer -= delta
	if ai_timer <= 0.0:
		ai_timer = .09 + pilot_index * .006
		var angle := HydroCourse.nearest_angle(global_position)
		var gate_angle := float(next_gate) / HydroCourse.GATES * TAU
		var gap := fposmod(gate_angle - angle, TAU)
		var lookahead := .14 + minf(speed_kph,100.0) * .0009
		var target_angle := angle + minf(lookahead, gap + .015)
		if gap > PI:
			target_angle = gate_angle
		var lane := (float(pilot_index % 3)-1.0) * 2.8
		ai_target = HydroCourse.point(target_angle) + HydroCourse.tangent(target_angle).cross(Vector3.UP) * lane
	var direction := ai_target - global_position
	direction.y = 0.0
	var heading := -global_basis.z
	heading.y = 0.0
	var error := heading.normalized().signed_angle_to(direction.normalized(),Vector3.UP)
	steer = clampf(error * 2.8,-1.0,1.0)
	throttle = clampf(1.0-absf(error)*.5,.25,1.0)
	boosting = absf(error)<.08 and boost > 70.0 and speed_kph>45.0
	drifting = absf(error)>.38 and absf(error)<.75 and speed_kph>55.0
	jump_request = false

func _integrate_forces(state: PhysicsDirectBodyState3D) -> void:
	var dt := state.step
	var origin := state.transform.origin
	var basis := state.transform.basis.orthonormalized()
	var wet := 0
	for sample in SAMPLE_POINTS:
		var offset: Vector3 = basis * sample
		var p := origin + offset
		var depth := HydroCourse.wave(p, race.water_time) + .10 - p.y
		if depth > 0.0:
			wet += 1
			var local_speed := state.linear_velocity + state.angular_velocity.cross(offset)
			var lift := clampf(depth * 1850.0 - local_speed.y * 250.0,0.0,3400.0)
			state.apply_force(Vector3.UP * lift,offset)
	var query := PhysicsRayQueryParameters3D.create(origin+Vector3.UP*.4,origin-Vector3.UP*1.0)
	query.exclude = [get_rid()]
	var ground := get_world_3d().direct_space_state.intersect_ray(query)
	var on_land: bool = not ground.is_empty() and ground.normal.y>.45 and ground.position.y>HydroCourse.wave(origin,race.water_time)-.12
	on_water = wet>0 or on_land
	var forward := -basis.z
	forward.y = 0.0
	forward = forward.normalized()
	var right := forward.cross(Vector3.UP).normalized()
	var speed := state.linear_velocity.dot(forward)
	if wet>0 or on_land:
		var local_velocity := Vector3(state.linear_velocity.dot(right),state.linear_velocity.y,speed)
		local_velocity = HydroHandling.drive_velocity(local_velocity,throttle,drifting,boosting,craft_index,dt,grip_blend)
		state.linear_velocity = right*local_velocity.x+Vector3.UP*local_velocity.y+forward*local_velocity.z
		if on_land:
			var ground_normal: Vector3 = ground.normal
			var horizontal := Vector3(state.linear_velocity.x,0,state.linear_velocity.z)
			state.linear_velocity.y = maxf(state.linear_velocity.y,-horizontal.dot(ground_normal)/maxf(.45,ground_normal.y))
		var yaw := HydroHandling.yaw_target(steer,speed,drift_direction if drifting else 0.0,craft_index)
		state.angular_velocity.y = lerpf(state.angular_velocity.y,yaw,1.0-exp(-dt*14.0))
		if hop_buffer>0.0 and jump_cooldown <= 0 and active:
			state.apply_central_impulse(Vector3.UP * mass * 3.1)
			jump_cooldown = .65
			hop_buffer = 0.0
			jump_request = false
	if wet==0 and not on_land:
		# Modest air control keeps ramp exits steerable without ground-level grip.
		var air_yaw := HydroHandling.yaw_target(steer,speed,0.0,craft_index)*.35
		state.angular_velocity.y = lerpf(state.angular_velocity.y,air_yaw,1.0-exp(-dt*4.0))
	var correction := basis.y.cross(Vector3.UP) * mass * 34.0
	correction -= Vector3(state.angular_velocity.x,0,state.angular_velocity.z) * mass * 7.0
	state.apply_torque(correction)

func update_wake(delta: float) -> void:
	if not is_instance_valid(wake_node):return
	wake_clock += delta
	var presented := get_global_transform_interpolated()
	var head := presented.origin+presented.basis.z*1.5
	head.y = HydroCourse.wave(head,race.render_water_time)+.06
	if wake_clock>=.065:
		wake_clock = fmod(wake_clock,.065)
		if speed_kph>5.0:wake_points.push_front(head)
		elif not wake_points.is_empty():wake_points.pop_back()
	while wake_points.size() > (18 if human else 10):
		wake_points.pop_back()
	wake_mesh.clear_surfaces()
	if wake_points.size()<2:
		return
	wake_mesh.surface_begin(Mesh.PRIMITIVE_TRIANGLE_STRIP)
	for i in wake_points.size():
		var p := head if i==0 else wake_points[i]
		p.y = HydroCourse.wave(p,race.render_water_time)+.06
		var previous := head if i==1 else wake_points[maxi(0,i-1)]
		var direction := presented.basis.z if i==0 else (p-previous).normalized()
		var side := direction.cross(Vector3.UP).normalized()
		var width := .4 + i * .085
		var alpha := (1.0-float(i)/wake_points.size())*.45
		wake_mesh.surface_set_color(Color(.77,.96,1.0,alpha))
		wake_mesh.surface_add_vertex(p + side * width)
		wake_mesh.surface_add_vertex(p - side * width)
	wake_mesh.surface_end()

func respawn() -> void:
	var index := (next_gate - 1 + HydroCourse.GATES) % HydroCourse.GATES
	var angle := float(index)/HydroCourse.GATES*TAU
	var p := HydroCourse.point(angle) + HydroCourse.tangent(angle) * 5.0
	if passed < 0:
		p = HydroCourse.point(0.0)-HydroCourse.tangent(0.0)*8.0
		angle = 0.0
	if race.mode=="explore":p = race.adventure.safe_position
	position = p + Vector3.UP*.65
	rotation = Vector3(0,atan2(-HydroCourse.tangent(angle).x,-HydroCourse.tangent(angle).z),0)
	linear_velocity = Vector3.ZERO
	angular_velocity = Vector3.ZERO
	last_position = position
	off_course_time = 0.0
	stuck_time = 0.0
	wake_points.clear()
	drifting = false
	drift_direction = 0.0
	drift_charge = 0.0
	mini_turbo_remaining = 0.0
	grip_blend = 0.0
	hop_buffer = 0.0
	steer = 0.0
	jump_cooldown = 0.0
	force_update_transform()
	reset_physics_interpolation()
	if human:race.reset_chase_camera()
	race.recovery_count += 1

func progress_score() -> float:
	return passed * 10000.0 - global_position.distance_to(HydroCourse.gate(next_gate))

func _exit_tree() -> void:
	if is_instance_valid(wake_node):
		wake_node.queue_free()

func _make_sparks() -> void:
	sparks = CPUParticles3D.new()
	sparks.amount = 36
	sparks.lifetime = .32
	sparks.local_coords = false
	sparks.emitting = false
	sparks.position = Vector3(0,.2,1.1)
	sparks.direction = Vector3(0,.35,1)
	sparks.spread = 55.0
	sparks.initial_velocity_min = 4.0
	sparks.initial_velocity_max = 8.0
	sparks.gravity = Vector3(0,-5,0)
	sparks.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	sparks.emission_box_extents = Vector3(.65,.02,.12)
	var mesh := BoxMesh.new()
	mesh.size = Vector3(.045,.045,.20)
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.vertex_color_use_as_albedo = true
	mesh.material = material
	sparks.mesh = mesh
	visual.add_child(sparks)

func _process(_delta: float) -> void:
	if not is_instance_valid(sparks):return
	sparks.emitting = active and ((drifting and drift_charge>=.20) or boosting)
	sparks.color = Color("ffad26") if drift_charge>=.65 or boosting else Color("44cfff")
	sparks.initial_velocity_min = 8.0 if boosting else 4.0
	sparks.initial_velocity_max = 13.0 if boosting else 8.0
