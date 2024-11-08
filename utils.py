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
    
    st.header("Empower Your Conversations with Thoughtful Starters! 💬", divider='rainbow')
    st.write("Generate insightful conversation starters by analyzing LinkedIn profiles")

    st.subheader("About LinkedInConversationHelper")
    st.markdown("""
    **LinkedInConversationHelper** is a smart assistant to help you connect more meaningfully with your LinkedIn connections. By analyzing similarities between your LinkedIn profile and your target's profile, this tool generates thoughtful, personalized questions to help you start conversations.

    Whether you’re networking, looking for referrals, or simply aiming for a meaningful exchange, LinkedInConversationHelper offers customized conversation starters based on shared experiences, career paths, and life insights.
    """)

    st.markdown("""
    ### What Can You Do with LinkedInConversationHelper?
    - **Identify Common Ground**: Find conversation points based on shared career paths, skills, and experiences.
    - **Get Tailored Questions**: Receive a set of personalized questions crafted to help you connect authentically.
    - **Break the Ice Confidently**: Start conversations with confidence, knowing you have insights that resonate with your connection.
    """)

    st.markdown("""
    ### How It Works
    1. **Login with Google**
    1. **Download LinkedIn Profiles**: Export your LinkedIn profile as a PDF, along with your conversation partner's profile.
    2. **Upload Profiles Here**: Drag and drop both PDFs below and hit submit.
    3. **Receive Customized Questions**: Instantly receive 6 questions to help you engage thoughtfully:
       - 2 **personal** questions to find common ground
       - 2 **career-related** questions
       - 1 **philosophical** open-ended question about life
       - 1 **career advice** question
    """)

    st.markdown("""
    ### Example Questions
    Here are examples of the types of questions you might receive:
    - **Personal Question**: “What inspired you to transition from Software Engineer to a Product Manager? It seems like both of us have embraced career shifts!”
    - **Career Question**: “In your role as a Marketing Assistant, what’s been your biggest challenge with [relevant skill or field from user's experience]?”
    - **Philosophical Question**: “How do you find balance between work and life, given the demands of [shared field or responsibility]?”
    """)

    st.markdown("""
    ### Ready to Start?
    1. **Log in** using your Google credentials above.
    2. **Upload both profiles** (your own and your target’s) as PDFs.
    3. **Click “Submit”** and start connecting with insights that matter.""")