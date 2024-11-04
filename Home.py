# these are the imports
import google.generativeai as genai
import os
import streamlit as st
import fitz
from logzero import logger
import google.auth.transport.requests
import google.oauth2.id_token
from google_auth_oauthlib.flow import Flow
import datetime
import streamlit.components.v1 as components
import utils
import database_functions as db_funcs
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
os.environ['GOOGLE_CLIENT_ID'] = st.secrets['google_oauth']['client_id']

flow = Flow.from_client_config(
    {
        "web": {
            "client_id": st.secrets["google_oauth"]["client_id"],
            "project_id": st.secrets["google_oauth"]["project_id"],
            "auth_uri": st.secrets["google_oauth"]["auth_uri"],
            "token_uri": st.secrets["google_oauth"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["google_oauth"]["auth_provider_x509_cert_url"],
            "client_secret": st.secrets["google_oauth"]["client_secret"],
            "redirect_uris": st.secrets["google_oauth"]["redirect_uris"]
        }
    },
    scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email'], # 'https://www.googleapis.com/auth/userinfo.profile'],
    redirect_uri= st.secrets["google_oauth"]["redirect_uris"][0]
)

def google_oauth():
    logger.debug("Reached google_oauth")
    authorization_url, state = flow.authorization_url(prompt='consent')
    st.session_state['state'] = state
    
    st.write(f"[Login with Google]({authorization_url})")
    # with st.container():
    #     st.markdown(f'<a href="{authorization_url}" target="_self" class="button primary" style="background-color: #4285F4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 10px;">Login with Google</a>', unsafe_allow_html=True)
    logger.debug("Reached end of google_oauth")

def process_auth_callback():
    logger.debug("Reached process auth callback")
    if 'code' in st.query_params.keys():
        logger.debug("Reached process auth callback - code ")
        code = st.query_params['code']
        try:
            logger.debug("Reached process auth callback - code try block")
            flow.fetch_token(code=code)
            credentials = flow.credentials
            request = google.auth.transport.requests.Request()
            id_info = google.oauth2.id_token.verify_oauth2_token(
                credentials._id_token, request, os.environ['GOOGLE_CLIENT_ID'], clock_skew_in_seconds=3)
            st.session_state['credentials'] = credentials_to_dict(credentials)
            return id_info
        except Exception as e:
            st.error(f"Error fetching token: {e}")
            return None
    return None

def credentials_to_dict(credentials):
    return {'token': credentials.token, 'refresh_token': credentials.refresh_token, 'token_uri': credentials.token_uri, 'client_id': credentials.client_id, 'client_secret': credentials.client_secret, 'scopes': credentials.scopes}

def llm_setup():
    """Setting up Gemini sources."""
    genai.configure(api_key=st.session_state['gemini_api_key'])
    system_behavior = st.secrets['system_behavior']
    generation_config = genai.GenerationConfig(temperature=0.25)
    st.session_state['model'] = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_behavior, generation_config=generation_config)

def parse_pdf(file):
    """Extracts text from uploaded PDF."""
    text = ""
    if file:
        pdf_document = fitz.open(stream=file.read(), filetype="pdf")  # Read the PDF file
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
    return text

def get_llm_response():
    """Send the parsed text to the Gemini model and return generated questions."""
    # logger.debug("get_llm_response() called")  # Add this debug log
    model = st.session_state['model']
    messages = st.session_state['messages']
    user_text = st.session_state['user_text']
    guest_text = st.session_state['guest_text']
    # logger.debug(messages)
    if not st.session_state['first_interaction']:
        final_prompt = messages
    else:
        final_prompt = f"""User profile: {user_text}\n Guest Profile: {guest_text}\n\n{st.secrets['question_prompt']}"""
        st.session_state['first_interaction'] = False
        st.session_state['messages'].append({"role":"user", "parts": [f"User profile: {user_text}\n Guest Profile: {guest_text}"]})
        # logger.debug(final_prompt)
    response = model.generate_content(final_prompt)
    return response.text

