"""Contains utility functions"""
import random
import streamlit as st
from logzero import logger

def initialize_variables():
    """
    initializes streamlit variables used in the session state
    """
    _initialize_api_key()
    st.session_state['rate_limit'] = st.secrets['message_rate_limit']
    st.session_state['variables_initialised'] = True
    
def _initialize_api_key():
    """
    Randomly initialises api key.
    """
    if 'gemini_api_key' not in st.session_state:
        st.session_state['gemini_api_key'] = random.choice(list(st.secrets['api_keys'].values()))
        logger.debug(f"This session uses the key {st.session_state['gemini_api_key']}")

