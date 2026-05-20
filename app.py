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
        /* Define precise municipal teal and color palette hex codes from reference vibe */
        :root {
            --municipal-primary: #0d5c75;
            --municipal-primary-dark: #0a4a5d;
            --municipal-secondary: #d9e6eb;
            --municipal-background: #ffffff;
            --municipal-sub-background: #f9fcfd;
            --municipal-text: #2c3e50;
        }

        /* Apply generic sans-serif font consistently - let the user's browser pick a suitable one */
        * {
            font-family: sans-serif !important;
        }

        /* Style the Tabs to look like the solid professional navigation blocks */
        .stTabs [data-baseweb="tab-list"] {
            gap: 15px;
            border-bottom: 2px solid var(--municipal-primary);
            padding: 10px 0px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: var(--municipal-primary);
            color: white !important;
            border-radius: 8px 8px 0px 0px;
            padding: 15px 30px;
            font-weight: 700;
            font-size: 1.1rem;
            transition: background-color 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .stTabs [data-baseweb="tab"]:hover {
            background-color: var(--municipal-primary-dark);
        }
        .stTabs [aria-selected="true"] {
            background-color: var(--municipal-primary-dark);
            border-bottom: 2px solid var(--municipal-primary-dark) !important;
        }

        /* Style the Dashboard Expanders as professional cards with colored headers/borders */
        [data-testid="stExpander"] {
            border: 3px solid var(--municipal-secondary);
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 20px;
            background-color: var(--municipal-background);
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            transition: box-shadow 0.3s ease;
        }
        [data-testid="stExpander"]:hover {
            box-shadow: 0 8px 15px rgba(0,0,0,0.1);
        }
        
        /* The summary header of the expander card */
        [data-testid="stExpander"] summary {
            background-color: var(--municipal-primary);
            color: white;
            padding: 15px;
            border-bottom: 2px solid var(--municipal-secondary);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        /* Style text within expander headers */
        [data-testid="stExpander"] summary p {
            color: white !important;
            font-size: 1.2rem;
            font-weight: 700;
            margin: 0;
            text-transform: none; /* Keep original case for title details */
        }
        /* Ensure toggle icon is white */
        [data-testid="stExpander"] summary div[data-testid="stExpanderToggle"] {
            color: white !important;
        }
        
        /* Spacing and clean backgrounds within side-by-side columns */
        [data-testid="column"] {
            padding: 15px;
            background-color: var(--municipal-sub-background);
            border-radius: 5px;
            margin: 5px;
        }
        
        /* Professional style for info/alert boxes (pale teal background, teal border) */
        [data-testid="stAlert"] {
            background-color: var(--municipal-sub-background);
            color: var(--municipal-primary);
            border: 1px solid var(--municipal-primary);
            border-radius: 5px;
            font-weight: 500;
        }
        
        /* Consistent professional style for primary buttons */
        .stButton>button {
            background-color: var(--municipal-primary) !important;
            color: white !important;
            border-radius: 5px !important;
            border: none !important;
            padding: 10px 20px !important;
            font-weight: 600 !important;
            transition: background-color 0.3s ease !important;
            text-transform: uppercase;
        }
        .stButton>button:hover {
            background-color: var(--municipal-primary-dark) !important;
        }
        
        /* Title styling with subtle municipal primary color */
        h1 {
            color: var(--municipal-primary);
        }
        </style>
    """, unsafe_allow_html=True)

# Run the CSS function globally for consistent aesthetic application
set_custom_css()

# --- Main App Logic with McKinney Integration ---
# Use correct McKinney Texas City Hall image URL
st.image("https://vmcdn.ca/f/files/localprofile/images/news/mckinneytexascityhall12257-42.jpg;w=960", use_container_width=True, caption="McKinney Texas Town Hall")
st.title("Municipal Ordinance Generator & Dashboard - Town of McKinney")

# --- Initialize Memory (Session State) ---
if 'history' not in st.session_state:
    st.session_state.history = []

# Configure API key securely from Streamlit secrets
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("API Key not found. Please set GEMINI_API_KEY in your Streamlit secrets.")
    st.stop()

# Helper function to create Word Docs in-memory
def create_word_docx(text_content):
    doc = Document()
    doc.add_paragraph(text_content)
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream

# --- Create Professional Style Tabs ---
tab1, tab2 = st.tabs(["📝 Draft New Ordinance", "📊 Ordinance Dashboard"])

# ==========================================
# TAB 1: GENERATOR (with refined examples)
# ==========================================
with tab1:
    st.markdown("### Create a New Draft")
    with st.form("ordinance_form"):
        city_name = st.text_input("Town Name", value="McKinney")
        department = st.selectbox("Sponsoring Department", ["Planning & Zoning", "Public Works", "Finance", "Parks & Rec", "Economic Development", "Town Manager's Office"])
        item_title = st.text_input("Short Title / Caption", placeholder="e.g., Rezoning specific property to commercial")
        substance = st.text_area("Core Substance / Policy Change", placeholder="Describe exactly what changes, including precise property details, specific code sections/fees to amend, dates, etc.")
        fiscal_impact = st.text_input("Fiscal Impact / Funding Source", placeholder="e.g., Projected increase of $50,000 annually to General Fund")
        
        submitted = st.form_submit_button("Generate Draft Ordinance")

    if submitted:
        if not substance or not item_title:
            st.error("Please fill out the Title and Core Substance fields.")
        else:
            # Re-generate with precise McKinney/Texas town context in prompt
            with st.spinner(f"Drafting formal town ordinance for the Town of {city_name} based on municipal template..."):
                prompt = f"""
                You are a municipal legal assistant for the Town of {city_name}, Texas. Draft a formal town ordinance based on the following structured inputs. Maintain standard Texas municipal legal boilerplate (severability, repealer, effective date) and ensure professional, legally appropriate language mapping the 'Substance' input accurately into relevant sections.

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
                [Generate appropriate SECTIONS here with precise, legally relevant language mapping the 'Substance' input accurately]
                """
                
                # Call specific model version (as assumed fixed previously)
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt)
                generated_text = response.text
                
                # --- Save to History with professional timestamps and metadata ---
                record = {
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "city": city_name,
                    "department": department,
                    "title": item_title,
                    "fiscal": fiscal_impact,
                    "text": generated_text
                }
                # Add new record to the beginning for immediate dashboard view
                st.session_state.history.insert(0, record)
                
                st.success(f"Draft created successfully for {city_name}! View it below or in the Dashboard tab.")
                st.text_area("Review Draft", value=generated_text, height=300)
                word_file = create_word_docx(generated_text)
                # Formulate safe city/dept specific filename
                safe_city = city_name.replace(' ', '_')
                safe_dept = department.replace(' ', '_')
                st.download_button(
                    label=f"📥 Download Draft as Word Document (.docx)",
                    data=word_file,
                    file_name=f"Draft_Ordinance_{safe_city}_{safe_dept}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

# ==========================================
# TAB 2: DASHBOARD (professional visual history review)
# ==========================================
with tab1 if not st.session_state.history else tab2: # Show history in dashboard tab if exists, otherwise show empty msg/generator
    st.markdown("### Ordinance History & Review - Dashboard")
    
    if len(st.session_state.history) == 0:
        st.info("No ordinances generated yet. Please navigate to the 'Draft New Ordinance' tab to get started.")
    else:
        st.write(f"**Total Drafts in Session:** {len(st.session_state.history)}")
        st.divider()
        
        # Display saved history iteratively within styled card structures
        for idx, item in enumerate(st.session_state.history):
            # Formulate professional expander card title
            expander_title = f"📄 {item['title']} ({item['department']} - {item['timestamp']})"
            # Use columns inside for side-by-side metadata/text detail review within each professional card
            with st.expander(expander_title, expanded=(idx==0)):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown("**Metadata:**")
                    st.write(f"- **Town:** {item['city']}")
                    st.write(f"- **Dept:** {item['department']}")
                    st.write(f"- **Fiscal Impact:** {item['fiscal']}")
                    st.write(f"- **Generated:** {item['timestamp']}")
                    
                    word_file = create_word_docx(item['text'])
                    # Generate precise safe city/dept file names for downloads within history
                    safe_city_item = item['city'].replace(' ', '_')
                    safe_dept_item = item['department'].replace(' ', '_')
                    st.download_button(
                        label="📥 Download (.docx)",
                        data=word_file,
                        file_name=f"Draft_Ordinance_{safe_city_item}_{safe_dept_item}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"dl_btn_{idx}" # Unique key for each download button
                    )
                
                with col2:
                    st.markdown("**Generated Text:**")
                    st.text_area("Ordinance Text", value=item['text'], height=250, key=f"text_{idx}", disabled=True)