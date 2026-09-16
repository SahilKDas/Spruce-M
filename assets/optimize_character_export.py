from pathlib import Path
p=Path(__file__).with_name('rebuild_characters.py');s=p.read_text()
start=s.index("    for side in ['L','R']:\n        for limb,pole,target")
end=s.index("    rig['instructions']",start)
constraints=s[start:end]
s=s[:start]+s[end:]
anchor="    return {'name':name,'category':'character'"
s=s.replace(anchor,constraints+anchor)
s=s.replace("export_force_sampling=True,export_frame_step=4", "export_force_sampling=False,export_animations=(level==0),export_frame_step=4")
p.write_text(s)
v=Path(__file__).with_name('validate_characters_v2.py');s=v.read_text().replace("        assert doc.get('animations'),(name,suffix,'Missing pose test')", "        if not suffix:assert doc.get('animations'),(name,suffix,'Missing pose test')");v.write_text(s)
