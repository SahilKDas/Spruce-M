extends SceneTree

func simulate(rate: int, throttle: float, initial: Vector3, seconds: float, drifting: bool = false) -> Vector3:
	var velocity := initial
	for i in roundi(seconds*rate):
		velocity = HydroHandling.drive_velocity(velocity,throttle,drifting,false,0,1.0/rate)
	return velocity

func _initialize() -> void:
	var baseline := simulate(60,1.0,Vector3.ZERO,12.0)
	assert(baseline.z>25.0 and baseline.z<=27.001,"Acceleration did not settle at the craft speed limit")
	for rate in [30,120]:
		assert(simulate(rate,1.0,Vector3.ZERO,12.0).distance_to(baseline)<.15,"Handling changes with physics tick rate")
	var brake := simulate(60,-1.0,Vector3(0,0,25),6.0)
	assert(brake.z<0.0 and brake.z>=-5.001,"Braking/reverse speed limit failed")
	var gripping := simulate(60,0.0,Vector3(8,0,20),.5)
	var sliding := simulate(60,0.0,Vector3(8,0,20),.5,true)
	assert(sliding.x>gripping.x*3.0,"Drift did not preserve lateral movement")
	assert(HydroHandling.yaw_target(-1,20,1)>0,"Countersteering reversed a locked drift")
	assert(HydroHandling.yaw_target(0,0,0)==0,"Craft turns while stationary")
	print("HYDRO_HANDLING_OK acceleration, speed limits, braking, tick-rate stability, drift grip and countersteer")
	quit()
