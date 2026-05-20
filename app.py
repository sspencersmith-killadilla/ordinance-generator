import streamlit as st
import google.generativeai as genai
from docx import Document
import io
import datetime

st.set_page_config(page_title="Municipal Ordinance Generator", layout="wide", page_icon="🏛️")

# --- CUSTOM CSS INJECTION ---
def set_custom_css():
    st.markdown("""
        <style>
        /* Define the core municipal teal color from the reference image */
        :root {
            --municipal-teal: #166a84;
            --municipal-dark: #0f4b5e;
        }

        /* Style the Tabs to look like the blocky navigation sections */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            border-bottom: 2px solid var(--municipal-teal);
        }
        .stTabs [data-baseweb="tab"] {
            background-color: var(--municipal-teal);
            color: white !important;
            border-radius: 6px 6px 0px 0px;
            padding: 12px 24px;
            font-weight: 600;
        }
        .stTabs [aria-selected="true"] {
            background-color: var(--municipal-dark);
        }

        /* Style the Dashboard Expanders to look like professional cards */
        [data-testid="stExpander"] {
            border: 2px solid var(--municipal-teal);
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 15px;
            background-color: white;
        }
        
        /* The header of the expander */
        [data-testid="stExpander"] summary {
            background-color: var(--municipal-teal);
            color: white;
            padding: 10px;
        }
        
        /* Force the text inside the expander header to be white */
        [data-testid="stExpander"] summary p {
            color: white !important;
            font-size: 1.1rem;
            font-weight: 600;
        }
        
        /* Style the st.info boxes to match the vibe */
        [data-testid="stAlert"] {
            background-color: #f0f7f9;
            color: var(--municipal-dark);
            border: 1px solid var(--municipal-teal);
        }
        </style>
    """, unsafe_allow_html=True)

# Run the CSS function
set_custom_css()

# --- Main App Logic ---
st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Flower_Mound_Texas_Town_Hall.jpg/800px-Flower_Mound_Texas_Town_Hall.jpg", use_container_width=True)
st.title("Municipal Ordinance Generator & Dashboard")

if 'history' not in st.session_state:
    st.session_state.history = []

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("API Key not found. Please set GEMINI_API_KEY in your Streamlit secrets.")
    st.stop()

def create_word_docx(text_content):
    doc = Document()
    doc.add_paragraph(text_content)
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream

tab1, tab2 = st.tabs(["📝 Draft New Ordinance", "📊 Ordinance Dashboard"])

with tab1:
    st.markdown("### Create a New Draft")
    with st.form("ordinance_form"):
        city_name = st.text_input("City Name", value="Flower Mound")
        department = st.selectbox("Sponsoring Department", ["Library System", "Public Works", "Finance", "Parks & Rec", "Town Manager's Office"])
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
                You are a municipal legal assistant. Draft a formal town ordinance based on the following structured inputs. Maintain standard Texas municipal legal boilerplate (severability, repealer, effective date).

                INPUTS:
                - Town: {city_name}
                - Department: {department}
                - Title: {item_title}
                - Substance: {substance}
                - Fiscal Notes: {fiscal_impact}

                TEMPLATE TO FOLLOW:
                ORDINANCE NO. ______
                AN ORDINANCE OF THE TOWN OF {city_name.upper()}, TEXAS, AMENDING THE CODE OF ORDINANCES BY {item_title.upper()}; PROVIDING A REPEALER CLAUSE; PROVIDING A SEVERABILITY CLAUSE; AND PROVIDING AN EFFECTIVE DATE.
                
                BE IT ORDAINED BY THE TOWN COUNCIL OF THE TOWN OF {city_name.upper()}, TEXAS:
                [Generate appropriate SECTIONS here]
                """
                
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt)
                generated_text = response.text
                
                record = {
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "city": city_name,
                    "department": department,
                    "title": item_title,
                    "fiscal": fiscal_impact,
                    "text": generated_text
                }
                st.session_state.history.insert(0, record)
                
                st.success("Draft created successfully! You can view it below or switch to the Dashboard tab.")
                st.text_area("Review Draft", value=generated_text, height=300)
                word_file = create_word_docx(generated_text)
                st.download_button(
                    label="📥 Download this draft as Word Document",
                    data=word_file,
                    file_name=f"Draft_{department.replace(' ', '_')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

with tab2:
    st.markdown("### Ordinance History & Review")
    
    if len(st.session_state.history) == 0:
        st.info("No ordinances generated yet. Go to the 'Draft New Ordinance' tab to get started.")
    else:
        st.write(f"**Total Drafts in Session:** {len(st.session_state.history)}")
        st.divider()
        
        for idx, item in enumerate(st.session_state.history):
            with st.expander(f"📄 {item['title']} ({item['department']} - {item['timestamp']})", expanded=(idx==0)):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown("**Metadata:**")
                    st.write(f"- **Town:** {item['city']}")
                    st.write(f"- **Dept:** {item['department']}")
                    st.write(f"- **Fiscal Impact:** {item['fiscal']}")
                    
                    word_file = create_word_docx(item['text'])
                    st.download_button(
                        label="📥 Download (.docx)",
                        data=word_file,
                        file_name=f"Draft_{item['department'].replace(' ', '_')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"dl_btn_{idx}" 
                    )
                
                with col2:
                    st.markdown("**Generated Text:**")
                    st.text_area("Ordinance Text", value=item['text'], height=250, key=f"text_{idx}", disabled=True)