def initialise_side_bar_components():
    """
    Contains components that are present in the side bar, apart from pages.
    """
    
    user_pdf_content = db_funcs.get_user_pdf(cursor, st.session_state['user_info']['email'])
    if user_pdf_content:
        returning_user = True
        user_pdf_uploaded = True
    else:
        returning_user = False

    if 'preload_pdf' not in st.session_state:
        if returning_user:
            st.session_state.preload_pdf = True
        else:
            st.session_state.preload_pdf = False

    with st.sidebar:
        if st.session_state.preload_pdf:
            st.subheader("Your LinkedIn profile is loaded")
            
            # Wrap the button in a container with dark blue background
            
            if st.button("Re-upload user profile", disabled=not st.session_state.preload_pdf):
                st.session_state.preload_pdf = False
                st.session_state.first_interaction = True  # Ensure first_interaction is reset
                st.session_state.pdfs_submitted = False
                st.session_state['user_text'] = None  # Reset to ensure new conversation tips
                st.session_state['messages'] = []
                st.rerun()
        
        if not st.session_state.preload_pdf:
            st.subheader("Upload your profile")
            user_pdf = st.file_uploader("Upload user profile", type="pdf", key="main_pdf", label_visibility="hidden")
            user_pdf_uploaded = True

        # New file uploader for guest PDF
        st.subheader("Upload guest's profile")
        guest_pdf_disabled = st.session_state.get('guest_text') is not None
        guest_pdf = st.file_uploader("Upload guest profile", type="pdf", key="guest_pdf", label_visibility="hidden",disabled=guest_pdf_disabled)
        
        # Re-upload guest profile option
        if st.session_state.get('guest_text', None):
            if st.button("Re-upload guest profile"):
                # Clear out the guest profile and reset interaction to allow new guest upload
                st.session_state['guest_text'] = None
                st.session_state['first_interaction'] = True
                st.session_state['pdfs_submitted'] = False  # Reset state
                st.session_state['initial_response_generated']= False
                st.session_state['messages'] = []
                st.rerun()

        if st.button("Submit", type="primary"):
            if user_pdf_uploaded and guest_pdf:
                if not returning_user:    
                    user_text = parse_pdf(user_pdf)
                else:
                    user_text = user_pdf_content
                guest_text = parse_pdf(guest_pdf)
                st.session_state['user_text'] = user_text
                st.session_state['guest_text'] = guest_text
                st.session_state['pdfs_submitted'] = True
                st.session_state['first_interaction'] = True  # Ensure the new interaction begins
                db_funcs.save_user_if_not_exists(cursor, db, st.session_state['user_info']['email'], st.session_state.get('user_text', ''))
                st.rerun()
            else:
                st.error("Error: Please upload both your LinkedIn profile PDF and the guest's LinkedIn profile PDF.")

        # Add this at the end of the sidebar
        st.markdown("---")  # Horizontal line for visual separation
        st.warning("""Messages aren't stored across sessions!""", icon="⚠️")
        st.warning("""We save your LinkedIn profile just to load it faster the next time you visit.
                   We don't use any of the data to train models; we can't afford to train new models.""", icon="⚠️")
        
def add_refresh_warning():
    refresh_warning_js = '''
    <script>
    window.addEventListener('beforeunload', function (e) {
        e.preventDefault();
        e.returnValue = 'Hey, the session will get logged off if you refresh. Are you sure you want to continue?';
    });
    </script>
    '''
    components.html(refresh_warning_js, height=0)

