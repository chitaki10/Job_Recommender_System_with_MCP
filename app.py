import streamlit as st
from src.helper import extract_text_from_pdf, ask_groq, fetch_linkedin_jobs, fetch_naukri_jobs

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Job Recommender",
    page_icon="💼",
    layout="wide"
)


st.title("AI Job Recommender")
st.markdown(
    "> Upload your resume and get **AI-powered** job recommendations, "
    "skill gap analysis, and a personalized career roadmap."
)
st.divider()


def display_section(icon: str, title: str, content: str):
    """Renders a styled markdown card for each analysis section."""
    with st.container(border=True):
        st.markdown(f"### {icon} {title}")
        st.markdown(content)


def main():
    uploaded_file = st.file_uploader(
        "📄 Upload your Resume (PDF only)",
        type=["pdf"],
        help="Supported format: PDF. Max size: 10MB."
    )

    if uploaded_file:
        # ── Step 1: Extract ──────────────────────────────────────────────────
        with st.spinner("📖 Extracting text from your resume..."):
            resume_text = extract_text_from_pdf(uploaded_file)

        if not resume_text or len(resume_text.strip()) < 50:
            st.error("⚠️ Could not extract enough text. Is your PDF scanned? Try a text-based PDF.")
            st.stop()

        st.success("✅ Resume parsed successfully!")
        st.divider()

        # ── Step 2: Resume Summary ───────────────────────────────────────────
        with st.spinner("🧠 Summarizing your resume..."):
            summary = ask_groq(
                f"Summarize this resume. Highlight key skills, years of experience, "
                f"tech stack, and notable achievements. Be concise.\n\n{resume_text}",
                max_tokens=500
            )
        display_section("🧠", "Resume Summary", summary)

        # ── Step 3: Skill Gap Analysis ───────────────────────────────────────
        with st.spinner("🔍 Analyzing skill gaps..."):
            skill_gap = ask_groq(
                f"Analyze this resume and identify:\n"
                f"1. Missing technical skills for current job market\n"
                f"2. Gaps in certifications or education\n"
                f"3. Weak areas compared to industry standards\n"
                f"4. Specific suggestions to close each gap\n\n"
                f"Format your response using bullet points.\n\n{resume_text}",
                max_tokens=500
            )
        display_section("🔍", "Skill Gap Analysis", skill_gap)

        # ── Step 4: Career Roadmap ────────────────────────────────────────────
        with st.spinner("🗺️ Building your career roadmap..."):
            roadmap = ask_groq(
                f"Based on this resume, create a 6–12 month career improvement roadmap:\n"
                f"1. Top 3 skills to learn immediately\n"
                f"2. Certifications to pursue (with priority order)\n"
                f"3. Projects to build for portfolio\n"
                f"4. Industry exposure and networking steps\n\n"
                f"Format as a numbered, structured plan.\n\n{resume_text}",
                max_tokens=500
            )
        display_section("🗺️", "Career Roadmap", roadmap)

        # ── Step 5: Job Recommendations ──────────────────────────────────────
        st.divider()
        st.markdown("### 💼 Job Recommendations")

        col1, col2 = st.columns(2)

        with col1:
            with st.spinner("🔗 Fetching LinkedIn jobs..."):
                linkedin_jobs = fetch_linkedin_jobs(resume_text)
            with st.container(border=True):
                st.markdown("#### 🔗 LinkedIn Matches")
                if linkedin_jobs:
                    for job in linkedin_jobs:
                        st.markdown(f"- **{job.get('title', 'N/A')}** at {job.get('company', 'N/A')} — [Apply]({job.get('url', '#')})")
                else:
                    st.info("No LinkedIn jobs fetched. Check your API integration.")

        with col2:
            with st.spinner("🏢 Fetching Naukri jobs..."):
                naukri_jobs = fetch_naukri_jobs(resume_text)
            with st.container(border=True):
                st.markdown("#### 🏢 Naukri Matches")
                if naukri_jobs:
                    for job in naukri_jobs:
                        st.markdown(f"- **{job.get('title', 'N/A')}** at {job.get('company', 'N/A')} — [Apply]({job.get('url', '#')})")
                else:
                    st.info("No Naukri jobs fetched. Check your API integration.")

        # ── Footer ────────────────────────────────────────────────────────────
        st.divider()
        st.caption("⚡ Powered by Groq LLM · Built with Streamlit · AI Job Recommender v1.0")


if __name__ == "__main__":
    main()
