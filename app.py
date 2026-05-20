import streamlit as st
import google.generativeai as genai
from docx import Document
import io
import datetime
from PIL import Image
import requests

# Set page config at the very beginning
st.set_page_config(page_title="Municipal Ordinance Generator", layout="wide", page_icon="🏛️")

# --- Helper function: download and crop image for a wide banner ---
def get_cropped_banner(url):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        img = Image.open(response.raw)
        
        # Define crop area (left, top, right, bottom)
        # We will crop a 300px strip from the top of the image
        width, height = img.size
        banner_height = 300
        crop_box = (0, 0, width, banner_height)
        cropped_img = img.crop(crop_box)
        
        # Convert back to bytes for st.image
        img_byte_arr = io.BytesIO()
        cropped_img.save(img_byte_arr, format=img.format)
        img_byte_arr.seek(0)
        return img_byte_arr
    except Exception as e:
        st.error(f"Error loading banner image: {str(e)}")
        return None

# --- Custom CSS to match McKinney reference aesthetic ---
def set_custom_css():
    st.markdown("""
        <style>
        /* Define precise municipal teal color palette from reference image */
        :root {
            --municipal-primary: #166a84;
            --municipal-primary-dark: #0f4b5e;
            --municipal-secondary: #f0f7f9;
            --municipal-border: #d1e2e8;
            --municipal-text: #2c3e50;
        }

        /* Generic sans-serif font applied everywhere */
        * {
            font-family: sans-serif !important;
        }

        /* Style the Tabs to look like the solid, blocky navigation segments */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            border-bottom: 3px solid var(--municipal-primary);
        }
        .stTabs [data-baseweb="tab"] {
            background-color: var(--municipal-primary);
            color: white !important;
            border-radius: 6px 6px 0px 0px;
            padding: 15px 30px;
            font-weight: 700;
            font-size: 1.1rem;
            transition: background-color 0.3s ease;
            text-transform: uppercase;
        }
        .stTabs [data-baseweb="tab"]:hover {
            background-color: var(--municipal-primary-dark);
        }
        .stTabs [aria-selected="true"] {
            background-color: var(--municipal-primary-dark);
        }

        /* Style the Dashboard Expanders to look like professional cards */
        [data-testid="stExpander"] {
            border: 2px solid var(--municipal-border);
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 20px;
            background-color: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        
        /* The summary header of the expander card */
        [data-testid="stExpander"] summary {
            background-color: var(--municipal-primary);
            color: white;
            padding: 12px;
            border-bottom: 2px solid var(--municipal-border);
        }
        
        /* Force the text inside the expander header to be white, bold, and larger */
        [data-testid="stExpander"] summary p {
            color: white !important;
            font-size: 1.2rem;
            font-weight: 700;
            margin: 0;
            text-transform: none; 
        }
        
        /* Style standard st.write and list items to be cleaner and spaced better */
        [data-testid="stExpander"] st.write {
            color: var(--municipal-text);
            margin-bottom: 5px;
        }
        
        /* Professional style for primary buttons */
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
        
        /* Ensure st.info blocks use a consistent professional style */
        [data-testid="stAlert"] {
            background-color: var(--municipal-secondary);
            color: var(--municipal-primary);
            border: 1px solid var(--municipal-primary);
            border-radius: 5px;
            font-weight: 500;
        }
        
        /* General page titles use the primary teal color */
        h1 {
            color: var(--municipal-primary);
        }
        </style>
    """, unsafe_allow_html=True)

# Define Word doc creation function
def create_word_docx(text_content):
    doc = Document()
    doc.add_paragraph(text_content)
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream

# --- Apply Custom Aesthetics ---
set_custom_css()

# --- Display the Cropped Banner Image ---
banner_image_bytes = get_cropped_banner("https://www.vmcdn.ca/f/files/localprofile/images/news/mckinneytexascityhall12257-42.jpg;w=960")
if banner_image_bytes:
    st.image(banner_image_bytes, use_container_width=True) # Full width banner
