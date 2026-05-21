import streamlit as st
import google.generativeai as genai
from docx import Document
import io
import datetime
from PIL import Image
import requests
import PyPDF2
import json

# Set page config at the very beginning
st.set_page_config(page_title="Municipal Ordinance Portal", layout="wide", page_icon="🏛️")

# --- Helper functions ---
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

def extract_text_from_pdf(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def create_word_docx(text_content):
    doc = Document()
    doc.add_paragraph(text_content)
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream

# --- Custom CSS ---
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

        /* Dashboard Cards */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border: 2px solid var(--municipal-border) !important;
            border-radius: 8px !important;
            background-color: white !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 15px;
            padding: 5px;
        }

        /* Expander */
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

        /* Buttons */
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
        
        /* Info Blocks */
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

# Apply CSS & Header
set_custom_css()
banner_image_bytes = get_cropped_banner("https://www.vmcdn.ca/f/files/localprofile/images/news/mckinneytexascityhall12257-42.jpg;w=960")
if banner_image_bytes:
    st.image(banner_image_bytes, use_container_width=True) 
st.title("Municipal Ordinance Portal - McKinney, Texas")

# Init Memory
if 'history' not in st.session_state:
    st.session_state.history = []

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except KeyError:
    st.error("API Key not found. Please set GEMINI_API_KEY in your Streamlit secrets.")
    st.stop()

# --- Navigation ---
tab1, tab2, tab3 = st.tabs(["📝 Draft New Ordinance", "🔍 Analyze Document", "📊 Ordinance Dashboard"])

# ==========================================
# TAB 1: GENERATE FROM SCRATCH
# ==========================================
with tab1:
    st.markdown("### Draft a New Ordinance")
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
            with st.spinner("Drafting formal town ordinance..."):
                prompt = f"""
                You are a municipal legal assistant for the Town of {city_name}, Texas. Draft a formal town ordinance based on the following structured inputs. Maintain standard Texas municipal legal boilerplate (severability, repealer, effective date).
                INPUTS:
                - Town: {city_name}
                - Department: {department}
                - Title: {item_title}
                - Substance: {substance}
                - Fiscal Notes: {fiscal_impact}
                """
                response = model.generate_content(prompt)
                
                record = {
                    "type": "Generated",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "city": city_name,
                    "department": department,
                    "title": item_title,
                    "summary_or_substance": substance,
                    "fiscal": fiscal_impact,
                    "text": response.text
                }
                st.session_state.history.insert(0, record)
                st.success("Draft created successfully! Switch to the Dashboard to view.")

# ==========================================
# TAB 2: ANALYZE UPLOADED PDF
# ==========================================
with tab2:
    st.markdown("### Translate Legalese to Plain English")
    st.write("Upload a draft ordinance or resolution (PDF) to generate a summary, identify the department, and extract costs.")
    
    uploaded_file = st.file_uploader("Upload Document (.pdf)", type="pdf")
    
    if uploaded_file is not None:
        if st.button("Analyze Document"):
            with st.spinner("Reading and analyzing document..."):
                try:
                    document_text = extract_text_from_pdf(uploaded_file)
                    
                    prompt = f"""
                    You are an expert municipal analyst. Read the following text extracted from a municipal document.
                    Extract the following information and return it STRICTLY as a JSON object with these keys:
                    - "title": A short, 3-6 word title based on the document's subject.
                    - "summary": A clear, plain language summary of what this document actually does (under 4 sentences).
                    - "department": The specific city department bringing or sponsoring the item. If not explicitly stated, infer based on content or return "Not specified".
                    - "costs": The financial impact, budget, or costs associated. If none are mentioned, state "No fiscal impact mentioned."

                    Document Text:
                    {document_text}
                    """
                    
                    # Force Gemini to return JSON
                    response = model.generate_content(
                        prompt,
                        generation_config={"response_mime_type": "application/json"}
                    )
                    
                    result_data = json.loads(response.text)
                    
                    record = {
                        "type": "Analyzed",
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "city": "McKinney (Inferred)",
                        "department": result_data.get("department", "Unknown"),
                        "title": result_data.get("title", uploaded_file.name),
                        "summary_or_substance": result_data.get("summary", "No summary generated."),
                        "fiscal": result_data.get("costs", "Unknown"),
                        "text": document_text # Save the extracted text
                    }
                    st.session_state.history.insert(0, record)
                    st.success("Document analyzed! Switch to the Dashboard to view the breakdown.")
                except Exception as e:
                    st.error(f"Error analyzing document: {str(e)}")

# ==========================================
# TAB 3: DASHBOARD
# ==========================================
with tab3:
    st.markdown("### Ordinance Dashboard")
    
    if len(st.session_state.history) == 0:
        st.info("No activity yet. Go to 'Draft New Ordinance' or 'Analyze Document' to begin.")
    else:
        st.write(f"**Total Records:** {len(st.session_state.history)}")
        
        for idx, item in enumerate(st.session_state.history):
            with st.container(border=True):
                # Indicate if it was generated by the AI or analyzed from an upload
                icon = "✨ Generated" if item['type'] == "Generated" else "🔍 Analyzed"
                st.markdown(f"#### {icon}: {item['title']}")
                
                st.markdown("**Key Info:**")
                col1, col2, col3 = st.columns(3)
                col1.info(f"**🏢 Dept:**<br>{item['department']}")
                col2.info(f"**💰 Fiscal Impact:**<br>{item['fiscal']}")
                col3.info(f"**🕒 Time:**<br>{item['timestamp']}")
                
                # Change the label based on what it is
                substance_label = "Core Substance:" if item['type'] == "Generated" else "Plain English Summary:"
                st.markdown(f"**{substance_label}**")
                st.write(item['summary_or_substance'])
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                exp_col, dl_col = st.columns([4, 1])
                with exp_col:
                    exp_label = "🔍 View Full Draft" if item['type'] == "Generated" else "🔍 View Extracted Text"
                    with st.expander(exp_label):
                        st.text_area("Full Text", value=item['text'], height=350, key=f"text_{idx}", label_visibility="collapsed", disabled=True)
                
                with dl_col:
                    if item['type'] == "Generated":
                        word_file = create_word_docx(item['text'])
                        st.download_button(
                            label="📥 Download Docx",
                            data=word_file,
                            file_name=f"Draft_{item['department'].replace(' ', '_')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"dl_btn_{idx}"
                        )