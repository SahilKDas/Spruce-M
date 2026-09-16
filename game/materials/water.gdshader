shader_type spatial;
render_mode cull_back;
uniform float wave_time = 0.0;
varying vec3 world_pos;

void vertex() {
	vec3 p = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float a = p.x * .095 + p.z * .06 + wave_time * 1.5;
	float b = p.z * .19 - p.x * .045 - wave_time * 2.05;
	VERTEX.y += sin(a) * .19 + sin(b) * .09;
	NORMAL = normalize(vec3(-cos(a)*.01805 + cos(b)*.00405, 1., -cos(a)*.0114-cos(b)*.0171));
	world_pos = p;
}
void fragment() {
	float shelf = length(world_pos.xz / vec2(44., 68.));
	float shallow = 1.0 - smoothstep(.9, 1.6, shelf);
	vec3 deep = vec3(.008,.17,.26);
	vec3 clear = vec3(.035,.60,.53);
	ALBEDO = mix(deep, clear, shallow);
	float warp = sin(world_pos.x*.31+world_pos.z*.23-wave_time*.7)*1.3;
	float ripples = sin(world_pos.x*1.7 + world_pos.z*.63 + warp + wave_time*1.1);
	vec3 detail = vec3(ripples*.035,0.,sin(world_pos.z*2.1-world_pos.x*.4+warp-wave_time)*.025);
	NORMAL = normalize(NORMAL + (VIEW_MATRIX * vec4(detail,0.)).xyz);
	float foam = (1.0-smoothstep(.007,.032,abs(shelf-1.05 + sin(wave_time+world_pos.z*.2)*.009)))*.55;
	ALBEDO = mix(ALBEDO,vec3(.78,.94,.87),foam);
	ROUGHNESS = .36;
	METALLIC = .0;
	SPECULAR = .5;
}
