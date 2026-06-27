import io
import os

import PyPDF2
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="AI Resume Critiquer", page_icon="📃", layout="centered")

st.title("AI Resume Critiquer")
st.markdown(
    "A smart tool that reviews resumes and gives instant, personalized feedback "
    "to improve clarity, ATS score, and job impact."
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY not found in .env file")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

uploaded_file = st.file_uploader("Upload your resume (PDF or TXT)", type=["pdf", "txt"])
job_role = st.text_input("Enter target job role (optional)")
analyze = st.button("Analyze Resume")

def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def extract_text_from_file(file_obj):
    if file_obj.type == "application/pdf":
        return extract_text_from_pdf(io.BytesIO(file_obj.read()))
    return file_obj.read().decode("utf-8", errors="ignore")

def get_models():
    return [
        "gemini-3.5-flash",
  
    ]

def build_prompt(resume_text: str, target_role: str) -> str:
    return f"""
You are an expert AI Resume Critiquer, ATS optimizer, and hiring coach.

Analyze the resume below for the role: "{target_role}".

Resume:
\"\"\"
{resume_text}
\"\"\"

Provide clear markdown output with these exact sections:

## 1) Instant Resume Health Check
- Overall score out of 100
- ATS score out of 100
- 2-line overall impression

## 2) Weak Wording Found + Strong Rewrites
- List weak/generic/passive phrases from the resume
- Rewrite each into stronger, action-focused alternatives

## 3) Missing Keywords for ATS
- Missing keywords grouped by:
  - Technical skills
  - Tools/platforms
  - Domain/business terms
  - Soft skills
- Mention where each keyword should be added (Summary, Skills, Experience, Projects)

## 4) Formatting & Structure Issues
- Identify formatting and readability problems
- Give exact fixes to improve professional look and clarity

## 5) Stronger Bullet Points
- Rewrite at least 6 bullets in this format:
  Action Verb + What you did + Tool/Method + Measurable Impact
- If exact metrics are missing, use placeholders like [X%], [N users], [Y hours]

## 6) Suitability for Target Role
- Verdict: Strong Fit / Moderate Fit / Weak Fit
- Why (3-5 reasons)
- What is missing to become a strong fit

## 7) High-Impact Improvements
- Top changes needed immediately
- Improvements to make resume more professional and impactful

## 8) Final Action Checklist
- 10 practical next steps candidate should do now

Rules:
- Be specific, practical, and personalized.
- Do not invent fake experience.
- Keep tone honest, constructive, and encouraging.
""".strip()

if analyze:
    if not uploaded_file:
        st.warning("Please upload your resume first.")
        st.stop()

    try:
        resume_text = extract_text_from_file(uploaded_file)

        if not resume_text.strip():
            st.error("No readable content found in the uploaded file.")
            st.stop()

        MAX_CHARS = 12000
        if len(resume_text) > MAX_CHARS:
            resume_text = resume_text[:MAX_CHARS] + "\n\n[Truncated for analysis]"

        target_role = job_role.strip() if job_role.strip() else "General"
        prompt = build_prompt(resume_text, target_role)

        response = None
        used_model = None
        last_error = None

        with st.spinner("Analyzing resume... this may take 10-30 seconds"):
            for model_name in get_models():
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    used_model = model_name
                    break
                except Exception as e:
                    last_error = e

        if response is None:
            raise RuntimeError(f"All models failed. Last error: {last_error}")

        st.success(f"Analysis complete using {used_model}")
        st.markdown("### Analysis Results")
        st.markdown(response.text)

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")