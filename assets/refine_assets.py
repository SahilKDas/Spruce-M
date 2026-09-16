from pathlib import Path
p=Path(__file__).with_name('build_assets.py')
s=p.read_text()
s=s.replace("    for frame,angle in [(1,-.025),(25,.025),(49,-.025)]:", """    proportions={'human':(1,1,1),'shark':(1.30,1.15,1.12),'otter':(.82,.88,.87),'axolotl':(.95,.96,1.03),'robot':(1.04,1,1.06),'capy':(1.28,1.1,.92),'octopus':(1.06,1.03,.96)}
    rig.scale=proportions[kind]; rig.location.z=-.16*rig.scale.z
    for frame,angle in [(1,-.025),(25,.025),(49,-.025)]:""")
s=s.replace("(0,1.8,.02),.44", "(0,-2.1,.02),.40")
s=s.replace("(5,-11,7),(0,0,1),14.5", "(2,-14,8),(0,-.2,.8),14.5")
s=s.replace("scene.cycles.samples=24", "scene.cycles.samples=16")
p.write_text(s)
exec(compile(s,str(p),'exec'))
