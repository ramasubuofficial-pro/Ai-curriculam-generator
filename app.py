from io import BytesIO
import streamlit as st
import os
from dotenv import load_dotenv
from google import genai 
import markdown
from xhtml2pdf import pisa

# Load environment variables (including GEMINI_API_KEY)
load_dotenv()

# Initialize Gemini client
API_KEY = os.getenv("GEMINI_API_KEY")

try:
    if not API_KEY:
        st.error("GEMINI_API_KEY not found. Please create a .env file and set GEMINI_API_KEY.")
        st.stop()
        
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    st.error(f"Gemini Client initialization failed. Check your API key and network: {e}")
    st.stop()

# --- Configuration and UI ---
st.set_page_config(
    page_title="AI Curriculum Designer",
    layout="centered"
)

# Custom CSS for Mobile Responsiveness
st.markdown("""
<style>
    @media (max-width: 768px) {
        /* Reduce padding on smaller screens to use more space */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        /* Make the main title slightly smaller */
        h1 {
            font-size: 1.8rem !important;
        }
        /* Make the submit button full width on mobile */
        .stButton>button {
            width: 100% !important;
        }
    }

    /* Hide Streamlit Header, Menu, and Footer */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp > header {display: none;}
</style>
""", unsafe_allow_html=True)

st.title("🧠 AI-Generated Course Curriculum Designer")
st.markdown("Powered by Google Gemini. Use cutting-edge AI to instantly generate a professional, structured course syllabus.")

# --- User Inputs (Streamlit Form) ---
with st.form("curriculum_form"):
    course_topic = st.text_input(
        "Course Topic:",
        placeholder="e.g., Advanced Kubernetes for DevOps"
    )
    
    course_level = st.selectbox(
        "Target Level:",
        ("Beginner", "Intermediate", "Advanced", "Expert"),
        index=0
    )
    
    course_duration = st.text_input(
        "Course Duration (in weeks or hours):",
        placeholder="e.g., 8 Weeks"
    )
    
    submitted = st.form_submit_button("Generate Curriculum ✨")

# --- AI Generation Logic ---
if submitted and course_topic and course_duration:
    
    # 1. Define the Master Prompts and Combine
    system_prompt = (
        "You are an expert curriculum designer and educator. Your task is to "
        "create a professional, comprehensive, and structured course syllabus. "
        "The output must be strictly formatted using Markdown for clear readability. "
        "The hierarchy must be: # (Course Title), ## (Week/Module Title), ### (Topic Title), * (Learning Outcome/Prerequisites). "
        "Ensure all Learning Outcomes are action-oriented and measurable."
    )
    
    user_prompt = (
        f"Generate a full curriculum using the following details:\n"
        f"- **Topic:** {course_topic}\n"
        f"- **Level:** {course_level}\n"
        f"- **Duration:** {course_duration}\n\n"
        "The plan must include: Course Summary, Prerequisites, Weekly/Module Breakdown with Topics, detailed Learning Outcomes for each section, and a final section titled '## Capstone Project Ideas' with at least three distinct options."
    )
    
    full_prompt = system_prompt + "\n\n" + user_prompt
    
    # Using the faster, more stable model
    GEMINI_MODEL = "gemini-2.5-flash"
    st.info(f"Generating curriculum with {GEMINI_MODEL}...", icon="⏳")
    
    try:
        # 2. Call the Gemini API
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[full_prompt],
            config={"temperature": 0.7}
        )
        
        # 3. ROBUST CONTENT CHECK
        final_markdown = response.text
        if not final_markdown or len(final_markdown.strip()) < 50:
             st.error("Error: The Gemini model returned an empty or incomplete response. Please try regenerating the curriculum.")
             st.stop()
        
        # 4. Display the Result
        st.success("Curriculum Generated Successfully with Gemini!")
        st.markdown(final_markdown)
        
        st.divider()

        # 5. Generate and Offer PDF Download
        
        # Convert Markdown to HTML
        html_content = markdown.markdown(final_markdown, extensions=['tables'])
        
        # Wrap in basic HTML/CSS for styling
        styled_html = f"""
        <html>
        <head>
        <style>
            body {{ font-family: Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; }}
            h1 {{ color: #2c3e50; font-size: 24px; }}
            h2 {{ color: #34495e; border-bottom: 1px solid #eee; padding-bottom: 5px; font-size: 20px; }}
            h3 {{ color: #7f8c8d; font-size: 16px; }}
            li {{ margin-bottom: 5px; }}
        </style>
        </head>
        <body>
        {html_content}
        </body>
        </html>
        """
        
        pdf_file = BytesIO()
        pisa_status = pisa.CreatePDF(styled_html, dest=pdf_file)
        
        if not pisa_status.err:
            st.download_button(
                label="Download Curriculum (PDF) 📄",
                data=pdf_file.getvalue(),  
                file_name=f"{course_topic.replace(' ', '_')}_Curriculum.pdf", 
                mime="application/pdf"
            )
        else:
            st.error("There was an error generating the PDF.")

    except Exception as e:
        # Catch any errors during the Gemini API call (e.g., rate limits, invalid input)
        st.error(f"An error occurred during Gemini API call: {e}")

elif submitted:
    st.warning("Please fill in the Course Topic and Duration to generate the curriculum.")