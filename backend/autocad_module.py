# backend/autocad_module.py

import json
from pyautocad import Autocad, APoint

def create_dwg_from_json(layout_json):
    data = json.loads(layout_json)
    acad = Autocad(create_if_not_exists=True)

    acad.prompt("Generating drawing...\n")

    for i, room in enumerate(data.get("rooms", [])):
        x_offset = i * 1200
        p1 = APoint(x_offset, 0)
        p2 = APoint(x_offset + 1000, 800)
        acad.model.AddRectangle(p1, 1000, 800)
        acad.model.AddText(f"{room['name']} - {room['sprinklers']} sprinklers ({room['pipe_size']})", APoint(x_offset + 50, 850), 50)

    acad.prompt("✅ DWG Completed.\n")
