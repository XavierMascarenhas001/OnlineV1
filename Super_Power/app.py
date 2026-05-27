import streamlit as st

from modules.control_file_master import run_control_file_master
from modules.project_tracker import run_project_tracker
from modules.merge_control_tracker import run_merge_control_tracker
from modules.outputs import run_outputs
from modules.target_price_reader import run_target_price_reader
from modules.workbank import run_workbank

st.set_page_config(page_title="Operations Toolkit", layout="wide")

st.title("📊 Operations Toolkit")

tool = st.sidebar.radio(
    "Select Tool",
    [
        "Control File Master",
        "Project Tracker",
        "Merge Control Tracker",
        "Outputs",
        "Target Price Reader",
        "Workbank"
    ]
)

if tool == "Control File Master":
    run_control_file_master()

elif tool == "Project Tracker":
    run_project_tracker()

elif tool == "Merge Control Tracker":
    run_merge_control_tracker()

elif tool == "Outputs":
    run_outputs()

elif tool == "Target Price Reader":
    run_target_price_reader()

elif tool == "Workbank":
    run_workbank()