if __name__ == "__main__":
    st.set_page_config(page_title='Linkedin Convo Helper', page_icon=':speech_balloon:', initial_sidebar_state='expanded', layout='wide')
    login_status_container = st.container()
    logger.debug("Reached main")
    db, cursor = db_funcs.initialize_database()
    # Add the refresh warning
    # add_refresh_warning()
    
    if 'user_info' not in st.session_state:
        st.session_state['credentials'] = None
        st.session_state['user_info'] = None
        st.session_state['variables_initialised'] = False
        
    if st.session_state['user_info']:
        if not st.session_state['variables_initialised']:
            utils.initialize_variables()
            llm_setup()

        message_count = db_funcs.get_interaction_count(cursor, st.session_state['user_info']['email'], datetime.timedelta(minutes=st.session_state['timeframe']))
        with login_status_container:
            st.success(f"Welcome {st.session_state['user_info']['email']}. Setup is ready!")
            st.session_state['has_logged_in'] = True

        if message_count >= st.session_state['rate_limit']:
            st.error("You've reached today's quota of 10 messages. Please come back after 24 hours.")
        else:
            initialise_side_bar_components()
            
        # Chat display container
        chat_container = st.container()

        # This block deals with the initial user and guest pdf being set
        if st.session_state['pdfs_submitted'] and not st.session_state['initial_response_generated']:
            if st.session_state['user_text'] and st.session_state['guest_text']:
                response = get_llm_response()
                if response:
                    with chat_container:
                        st.chat_message("model").markdown(response)
                    st.session_state['messages'].append({"role":"model", "parts": [response]})
                    st.session_state['display_messages'].append({"role":"model", "parts": [response]})
                    st.session_state['first_interaction'] = False
                    st.session_state['initial_response_generated'] = True
                    st.rerun()  # Force a rerun to update the UI

        # Display existing messages
        with chat_container:
            for message in st.session_state['display_messages']:
                with st.chat_message(message["role"]):
                    st.markdown(message["parts"][0])

        # Add buttons after initial response
        if st.session_state.get('initial_response_generated', False):
            col1, col2, col3 = st.columns(3)
            
            def send_button_message(display_message, llm_prompt):
                st.session_state['user_input'] = display_message
                st.session_state['llm_prompt'] = llm_prompt
                st.session_state['button_clicked'] = True

            with col1:
                if st.button("Linkedin Connection Note", key="btn1"):
                    send_button_message(
                        "Help me create a Linkedin connection note",
                        "Help me create a linkedin connection note. The goal is to simply network. use the commonalities in our profiles to make the note catchy. Make it professional and actionable, Invite for a coffee or a virtual chat. Since it's linkedin make it within 300 characters."
                    )
            with col2:
                if st.button("Informational Interview", key="btn2"):
                    send_button_message("Help me setup an informational interview.", 
                                        "Help me setup an informational interview. The goal is to get to know more about the person, the company and the role they are in. Use my profile and common experiences to ask specific questions. And ask for a virtual coffee chat. Just give me the message to send.")
            with col3:
                if st.button("Referral Request", key="btn3"):
                    send_button_message("Help me get a referral for a role.", 
                                        "Help me get a referral for a role.The goal is to be direct and ask a referral for the role. For now assume the role i'm asking for is <the_role>. Use my skills and the guest's common ground to make me a strong candidate. Express genuine interest in the company and the role. Show the guest that i've done my research. Be respectful. Be brief. Just give me the message to send.")

        # Handle new user input
        if st.session_state['user_text'] and st.session_state['guest_text'] and not st.session_state['first_interaction']:
            user_input = st.chat_input("Type your message here", key="chat_input")
            
            if user_input or st.session_state.get('button_clicked', False):
                if st.session_state.get('button_clicked', False):
                    display_prompt = st.session_state['user_input']
                    llm_prompt = st.session_state['llm_prompt']
                    st.session_state['button_clicked'] = False
                else:
                    display_prompt = user_input
                    llm_prompt = user_input

                message_count = utils.cached_get_message_count(st.session_state['user_info']['email'], datetime.timedelta(minutes=st.session_state['timeframe']))
                if message_count < st.session_state['rate_limit']:
                    with chat_container:
                        st.chat_message("user").markdown(display_prompt)
                    st.session_state['messages'].append({"role":"user", "parts": [llm_prompt]})
                    st.session_state['display_messages'].append({"role":"user", "parts": [display_prompt]})
                    db_funcs.save_chat_message(cursor, db, st.session_state['user_info']['email'], "user", display_prompt) 
                    
                    with chat_container:
                        with st.spinner("Generating response... please wait"):
                            response = get_llm_response()
                        with st.chat_message("model"):
                            st.markdown(response)
                    st.session_state['messages'].append({"role":"model", "parts": [response]})
                    st.session_state['display_messages'].append({"role":"model", "parts": [response]})
                    db_funcs.save_chat_message(cursor, db, st.session_state['user_info']['email'], "model", response)
                else:
                    st.error("You've reached today's quota of 10 messages. Please come back after 24 hours.")

        logger.debug(f"User {st.session_state['user_info']['email']} reached {message_count} messages")
    else:
        user_info = process_auth_callback()
        if user_info:
            st.session_state['user_info'] = user_info
            st.rerun()
        else:
            with login_status_container:
                st.warning(body="You're not logged in, please login to use the assistant")
                google_oauth()
                logger.debug("Code to make user login")
    
    








