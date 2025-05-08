import streamlit as st
import os
import sys

st.set_page_config(
    page_title="Loan Funnel Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pages.overview import show_overview
from pages.approval_analysis import show_approval_analysis
from pages.dropout_analysis import show_dropout_analysis
from pages.economic_impact import show_economic_impact
from pages.policy_comparision import show_policy_comparision

st.markdown("""
<style>
    /* Make all text black */
    .stApp, .stApp p, .stApp div, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 {
        color: black !important;
    }
    
    /* Make plotly chart text and axis black */
    .js-plotly-plot .plotly text,
    .gtitle, .ytitle, .xtitle, 
    .xtick text, .ytick text {
        fill: black !important;
        color: black !important;
    }
    
    /* Make axis lines black */
    .xgrid line, .ygrid line,
    .xtick, .ytick {
        stroke: black !important;
    }
</style>
""", unsafe_allow_html=True)



DB_PATH = "data/loan_funnel.db"
ALERT_LOG_PATH = "data/alerts_log.txt"

st.title("📊 Loan Funnel Analytics")

st.markdown(
    """
    <style>
    div.stButton > button {
        background-color: #f0f2f6;
        color: #262730;
        font-weight: bold;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        margin-right: 0.5rem;
    }
    div.stButton > button:hover {
        background-color: #e0e2e6;
    }
    div.stButton > button:focus {
        background-color: #4a89dc;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html = True
)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    overview_btn = st.button("📈 Overview")
with col2:
    approval_btn = st.button("✅ Approval Analysis")
with col3:
    dropout_btn = st.button("❌ Risk Analysis")
with col4:
    economic_btn = st.button("💰 Economic Impact")
with col5:
    policy_btn = st.button("🔄 Policy Comparison")

st.markdown("----")

if 'current_page' not in st.session_state:
    st.session_state.current_page = "overview"

if overview_btn:
    st.session_state.current_page = "overview"
if approval_btn:
    st.session_state.current_page = "approval"
if dropout_btn:
    st.session_state.current_page = "dropout"
if economic_btn:
    st.session_state.current_page = "economic"
if policy_btn:
    st.session_state.current_page = "policy"

if st.session_state.current_page == "overview":
    show_overview(DB_PATH, ALERT_LOG_PATH)
elif st.session_state.current_page == "approval":
    show_approval_analysis(DB_PATH)
elif st.session_state.current_page == "dropout":
    show_dropout_analysis(DB_PATH)
elif st.session_state.current_page == "economic":
    show_economic_impact(DB_PATH)
elif st.session_state.current_page == "policy":
    show_policy_comparision(DB_PATH)

st.markdown("---")
st.caption("Built by Aishwarya Gade | Data Analytics Project Demo")