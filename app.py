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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, stream=True, headers=headers)
        response.raise_for_status()
        img = Image.open(response.raw)
        
        width, height = img.size
        banner_height = 300
        crop_box = (0, 0, width, banner_height)
        cropped_img = img.crop(crop_box)
        
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
        :root {
            --municipal-primary: #166a84;
            --municipal-primary-dark: #0f4b5e;
            --municipal-secondary: #f0f7f9;
            --municipal-border: #d1e2e8;
            --municipal-text: #2c3e50;
        }

        * { font-family: sans-serif !important; }

        /* Tab Styling */
        button[data-baseweb="tab"] {
            font-size: 1rem !important;
            font-weight: 700 !important;
            background-color: var(--municipal-secondary) !important;
            color: var(--municipal-primary) !important;
            border-radius: 5px 5px 0 0 !important;
            padding: 10px 24px !important;
            margin-right: 4px !important;
            border: 1px solid var(--municipal-border) !important;
            border-bottom: none !important;
            text-transform: uppercase;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            background-color: var(--municipal-primary) !important;
            color: white !important;
            border: 1px solid var(--municipal-primary) !important;
        }

        /* Style the native Streamlit containers to look like Dashboard Cards */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border: 2px solid var(--municipal-border) !important;
            border-radius: 8px !important;
            background-color: white !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 15px;
            padding: 5px;
        }

        /* Adjust the Expander used for the full text */
        [data-testid="stExpander"] {
            border: 1px solid var(--municipal-primary);
            border-radius: 6px;
            background-color: white;
            overflow: hidden;
            margin-top: 10px;
        }
        [data-testid="stExpander"] summary {
            background-color: var(--municipal-primary) !important;
            padding: 8px 15px !important;
        }
        [data-testid="stExpander"] summary p {
            color: white !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            margin-bottom: 0 !important;
        }
        [data-testid="stExpander"] summary svg {
            fill: white !important;
            color: white !important;
        }

        /* Professional style for primary buttons */
        .stButton>button {
            background-color: var(--municipal-primary) !important;
            color: white !important;
            border-radius: 5px !important;
            border: none !important;
            padding: 10px 20px !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            transition: background-color 0.3s ease !important;
            width: 100%;
        }
        .stButton>button:hover {
            background-color: var(--municipal-primary-dark) !important;
        }
        
        /* Ensure st.info blocks use a consistent professional style for Key Info */
        [data-testid="stAlert"] {
            background-color: var(--municipal-secondary);
            color: var(--municipal-text);
            border: 1px solid var(--municipal-border);
            border-radius: 5px;
            font-weight: 500;
            padding: 12px !important;
        }
        
        h1, h3, h4 { color: var(--municipal-primary); }
        </style>
    """, unsafe_allow_html=True)

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
    st.image(banner_image_bytes, use_container_width=True) 
st.title("Ordinance Generator & Dashboard - McKinney, Texas")

# Initialize memory (Session State)
if 'history' not in st.session_state:
    st.session_state.history = []

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
                
                # --- Save to History (Now including Substance!) ---
                record = {
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "city": city_name,
                    "department": department,
                    "title": item_title,
                    "substance": substance, # Saved for the dashboard
                    "fiscal": fiscal_impact,
                    "text": generated_text
                }
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
    st.markdown("### Ordinance History & Review")
    
    if len(st.session_state.history) == 0:
        st.info("No ordinances generated yet. Please navigate to the 'Draft New Ordinance' tab to get started.")
    else:
        st.write(f"**Total Drafts in Session:** {len(st.session_state.history)}")
        st.divider()
        
        for idx, item in enumerate(st.session_state.history):
            # Wrap each ordinance in a clean Dashboard Card (border container)
            with st.container(border=True):
                st.markdown(f"#### 📄 {item['title']}")
                
                # --- KEY INFO AT A GLANCE ---
                st.markdown("**Key Info:**")
                col1, col2, col3 = st.columns(3)
                col1.info(f"**🏢 Town & Dept:**<br>{item['city']} — {item['department']}")
                col2.info(f"**💰 Fiscal Impact:**<br>{item['fiscal']}")
                col3.info(f"**🕒 Generated:**<br>{item['timestamp']}")
                
                # --- CORE SUBSTANCE VISIBLE IMMEDIATELY ---
                st.markdown("**Core Substance:**")
                # Use .get() in case older entries in the session state didn't have substance saved
                st.write(item.get('substance', 'No substance details recorded.'))
                
                st.markdown("<br>", unsafe_allow_html=True) # Spacer
                
                # --- FULL TEXT EXPANDER AND DOWNLOAD ROW ---
                exp_col, dl_col = st.columns([4, 1])
                
                with exp_col:
                    with st.expander("🔍 View Full Ordinance Draft"):
                        st.text_area("Ordinance Text", value=item['text'], height=350, key=f"text_{idx}", label_visibility="collapsed", disabled=True)
                
                with dl_col:
                    word_file = create_word_docx(item['text'])
                    st.download_button(
                        label="📥 Download Docx",
                        data=word_file,
                        file_name=f"Draft_{item['department'].replace(' ', '_')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"dl_btn_{idx}"
                    )