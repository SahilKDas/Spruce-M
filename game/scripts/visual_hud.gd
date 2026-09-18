extends Control

var race: Node3D

func _draw() -> void:
	if not is_instance_valid(race.player):return
	var rider = race.player
	var teal := Color("39d9c8")
	var dark := Color(.02,.07,.10,.85)
	# A segmented speed dial and a lightning-shaped energy meter.
	var origin := Vector2(92,size.y-82)
	draw_circle(origin,62,dark)
	for i in 16:
		var a := PI*.75+float(i)/15*PI*1.5
		var direction := Vector2(cos(a),sin(a))
		draw_line(origin+direction*43,origin+direction*53,teal if rider.speed_kph>i*8 else Color("34505a"),5,true)
	var bolt := PackedVector2Array([origin+Vector2(2,-25),origin+Vector2(-17,4),origin+Vector2(-2,4),origin+Vector2(-7,25),origin+Vector2(18,-7),origin+Vector2(3,-7)])
	draw_colored_polygon(bolt,Color("ffbb45") if rider.boosting else Color.WHITE)
	draw_rect(Rect2(167,size.y-91,150,16),dark)
	draw_rect(Rect2(170,size.y-88,144*rider.boost/100.0,10),Color("ffbb45") if race.toast_time>0 else teal)
	# Lap rings fill clockwise; a row of boats shows race position.
	var lap := mini(race.lap_limit-1,maxi(0,rider.passed)/HydroCourse.GATES)
	for i in race.lap_limit:
		var p := Vector2(48+i*38,48)
		draw_circle(p,16,dark)
		draw_arc(p,11,-PI/2,PI*1.5,32,Color("34505a"),4,true)
		var progress := 1.0 if i<lap else (float(maxi(0,rider.passed)%HydroCourse.GATES)/HydroCourse.GATES if i==lap else 0.0)
		if progress>0:draw_arc(p,11,-PI/2,-PI/2+TAU*progress,32,teal,4,true)
	var place := 0
	for other in race.racers:
		if other!=rider and other.progress_score()>rider.progress_score():place+=1
	for i in race.racers.size():
		var p := Vector2(40+i*21,87)
		draw_colored_polygon(PackedVector2Array([p+Vector2(0,-8),p+Vector2(-5,6),p+Vector2(5,6)]),Color.WHITE if i==place else Color("426474"))
	# Starting lights replace the countdown text.
	if race.countdown>0:
		for i in 3:
			var p := Vector2(size.x*.5+(i-1)*54,size.y*.38)
			draw_circle(p,23,dark)
			draw_circle(p,16,Color("ff6644") if race.countdown<=3-i else Color("59352e"))
	elif race.race_time<.65:
		for i in 3:draw_circle(Vector2(size.x*.5+(i-1)*54,size.y*.38),16,teal)
