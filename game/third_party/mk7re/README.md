# mk7re reference and adaptation

Upstream: https://github.com/mk7re/MK7-Memory

Pinned revision: `30a854b8c033ab72d96bc9804e68679a1be3bf01`.

`game/scripts/handling.gd::rigid_velocity` adapts the componentwise velocity retention plus minimum/maximum force accumulation in [`template/Kart/Vehicle/Rigid.hpp::updateVel`](https://github.com/mk7re/MK7-Memory/blob/30a854b8c033ab72d96bc9804e68679a1be3bf01/template/Kart/Vehicle/Rigid.hpp). The upstream MIT license is included alongside this file.

The separation of sea speed, driving/drifting handling, lateral sliding, and two mini-turbo durations follows the documented fields in `template/Kart/PartsDriveParamSet.hpp`. Charge, boost duration, and boost-state concepts are documented in `template/Kart/Vehicle/VehicleMove.hpp`.

The published repository contains partial implementations and reverse-engineered data layouts. It does not provide a complete standalone Mario Kart 7 driving controller. Hydro Drift's acceleration curves, metre/second values, steering response, drift thresholds, and turbo durations are original tuning values. Water buoyancy, collision response, gravity, camera behavior, and rendering remain Hydro Drift/Godot implementations. This is an adaptation of the available code and documented structure, not an exact reproduction of Mario Kart 7 physics. No game ROM, proprietary parameter tables, or Nintendo assets are included.
