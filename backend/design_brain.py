# backend/design_brain.py

from ollama import chat

def generate_layout_json(prompt, context):
    system_prompt = """
You are an NFPA design assistant.
Based on user's request and context, output ONLY valid JSON describing the layout.
Example:
{
  "type": "FireSprinkler",
  "rooms": [
    {"name": "Kitchen", "sprinklers": 4, "pipe_size": "1 inch"},
    {"name": "Hallway", "sprinklers": 2, "pipe_size": "3/4 inch"}
  ],
  "total_pipes": 6,
  "estimated_cost": 1200
}
"""

    response = chat(model="llama3", messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context:\n{context}\n\nUser Prompt:\n{prompt}"}
    ])
    return response["message"]["content"]
