import streamlit as st

from modules.Control_file_master import run_Control_file_master
from modules.project_tracker import run_project_tracker
from modules.merge_control_tracker import run_merge_control_tracker
from modules.outputs import run_outputs
from modules.target_price_reader import run_target_price_reader
from modules.workbank import run_workbank

st.set_page_config(page_title="Super Power", layout="wide")

st.title("⚡ Super Power System")

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
