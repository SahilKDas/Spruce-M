extends SceneTree

func _initialize() -> void:
	var course = load("res://scripts/course.gd")
	for i in course.GATES:
		var angle: float = float(i)/course.GATES*TAU
		var center: Vector3 = course.point(angle)
		var tangent: Vector3 = course.tangent(angle)
		var side := tangent.cross(Vector3.UP)
		assert(course.crossed_gate(center-tangent*3,center+tangent*3,i),"Valid forward crossing rejected")
		assert(not course.crossed_gate(center+tangent*3,center-tangent*3,i),"Reverse lap exploit accepted")
		assert(not course.crossed_gate(center-tangent*3+side*30,center+tangent*3+side*30,i),"Off-course shortcut accepted")
		assert(not course.crossed_gate(center-tangent*3+Vector3.UP*20,center+tangent*3+Vector3.UP*20,i),"High-altitude gate skip accepted")
		var expected: float = course.wave(center,3.0)
		assert(is_finite(expected) and absf(expected)<.29,"Wave sample outside bound")
	print("HYDRO_RULES_OK 20 gates: forward, reverse, outside, height, wave bounds")
	quit()
