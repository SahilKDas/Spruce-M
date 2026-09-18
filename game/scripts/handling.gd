class_name HydroHandling
extends RefCounted

# Rigid.updateVel adaptation from mk7re/MK7-Memory (MIT).
# See third_party/mk7re/README.md for the pinned source and adaptation boundary.
static func rigid_velocity(velocity: Vector3, retention: Vector3, force_min: Vector3, force_max: Vector3) -> Vector3:
	return velocity * retention + force_min + force_max

# These metre/second tuning values belong to Hydro Drift, not Mario Kart 7.
static func drive_velocity(local_velocity: Vector3, throttle: float, drifting: bool, boosted: bool, craft: int, delta: float, grip_blend: float = -1.0) -> Vector3:
	var maximum: float = [27.0,28.5,30.0][craft] + (8.0 if boosted else 0.0)
	var ratio := clampf(absf(local_velocity.z)/maximum,0.0,1.0)
	var acceleration: float = [17.0,16.0,15.0][craft] * lerpf(1.0,.62,ratio)
	if boosted:acceleration *= 1.55
	if throttle<0.0 and local_velocity.z>0.0:acceleration = 24.0
	var slide := (1.0 if drifting else 0.0) if grip_blend<0.0 else clampf(grip_blend,0.0,1.0)
	var grip := lerpf([8.5,7.8,7.0][craft],2.1,slide)
	# Redirect momentum into the hull's heading instead of deleting corner speed.
	# Extreme collision side-slips still dissipate rather than becoming free thrust.
	var planar := Vector2(local_velocity.x,local_velocity.z)
	var heading := atan2(planar.x,planar.y)
	if planar.y>1.0 and absf(heading)<1.2:
		heading *= exp(-grip*delta)
		planar = Vector2(sin(heading),cos(heading))*planar.length()
	else:
		planar.x *= exp(-grip*delta)
	var retention := Vector3(1.0,1.0,exp(-.12*delta))
	var change := throttle*acceleration*delta
	if change>0.0:change = minf(change,maxf(0.0,maximum-planar.y*retention.z))
	if change<0.0:change = maxf(change,minf(0.0,-5.0-planar.y*retention.z))
	return rigid_velocity(Vector3(planar.x,local_velocity.y,planar.y),retention,Vector3(0,0,minf(change,0.0)),Vector3(0,0,maxf(change,0.0)))

static func steering_input(current: float, target: float, delta: float) -> float:
	# Fast direction changes; a faster release prevents sticky keyboard steering.
	var response := 18.0 if absf(target)<.01 or current*target<0.0 else 13.0
	return lerpf(current,target,1.0-exp(-response*delta))

static func yaw_target(steering: float, speed: float, drift_direction: float, craft: int = 0) -> float:
	var authority := clampf(absf(speed)/4.0,0.0,1.0)
	var turning := steering*lerpf(1.9,1.22,clampf(absf(speed)/30.0,0.0,1.0))
	if drift_direction!=0.0:
		turning = drift_direction*(1.02+.72*steering*drift_direction)
	return turning*authority*[1.08,1.0,.93][craft]*(1.0 if speed>=0.0 else -1.0)

static func mini_turbo_duration(charge: float) -> float:
	if charge>=.65:return 1.20
	if charge>=.20:return .55
	return 0.0
