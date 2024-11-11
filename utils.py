"""Contains utility functions"""
import random
import streamlit as st
from logzero import logger

import database_functions as db_funcs
def initialize_variables():
    """
    initializes streamlit variables used in the session state
    """
    _initialize_api_key()
    st.session_state['model'] = None
    st.session_state['user_text'] = None
    st.session_state['guest_text'] = None
    st.session_state['messages'] = []
    st.session_state['display_messages'] = []
    st.session_state['first_interaction'] = True
    st.session_state['pdfs_submitted']= False
    st.session_state['initial_response_generated']= False
    st.session_state['rate_limit'] = st.secrets['message_rate_limit']
    st.session_state['timeframe'] = st.secrets['timeframe_in_mins']
    st.session_state['variables_initialised'] = True
    
def _initialize_api_key():
    """
    Randomly initialises api key.
    """
    if 'gemini_api_key' not in st.session_state:
        st.session_state['gemini_api_key'] = random.choice(list(st.secrets['api_keys'].values()))
        logger.debug(f"This session uses the key {st.session_state['gemini_api_key']}")

# @st.cache_data(ttl=100)  # Cache for 90 seconds
def cached_get_message_count(email, timeframe):
    """Cache function to fetch message count"""
    db, cursor = db_funcs.initialize_database()
    return db_funcs.get_interaction_count(cursor, email, timeframe)

def initial_display_elements():
    st.markdown("""
        <style>
            h2 {
                color: #1E90FF; /* Blue color for h2 headings */
            }
            h3 {
                color: #1E90FF; /* Blue color for h3 headings */
            }
            h4 {
                color: #1E90FF; /* Blue color for h3 headings */
            }
            p, li {
                color: #FFFFFF; /* White color for paragraph and list items */
            }
        </style>
        """, unsafe_allow_html=True)
    
    st.header(""Network like a pro!", divider='rainbow')
    st.write("Generate insightful conversation starters by analyzing LinkedIn profiles")

    st.markdown("""
    ### How It Works
    1. **Login with Google**
    2. **Download LinkedIn Profiles**: Export your LinkedIn profile as a PDF, along with your conversation partner's profile.
    3. It's crucial you download the PDF from Linkedin's save profile as PDF button. 
    3. **Upload Profiles Here**: Upload both PDFs below and hit submit.
    4. Voila!
    """)
