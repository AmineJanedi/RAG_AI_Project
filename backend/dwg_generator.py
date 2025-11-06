# backend/dwg_generator.py
"""
Create DXF (openable in AutoCAD) from a layout dict using ezdxf.
NOTE: ezdxf writes DXF files. Converting to native DWG requires AutoCAD or commercial SDK.
"""

import ezdxf
import os
import uuid
from datetime import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../backend_outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_dxf_from_layout(layout: dict, filename: str = None) -> str:
    """
    layout: {
      "rooms": [{"name":"Room1","x":0,"y":0,"width":5000,"height":4000}, ...],
      "sprinklers":[{"x":1000,"y":1200}, ...]
    }
    Units used are mm by convention.
    Returns path to saved DXF file.
    """
    now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    uid = uuid.uuid4().hex[:6]
    fname = filename or f"design_{now}_{uid}.dxf"
    file_path = os.path.join(OUTPUT_DIR, fname)

    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()

    # Draw rooms with light polyline
    for r in layout.get("rooms", []):
        x = float(r.get("x", 0))
        y = float(r.get("y", 0))
        w = float(r.get("width", 1000))
        h = float(r.get("height", 1000))
        pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
        msp.add_lwpolyline(pts, dxfattribs={"layer": "ROOMS"})
        # add name text
        try:
            msp.add_text(r.get("name", ""), dxfattribs={"layer": "ROOMS"}).set_pos((x + 50, y + h - 50))
        except Exception:
            pass

    # Draw sprinklers as small circles
    for s in layout.get("sprinklers", []):
        sx = float(s.get("x", 0))
        sy = float(s.get("y", 0))
        msp.add_circle((sx, sy), radius=50, dxfattribs={"layer": "SPRINKLERS"})

    doc.saveas(file_path)
    return file_path
