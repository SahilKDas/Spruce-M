class_name HydroCourse
extends RefCounted

const GATES := 20
const WIDTH := 23.0
static var center := Vector3.ZERO

static func point(t: float) -> Vector3:
	return center + Vector3(cos(t) * (70.0 + 7.0 * sin(t * 3.0)), 0.0, sin(t) * 100.0)

static func tangent(t: float) -> Vector3:
	return (point(t + 0.002) - point(t - 0.002)).normalized()

static func nearest_angle(p: Vector3) -> float:
	var q := p-center
	return fposmod(atan2(q.z / 100.0, q.x / 70.0), TAU)

static func tide(time: float) -> float:
	return sin(time*TAU/180.0)*.9

static func wave(p: Vector3, time: float) -> float:
	return tide(time) + sin(p.x * 0.095 + p.z * 0.06 + time * 1.5) * 0.19 + sin(p.z * 0.19 - p.x * 0.045 - time * 2.05) * 0.09

static func normal(p: Vector3, time: float) -> Vector3:
	var a := p.x * 0.095 + p.z * 0.06 + time * 1.5
	var b := p.z * 0.19 - p.x * 0.045 - time * 2.05
	return Vector3(-cos(a) * 0.01805 + cos(b) * 0.00405, 1.0, -cos(a) * 0.0114 - cos(b) * 0.0171).normalized()

static func gate(index: int) -> Vector3:
	return point(float(index % GATES) / GATES * TAU)

static func crossed_gate(previous: Vector3, current: Vector3, index: int) -> bool:
	var t := float(index % GATES) / GATES * TAU
	var center := point(t)
	var direction := tangent(t)
	var before := (previous - center).dot(direction)
	var after := (current - center).dot(direction)
	if before > 0.0 or after < 0.0 or after - before < 0.00001:
		return false
	var crossing := previous.lerp(current, -before / (after - before))
	return Vector2(crossing.x - center.x, crossing.z - center.z).length() < WIDTH * 0.60 and absf(crossing.y) < 7.0
