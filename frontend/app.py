import streamlit as st
import requests
import io
from PIL import Image
from typing import Dict, List, Any

# --- Page Configuration ---
st.set_page_config(
    page_title="AIDRA - AI Disaster Response",
    page_icon="🚨",
    layout="wide"
)

# --- Backend API URL ---
# Assumes backend is running on localhost:8000
API_URL = "http://localhost:8000/analyze/"
HEALTH_URL = "http://localhost:8000/health"

# --- Session State ---
# Initialize session state variables
if "session_id" not in st.session_state:
    st.session_state.session_id = None # Backend session ID
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "last_image" not in st.session_state:
    st.session_state.last_image = None
if "error" not in st.session_state:
    st.session_state.error = None

# --- Helper Functions ---

def check_backend_health():
    """Checks if the backend API is reachable."""
    try:
        response = requests.get(HEALTH_URL, timeout=2)
        if response.status_code == 200:
            return True
    except requests.ConnectionError:
        return False
    return False

def call_analysis_api(image_bytes: bytes, country: str, session_id: str) -> Dict[str, Any]:
    """
    Calls the backend API to analyze the image.
    """
    files = {"image": ("disaster.jpg", image_bytes, "image/jpeg")}
    data = {"country": country}
    headers = {}
    
    if session_id:
        headers["X-Session-ID"] = session_id
        
    try:
        response = requests.post(API_URL, files=files, data=data, headers=headers, timeout=300)
        
        if response.status_code == 200:
            return response.json()
        else:
            try:
                # Try to parse error from backend
                error_detail = response.json().get("detail", response.text)
            except requests.JSONDecodeError:
                error_detail = response.text
            st.session_state.error = f"API Error ({response.status_code}): {error_detail}"
            return None
            
    except requests.exceptions.RequestException as e:
        st.session_state.error = f"Connection Error: Could not connect to backend. {e}"
        return None



def display_results(result: Dict[str, Any]):
    """
    Renders the analysis result in a structured format.
    """
    st.header(f"Analysis Complete: **{result.get('disaster_type', 'N/A')}**")
    
    # --- Top Metrics ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Risk Level", result.get("risk_level", "N/A"))
    col2.metric("Confidence", f"{result.get('confidence', 0)}%")
    col3.metric("Lives in Danger?", "YES" if result.get('lives_in_danger') else "NO")

    st.divider()

    # --- Main Sections ---
    tab_steps, tab_safety, tab_analysis, tab_contacts = st.tabs([
        "🚨 **Immediate Steps**", 
        "🛡️ **Safety Measures**", 
        "📊 **Detailed Analysis**",
        "📞 **Emergency Contacts**"
    ])

    # Tab 1: Immediate Steps
    with tab_steps:
        st.subheader("Step-by-Step Instructions")
        instructions = result.get("instructions", [])
        if instructions:
            for i, step in enumerate(instructions, 1):
                st.markdown(f"**{i}.** {step}")
        else:
            st.write("No specific instructions provided.")
            
    # Tab 2: Safety Measures
    with tab_safety:
        st.subheader("Safety Measures")
        safety = result.get("safety_measures", {})
        
        st.markdown("##### Personal Safety")
        for item in safety.get("personal_safety", ["N/A"]):
            st.markdown(f"- {item}")
            
        st.markdown("##### Preventive Actions")
        for item in safety.get("preventive_actions", ["N/A"]):
            st.markdown(f"- {item}")
            
        st.markdown("##### Risk Mitigation Checklist")
        for item in safety.get("risk_mitigation_checklist", ["N/A"]):
            st.markdown(f"- {item}")
            
    # Tab 3: Detailed Analysis
    with tab_analysis:
        st.subheader("Detailed Image Analysis")
        st.write(result.get("analysis", "No detailed analysis available."))

    # Tab 4: Emergency Contacts
    # with tab_contacts:
    #     st.subheader(f"Emergency Contacts ({st.session_state.get('country', 'N/A')})")
    #     contacts = result.get("contacts", {})
    #     if contacts:
    #         st.json(contacts)
    #     else:
    #         st.write("No emergency contacts found.")
    
    with tab_contacts:
        st.subheader(f"Emergency Contacts ({st.session_state.get('country', 'N/A')})")

        contacts = result.get("contacts", {})

        if contacts:
            for name, number in contacts.items():

                # CARD WRAPPER (no blank space)
                card = st.container()
                with card:
                    col1, col2 = st.columns([4, 1])

                    # LEFT SIDE → name + number
                    with col1:
                        st.markdown(
                            f"""
                            <p style="font-size:20px; margin:6px 0;">
                                <span style="font-size:20px; color:#ff4081;">📞</span>
                                <b>{name}</b> — {number}
                            </p>
                            """,
                            unsafe_allow_html=True
                        )

                    # RIGHT SIDE → Copy button
                    with col2:
                        button_html = f"""
                        <script>
                            function copy_{name.replace(" ", "_")}() {{
                                navigator.clipboard.writeText("{number}");
                            }}
                        </script>
                        <button onclick="copy_{name.replace(" ", "_")}()" style="
                            padding:6px 10px;
                            background:#4CAF50;
                            color:white;
                            border:none;
                            border-radius:6px;
                            cursor:pointer;
                            width:100%;
                            margin-top:4px;
                        ">Copy</button>
                        """
                        st.markdown(button_html, unsafe_allow_html=True)

                # SMALL DIVIDER LINE BETWEEN CARDS
                st.markdown("<hr style='opacity:0.2;'>", unsafe_allow_html=True)

        else:
            st.write("No emergency contacts found.")







