class_name HydroHandling
extends RefCounted

# Rigid.updateVel adaptation from mk7re/MK7-Memory (MIT).
# See third_party/mk7re/README.md for the pinned source and adaptation boundary.
static func rigid_velocity(velocity: Vector3, retention: Vector3, force_min: Vector3, force_max: Vector3) -> Vector3:
	return velocity * retention + force_min + force_max

# These metre/second tuning values belong to Hydro Drift, not Mario Kart 7.
static func drive_velocity(local_velocity: Vector3, throttle: float, drifting: bool, boosted: bool, craft: int, delta: float) -> Vector3:
	var maximum: float = [27.0,28.5,30.0][craft] + (8.0 if boosted else 0.0)
	var ratio := clampf(absf(local_velocity.z)/maximum,0.0,1.0)
	var acceleration: float = [11.5,11.0,10.5][craft] * lerpf(1.0,.52,ratio)
	if boosted:acceleration *= 1.45
	if throttle<0.0 and local_velocity.z>0.0:acceleration = 17.0
	var grip := .85 if drifting else 5.8
	var retention := Vector3(exp(-grip*delta),1.0,exp(-.14*delta))
	var change := throttle*acceleration*delta
	if change>0.0:change = minf(change,maxf(0.0,maximum-local_velocity.z*retention.z))
	if change<0.0:change = maxf(change,minf(0.0,-5.0-local_velocity.z*retention.z))
	return rigid_velocity(local_velocity,retention,Vector3(0,0,minf(change,0.0)),Vector3(0,0,maxf(change,0.0)))

static func yaw_target(steering: float, speed: float, drift_direction: float) -> float:
	var authority := clampf(absf(speed)/6.0,0.0,1.0)
	var turning := steering*lerpf(1.38,1.0,clampf(absf(speed)/30.0,0.0,1.0))
	if drift_direction!=0.0:
		turning = drift_direction*(.78+.68*steering*drift_direction)
	return turning*authority*(1.0 if speed>=0.0 else -1.0)

static func mini_turbo_duration(charge: float) -> float:
	if charge>=.65:return 1.20
	if charge>=.20:return .55
	return 0.0
