import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Municipal Ordinance Generator", layout="centered")

st.title("Municipal Ordinance Generator")

# Configure API key securely from Streamlit secrets
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("API Key not found. Please set GEMINI_API_KEY in your Streamlit secrets.")
    st.stop()

with st.form("ordinance_form"):
    city_name = st.text_input("City Name", value="McKinney")
    department = st.selectbox("Sponsoring Department", ["Library System", "Public Works", "Finance", "Parks & Rec", "City Manager's Office"])
    item_title = st.text_input("Short Title / Caption", placeholder="e.g., Amending Non-Resident Library Fees")
    substance = st.text_area("Core Substance / Policy Change", placeholder="Describe exactly what changes. Include fee amounts, effective dates, or specific code chapters being modified.")
    fiscal_impact = st.text_input("Fiscal Impact / Funding Source", placeholder="e.g., Net positive revenue of $5,000 annually to General Fund")
    
    submitted = st.form_submit_with_button("Generate Draft Ordinance")

if submitted:
    if not substance or not item_title:
        st.error("Please fill out the Title and Core Substance fields.")
    else:
        with st.spinner("Drafting ordinance based on municipal template..."):
            
            prompt = f"""
            You are a municipal legal assistant. Draft a formal city ordinance based on the following structured inputs and the strict template provided below. Maintain standard Texas municipal legal boilerplate (severability, repealer, effective date).

            INPUTS:
            - City: {city_name}
            - Department: {department}
            - Title/Caption Focus: {item_title}
            - Substance of Change: {substance}
            - Fiscal Notes: {fiscal_impact}

            TEMPLATE TO FOLLOW:
            ORDINANCE NO. ______
            AN ORDINANCE OF THE CITY OF {city_name.upper()}, TEXAS, AMENDING THE CODE OF ORDINANCES BY {item_title.upper()}; PROVIDING A REPEALER CLAUSE; PROVIDING A SEVERABILITY CLAUSE; AND PROVIDING AN EFFECTIVE DATE.
            
            BE IT ORDAINED BY THE CITY COUNCIL OF THE CITY OF {city_name.upper()}, TEXAS:
            [Generate appropriate SECTIONS here mapping the 'Substance of Change' accurately into legal language]
            """
            
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            
            st.subheader("Generated Draft")
            st.text_area("Review and Edit Draft", value=response.text, height=400)