st.title("Ordinance Generator & Dashboard - McKinney, Texas")

# Initialize memory (Session State)
if 'history' not in st.session_state:
    st.session_state.history = []

# Configure API key securely
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("API Key not found. Please set GEMINI_API_KEY in your Streamlit secrets.")
    st.stop()

# --- Create Professional Style Tabs ---
tab1, tab2 = st.tabs(["📝 Draft New Ordinance", "📊 Ordinance Dashboard"])

# ==========================================
# TAB 1: GENERATOR
# ==========================================
with tab1:
    st.markdown("### Create a New Draft")
    with st.form("ordinance_form"):
        city_name = st.text_input("Town Name", value="McKinney")
        department = st.selectbox("Sponsoring Department", ["Planning & Zoning", "Public Works", "Finance", "Parks & Rec", "Economic Development", "Town Manager's Office"])
        item_title = st.text_input("Short Title / Caption", placeholder="e.g., Rezoning specific property to commercial")
        substance = st.text_area("Core Substance / Policy Change", placeholder="Describe exactly what changes.")
        fiscal_impact = st.text_input("Fiscal Impact / Funding Source", placeholder="e.g., Projected increase of $50,000 annually to General Fund")
        
        submitted = st.form_submit_button("Generate Draft Ordinance")

    if submitted:
        if not substance or not item_title:
            st.error("Please fill out the Title and Core Substance fields.")
        else:
            with st.spinner(f"Drafting formal town ordinance for the Town of {city_name} based on municipal template..."):
                prompt = f"""
                You are a municipal legal assistant for the Town of {city_name}, Texas. Draft a formal town ordinance based on the following structured inputs. Maintain standard Texas municipal legal boilerplate (severability, repealer, effective date).

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
                
                st.success(f"Draft created successfully for {city_name}! View it below or switch to the Dashboard tab.")
                
                st.text_area("Review Draft", value=generated_text, height=300)
                word_file = create_word_docx(generated_text)
                st.download_button(
                    label=f"📥 Download Draft as Word Document (.docx)",
                    data=word_file,
                    file_name=f"Draft_Ordinance_{department.replace(' ', '_')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

# ==========================================
# TAB 2: DASHBOARD
# ==========================================
with tab2:
    st.markdown("### Ordinance History & Review - Dashboard")
    
    if len(st.session_state.history) == 0:
        st.info("No ordinances generated yet. Please navigate to the 'Draft New Ordinance' tab to get started.")
    else:
        st.write(f"**Total Drafts in Session:** {len(st.session_state.history)}")
        st.divider()
        
        # Display saved history iteratively
        for idx, item in enumerate(st.session_state.history):
            # This label structure matches 'Library System - 2026-05-20 23:46:38' in image reference
            expander_title = f"📄 {item['title']} ({item['department']} - {item['timestamp']})"
            
            # The CSS will restyle this expander into a professional card structure
            with st.expander(expander_title, expanded=(idx==0)):
                # Use columns for metadata and full text detail review
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown("**Metadata:**")
                    # Clean markdown list spacing
                    st.markdown(f"* **Town:** {item['city']}")
                    st.markdown(f"* **Dept:** {item['department']}")
                    st.markdown(f"* **Fiscal Impact:** {item['fiscal']}")
                    st.markdown(f"* **Generated:** {item['timestamp']}")
                    
                    word_file = create_word_docx(item['text'])
                    st.download_button(
                        label="📥 Download (.docx)",
                        data=word_file,
                        file_name=f"Draft_{item['department'].replace(' ', '_')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"dl_btn_{idx}" # Keys must be unique for loops
                    )
                
                with col2:
                    st.markdown("**Generated Text:**")
                    # Display the full text in a disabled, large text area that matches the layout vibe
                    st.text_area("Ordinance Text", value=item['text'], height=450, key=f"text_{idx}", disabled=True)