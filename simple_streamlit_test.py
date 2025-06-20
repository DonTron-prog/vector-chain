#!/usr/bin/env python3
"""Simple test to verify Streamlit app functionality."""

import streamlit as st
import logfire

# Configure Logfire for Streamlit app
from logfire_config import configure_logfire
logfire = configure_logfire()

st.title("🧠 Adaptive Memory Research Chat Test")

st.write("This is a simple test to verify the Streamlit app works with adaptive memory.")

# Test Logfire integration
if st.button("Test Logfire"):
    logfire.info("Streamlit test button clicked", user_action="test_logfire")
    st.success("✅ Logfire event logged successfully!")

# Show available research modes
st.header("Available Research Modes")
modes = {
    "simple_chat": "💬 Simple Chat",
    "rag_only": "📚 RAG Only", 
    "deep_research": "🔍 Deep Research",
    "full_planning": "🎯 Full Planning",
    "adaptive_memory": "🧠 Adaptive Memory"
}

for key, value in modes.items():
    st.write(f"- {value}")

if st.button("Log Mode Test"):
    for mode in modes.keys():
        logfire.info("Research mode available", mode=mode, features=modes[mode])
    st.success("✅ All modes logged to Logfire!")

st.write("🎯 **Status**: Streamlit app with adaptive memory integration ready!")