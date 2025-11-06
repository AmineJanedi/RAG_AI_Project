# backend/app.py
"""
FastAPI backend with:
- /chat     : streams LLM responses (forwarding from Ollama streaming)
- /generate-dwg : accepts prompt or layout JSON, returns DXF + reports
Serves outputs from backend_outputs/ for download.
"""

import os
import json
from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import AsyncGenerator

from ollama_client import query_ollama
from rag_module import query_rag
from dwg_generator import create_dxf_from_layout
from report_generator import generate_technical_report, generate_financial_report

BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, "../backend_outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI(title="FireAI Backend")

# mount endpoint to serve output files directly
app.mount("/backend_outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

@app.get("/")
def home():
    return {"message": "FireAI backend running"}

@app.post("/chat")
def chat(prompt: str = Form(...)):
    """
    Streams response from Ollama to client (chunked text).
    The frontend can read the stream and display typing effect.
    """
    # get RAG context (optional)
    context = query_rag(prompt)
    full_prompt = f"Context:\n{context}\n\nUser Prompt:\n{prompt}\n\nPlease answer concisely."

    # request streaming from Ollama
    gen = query_ollama(full_prompt, stream=True)

    def event_stream() -> AsyncGenerator[bytes, None]:
        try:
            # gen is a generator yielding small strings
            for chunk in gen:
                if not chunk:
                    continue
                # ensure bytes and yield
                text = str(chunk)
                # yield as simple chunks (not SSE) - client reads iter_lines
                yield (text).encode("utf-8")
        except Exception as e:
            yield f"[ERR]{str(e)}".encode("utf-8")
    return StreamingResponse(event_stream(), media_type="text/plain")

@app.post("/generate-dwg")
async def generate_dwg(prompt: str = Form(None), layout_json: str = Form(None), upload: UploadFile = File(None)):
    """
    Modes:
    - If layout_json provided: use it.
    - If upload provided: expect JSON file and use it.
    - If prompt provided: ask LLM to return JSON layout, then create DXF + reports.
    Returns URLs to download DXF + technical + financial reports (served under /backend_outputs).
    """
    if upload:
        raw = await upload.read()
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid uploaded JSON: {e}")
    elif layout_json:
        try:
            payload = json.loads(layout_json)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    elif prompt:
        context = query_rag(prompt)
        ai_input = f"Context:\n{context}\n\nUser Request:\n{prompt}\n\nReturn ONLY JSON with keys: rooms (list), sprinklers (list). Rooms must have name,x,y,width,height (in mm)."
        ai_resp = query_ollama(ai_input, stream=False)
        # try parse JSON (strip fenced code)
        text = ai_resp.strip()
        if text.startswith("```"):
            text = "\n".join(text.splitlines()[1:-1])
        try:
            payload = json.loads(text)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse JSON from LLM: {e}; raw_output={ai_resp[:1000]}")
    else:
        raise HTTPException(status_code=400, detail="Provide prompt, layout_json, or upload a JSON file.")

    # generate DXF
    try:
        dxf_path = create_dxf_from_layout(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DXF generation failed: {e}")

    # generate reports
    tech_path = generate_technical_report(payload)
    fin_path = generate_financial_report(payload)

    # convert paths to URLs served by FastAPI static route
    def to_url(p):
        fname = os.path.basename(p)
        return f"/backend_outputs/{fname}"

    return JSONResponse({
        "status": "success",
        "layout": payload,
        "files": {
            "dxf": to_url(dxf_path),
            "technical_report": to_url(tech_path),
            "financial_report": to_url(fin_path)
        }
    })
