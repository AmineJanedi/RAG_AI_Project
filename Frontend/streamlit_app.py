# frontend/streamlit_app.py
import streamlit as st
import requests
import os

st.title("🏗️ AI CAD Generator (RAG + Llama3 + Cost Report)")

prompt = st.text_area("Describe your design:", height=150)

if st.button("Generate Design"):
    with st.spinner("Generating..."):
        response = requests.post("http://127.0.0.1:8000/generate", json={"prompt": prompt})
        result = response.json()

        if result["status"] == "success":
            st.success("✅ Design generated successfully!")
            st.json(result["layout"])
            st.subheader("💰 Cost Summary")
            st.json(result["cost_summary"])

            pdf_path = "../backend/design_report.pdf"
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    st.download_button("📄 Download Report", f, file_name="design_report.pdf")

            st.info("DWG file saved as output_design.dwg in backend folder.")
        else:
            st.error("❌ Error:")
            st.code(result["message"])
#Run command : 
#python -m streamlit run streamlit_app.py
