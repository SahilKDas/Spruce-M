extends Control

var race: Node3D

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE

func _point(p: Vector3) -> Vector2:
	if race.mode=="explore":return Vector2(100+p.x*.20,106+p.z*.20)
	var q := p-HydroCourse.center
	return Vector2(100+q.x*.67,106+q.z*.67)

func _draw() -> void:
	draw_style_box(race._style(Color(.02,.07,.10,.88),16),Rect2(Vector2.ZERO,Vector2(200,214)))
	if race.mode=="explore":
		for i in 4:
			var p := _point(race.adventure.CENTERS[i])
			draw_circle(p,10,race.adventure.COLORS[i])
			var box := _point(race.adventure.boxes[i].position)
			draw_rect(Rect2(box-Vector2(3,3),Vector2(6,6)),Color("39d9c8"),false,2)
		for i in race.adventure.relics.size():
			if not i in race.adventure.collected:draw_circle(_point(race.adventure.relics[i].position),2,Color("ffd769"))
		if is_instance_valid(race.player):draw_circle(_point(race.player.position),4,Color.WHITE)
		return
	var line := PackedVector2Array()
	for i in 81:
		line.append(_point(HydroCourse.point(float(i)/80*TAU)))
	draw_polyline(line,Color("426474"),14,true)
	draw_polyline(line,Color("90bdb5"),1,true)
	if not is_instance_valid(race.player):return
	var gate := _point(HydroCourse.gate(race.player.next_gate))
	draw_arc(gate,7,0,TAU,20,Color("39d9c8"),2,true)
	for racer in race.racers:
		if racer==race.player:continue
		draw_circle(_point(racer.position),3,Color("ff9966"),true,-1,true)
	var player_point := _point(race.player.position)
	var forward: Vector3 = -race.player.global_basis.z
	var facing := Vector2(forward.x,forward.z).normalized()
	var side := facing.orthogonal()
	draw_colored_polygon(PackedVector2Array([player_point+facing*7,player_point-facing*5+side*4,player_point-facing*5-side*4]),Color.WHITE)