# --- Main Application UI ---

st.title("🚨 AI Disaster Response Assistant (AIDRA)")
st.markdown("Upload an image of a disaster or accident. The AI will analyze it and provide immediate response steps.")

# Check backend status
if not check_backend_health():
    st.error("**Backend Connection Error:** The FastAPI server is not running or is unreachable. Please start the backend (`./run.sh` or `uvicorn backend.main:app`) and refresh this page.")
else:
    # --- Sidebar for Uploads ---
    with st.sidebar:
        st.header("Upload Image")
        uploaded_file = st.file_uploader(
            "Choose an image...", 
            type=["jpg", "jpeg", "png"]
        )
        
        country = st.text_input("Your Country", "India")
        st.session_state.country = country # Save for display
        
        analyze_button = st.button("Analyze Image", type="primary", disabled=(uploaded_file is None))

        st.divider()
        st.info(
            f"**Session:** `{st.session_state.session_id or 'None'}`\n\n"
            "Your analysis history is stored per session. The session ID is sent to the backend to maintain memory."
        )

    # --- Main Content Area ---
    if analyze_button and uploaded_file:
        st.session_state.error = None # Clear old errors
        
        # Read image
        image = Image.open(uploaded_file)
        img_bytes_io = io.BytesIO()
        image.save(img_bytes_io, format=image.format)
        image_bytes = img_bytes_io.getvalue()
        
        st.session_state.last_image = image
        
        # Call API
        with st.spinner("Analyzing image... This may take a moment."):
            result = call_analysis_api(image_bytes, country, st.session_state.session_id)
        
        if result:
            st.session_state.analysis_result = result
            st.session_state.session_id = result.get("session_id") # Save new session ID
            st.balloons()
        else:
            st.session_state.analysis_result = None

    # Display error if any
    if st.session_state.error:
        st.error(st.session_state.error)

    # Display results
    if st.session_state.analysis_result:
        # Create two columns: one for the image, one for the results
        col_img, col_res = st.columns([1, 2])
        
        with col_img:
            if st.session_state.last_image:
                st.image(st.session_state.last_image, caption="Uploaded Image", use_container_width=True)
                
        with col_res:
            display_results(st.session_state.analysis_result)
            
    else:
        st.info("Upload an image and click 'Analyze Image' to begin.")