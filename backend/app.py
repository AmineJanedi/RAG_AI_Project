# backend/app.py
from fastapi import FastAPI
from pydantic import BaseModel
import ollama
from rag_module import load_rag_context, query_rag
from dwg_generator import create_dwg_from_json
from report_generator import estimate_cost, generate_report
import json

app = FastAPI()

vector_store = load_rag_context()

class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
def generate_design(request: PromptRequest):
    rag_context = query_rag(vector_store, request.prompt)

    final_prompt = f"""
    You are an architectural AI assistant. 
    Based on the user's request and company standards below, 
    create a JSON layout (rooms, sprinklers).

    Context:
    {rag_context}

    User Request:
    {request.prompt}

    Output only valid JSON.
    Example:
    {{
        "rooms": [{{"name": "Office", "x": 0, "y": 0, "width": 5000, "height": 4000}}],
        "sprinklers": [{{"x": 1000, "y": 1000}}, {{"x": 4000, "y": 3000}}]
    }}
    """

    response = ollama.chat(model="llama3", messages=[{"role": "user", "content": final_prompt}])
    raw_output = response["message"]["content"]

    try:
        layout_data = json.loads(raw_output)

        # 1. Create DWG
        create_dwg_from_json(layout_data)

        # 2. Estimate costs
        cost_data = estimate_cost(layout_data)

        # 3. Generate report
        generate_report(layout_data, cost_data)

        return {
            "status": "success",
            "layout": layout_data,
            "cost_summary": cost_data,
            "files": ["output_design.dwg", "design_report.pdf"]
        }

    except Exception as e:
        return {"status": "error", "message": str(e), "raw_output": raw_output}
#Run command : 
#python -m uvicorn app:app --reload
