import streamlit as st
import google.generativeai as genai
from docx import Document
import io
import datetime

st.set_page_config(page_title="Municipal Ordinance Generator", layout="wide")

st.title("Municipal Ordinance Generator & Dashboard")

# --- Initialize Memory (Session State) ---
# This creates a temporary database that lasts while the browser tab is open
if 'history' not in st.session_state:
    st.session_state.history = []

# Configure API key securely
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("API Key not found. Please set GEMINI_API_KEY in your Streamlit secrets.")
    st.stop()

# Helper function to create Word Docs
def create_word_docx(text_content):
    doc = Document()
    doc.add_paragraph(text_content)
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream

# --- Create Tabs ---
tab1, tab2 = st.tabs(["📝 Draft New Ordinance", "📊 Ordinance Dashboard"])

# ==========================================
# TAB 1: GENERATOR
# ==========================================
with tab1:
    st.markdown("### Create a New Draft")
    with st.form("ordinance_form"):
        city_name = st.text_input("City Name", value="McKinney")
        department = st.selectbox("Sponsoring Department", ["Library System", "Public Works", "Finance", "Parks & Rec", "City Manager's Office"])
        item_title = st.text_input("Short Title / Caption", placeholder="e.g., Amending Non-Resident Library Fees")
        substance = st.text_area("Core Substance / Policy Change", placeholder="Describe exactly what changes.")
        fiscal_impact = st.text_input("Fiscal Impact / Funding Source", placeholder="e.g., Net positive revenue of $5,000 annually to General Fund")
        
        submitted = st.form_submit_button("Generate Draft Ordinance")

    if submitted:
        if not substance or not item_title:
            st.error("Please fill out the Title and Core Substance fields.")
        else:
            with st.spinner("Drafting ordinance based on municipal template..."):
                prompt = f"""
                You are a municipal legal assistant. Draft a formal city ordinance based on the following structured inputs. Maintain standard Texas municipal legal boilerplate (severability, repealer, effective date).

                INPUTS:
                - City: {city_name}
                - Department: {department}
                - Title: {item_title}
                - Substance: {substance}
                - Fiscal Notes: {fiscal_impact}

                TEMPLATE TO FOLLOW:
                ORDINANCE NO. ______
                AN ORDINANCE OF THE CITY OF {city_name.upper()}, TEXAS, AMENDING THE CODE OF ORDINANCES BY {item_title.upper()}; PROVIDING A REPEALER CLAUSE; PROVIDING A SEVERABILITY CLAUSE; AND PROVIDING AN EFFECTIVE DATE.
                
                BE IT ORDAINED BY THE CITY COUNCIL OF THE CITY OF {city_name.upper()}, TEXAS:
                [Generate appropriate SECTIONS here]
                """
                
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt)
                generated_text = response.text
                
                # --- Save to History ---
                record = {
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "city": city_name,
                    "department": department,
                    "title": item_title,
                    "fiscal": fiscal_impact,
                    "text": generated_text
                }
                # Add the new record to the beginning of the list
                st.session_state.history.insert(0, record)
                
                st.success("Draft created successfully! You can view it below or switch to the Dashboard tab.")
                
                # Show results in the generator tab too
                st.text_area("Review Draft", value=generated_text, height=300)
                word_file = create_word_docx(generated_text)
                st.download_button(
                    label="📥 Download this draft as Word Document",
                    data=word_file,
                    file_name=f"Draft_{department.replace(' ', '_')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

# ==========================================
# TAB 2: DASHBOARD
# ==========================================
with tab2:
    st.markdown("### Ordinance History & Review")
    
    if len(st.session_state.history) == 0:
        st.info("No ordinances generated yet. Go to the 'Draft New Ordinance' tab to get started.")
    else:
        st.write(f"**Total Drafts in Session:** {len(st.session_state.history)}")
        st.divider()
        
        # Loop through saved history and display it
        for idx, item in enumerate(st.session_state.history):
            # Create a collapsible expander for each ordinance
            with st.expander(f"📄 {item['title']} ({item['department']} - {item['timestamp']})", expanded=(idx==0)):
                
                # Use columns to put metadata and text side-by-side
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown("**Metadata:**")
                    st.write(f"- **City:** {item['city']}")
                    st.write(f"- **Dept:** {item['department']}")
                    st.write(f"- **Fiscal Impact:** {item['fiscal']}")
                    
                    word_file = create_word_docx(item['text'])
                    st.download_button(
                        label="📥 Download (.docx)",
                        data=word_file,
                        file_name=f"Draft_{item['department'].replace(' ', '_')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"dl_btn_{idx}" # Keys must be unique for buttons in loops
                    )
                
                with col2:
                    st.markdown("**Generated Text:**")
                    st.text_area("Ordinance Text", value=item['text'], height=250, key=f"text_{idx}", disabled=True)
