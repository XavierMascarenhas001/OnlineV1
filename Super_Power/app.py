import streamlit as st

# =========================================================
# IMPORTANT: correct imports for your structure
# Super_Power/app.py (already inside Super_Power folder)
# so we use "modules.*" NOT "Super_Power.modules.*"
# =========================================================

from modules.control_file_master import run_control_file_master
from modules.project_tracker import run_project_tracker
from modules.merge_control_tracker import run_merge_control_tracker
from modules.outputs import run_outputs
from modules.target_price_reader import run_target_price_reader
from modules.workbank import run_workbank

# =========================================================
# STREAMLIT CONFIG
# =========================================================

st.set_page_config(
    page_title="Super Power",
    layout="wide"
)

st.title("⚡ Super Power System")

# =========================================================
# SIDEBAR NAVIGATION
# =========================================================

option = st.sidebar.selectbox(
    "Select Module",
    [
        "Control File Master",
        "Project Tracker",
        "Merge Control Tracker",
        "Outputs",
        "Target Price Reader",
        "Workbank"
    ]
)

# =========================================================
# ROUTING
# =========================================================

if option == "Control File Master":
    run_control_file_master()

elif option == "Project Tracker":
    run_project_tracker()

elif option == "Merge Control Tracker":
    run_merge_control_tracker()

elif option == "Outputs":
    run_outputs()

elif option == "Target Price Reader":
    run_target_price_reader()

elif option == "Workbank":
    run_workbank()
