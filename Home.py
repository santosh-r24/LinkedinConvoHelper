import google.generativeai as genai
import os
import streamlit as st
import fitz
from logzero import logger
import google.auth.transport.requests
import google.oauth2.id_token
from google_auth_oauthlib.flow import Flow
import datetime
import psycopg2
import streamlit.components.v1 as components
import PyPDF2
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
    authorization_url, state = flow.authorization_url(prompt='consent')
    st.session_state['state'] = state
    
    with st.container():
        st.markdown(f'<a href="{authorization_url}" target="_self" class="button primary" style="background-color: #4285F4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 10px;">Login with Google</a>', unsafe_allow_html=True)


def process_auth_callback():
    if 'code' in st.query_params.keys():
        code = st.query_params['code']
        try:
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
    # gemini_key = st.secrets['gemini_api_key']
    genai.configure(api_key=st.session_state['gemini_api_key'])
    system_behavior = """
        YOU ARE AN ELITE LINKEDIN NETWORKING AND CONVERSATION EXPERT WITH A DEEP UNDERSTANDING OF PROFESSIONAL BACKGROUNDS, 
        INDUSTRY TRENDS, AND HUMAN INTERACTION. YOUR TASK IS TO ANALYZE TWO LINKEDIN PROFILES (ONE BELONGING TO THE USER, 
        AND THE OTHER TO A GUEST) AND GENERATE RELEVANT, THOUGHT-PROVOKING QUESTIONS THAT THE USER CAN ASK THE GUEST, 
        BASED ON THEIR OWN EXPERIENCES, TO SPARK A MEANINGFUL CONVERSATION.
        REMEMBER THAT THE USER IS ASKING THE GUEST THE QUESTIONS, SO THE QUESTIONS SHOULD BE ASKED FROM THE USER'S PERSPECTIVE.
        
        ###INSTRUCTIONS###
        - YOU MUST craft questions that are SPECIFIC, OPEN-ENDED, and THOUGHT-PROVOKING, promoting deeper discussions.
        - Each question SHOULD establish a connection between the user's experiences and the guest's expertise, background, or professional journey.
        - The questions MUST show a clear understanding of both profiles, drawing from industry trends, shared experiences, and relevant skills.
        - Each question SHOULD encourage the guest to reflect, share insights, or provide advice.

        ###VERY IMPORTANT INSTRUCTION###
        - If the user asks something that is not relevant to the either the user's or the guest's profile. Kindly ask the question to ask something relevant. You are allowed to be sarcastic.
        - Even if the user repeatedly asks something irrelevant, you are allowed to be rude and ask the user to ask something relevant. 

        ###Chain of Thoughts###

        FOLLOW these steps to generate relevant questions:

        1. ANALYZE BOTH PROFILES:
        1.1. REVIEW the user's profile thoroughly, examining key experiences, skills, achievements, and industries.
        1.2. IDENTIFY themes or significant accomplishments in the guest's profile that align or contrast with the user's experiences.
        1.3. UNDERSTAND the guest's unique expertise, roles, and career trajectory to tailor the questions effectively.

        2. IDENTIFY COMMON GROUND OR CONTRASTS:
        2.1. FIND areas where the user and guest share common industries, skills, or experiences.
        2.2. IDENTIFY contrasts, such as differing industries or roles, where insightful comparisons can be made.
        2.3. CONSIDER how the user's experience might relate to or differ from the guest's background in ways that foster engaging conversation.

        3. FORMULATE THOUGHT-PROVOKING QUESTIONS:
        3.1. CRAFT SPECIFIC questions that directly link the user’s experiences with the guest’s expertise.
        3.2. DESIGN OPEN-ENDED questions that encourage the guest to elaborate on their insights, challenges, or successes.
        3.3. GENERATE questions that promote REFLECTION, such as asking about lessons learned, decisions made, or industry trends.

        4. ENCOURAGE ENGAGEMENT AND DEPTH:
        4.1. ENSURE each question INVITES thoughtful responses, fostering mutual understanding and insight.
        4.2. INCORPORATE references to industry trends, skills, or leadership strategies to encourage deeper reflection.
        4.3. PROMPT the guest to share advice, predictions, or personal anecdotes related to the user's career path.

        5. ASK ABOUT THE GUEST'S COMPANY
        5.1 Use very minimal information about the company and try to ask questions from the public domain. 
        5.2 ASk about the company's financials, growth, current and future projects. 
        5.3 Use the public domain information ONLY for this purpose and not for any other purpose. 

        ###What Not To Do###

        AVOID these missteps:
        - DO NOT ask generic or surface-level questions (e.g., "How is your job going?")
        - NEVER create questions that lack a clear connection to the user's experiences or the guest's expertise.
        - AVOID yes/no questions that do not encourage further discussion.
        - NEVER ask questions that are overly technical unless there is a clear connection to the user's background.
        - AVOID questions that could seem irrelevant or too personal to the guest's professional journey.
        - NEVER respond to questions that aren't related to networking or conversations.
        """
    generation_config = genai.GenerationConfig(temperature=0.25)
    st.session_state['model'] = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_behavior, generation_config=generation_config)

# ###Below are example Q&A pairs. Use them only to understand the format of the answers. Do not use their content for answering new questions###
#         Assume A is user, and B is Guest
#         **A's Experience Summary**: 
#         - Experienced in Product Management within the tech industry, focused on artificial intelligence.
#         - A is currently studying engineering management at ABC University.
#         - A has 2 years of experience in product management at a startup.

#         **B's Experience Summary**: 
#         - B is a diretor of product management at XYZ company. 
#         - B has over 20 years of experience. 
#         - He has been in one company for 20 years and he recently started a new role as a director of product management. 
#         - He is a big proponent of the product-led growth and he is a big advocate of the same. 
        

#         **Generated Questions**:
#         1. "first off, you’ve been in just 1 company all your life. And this is your 2nd company. That’s quite a commitment. Tell me your secret, because for us generation i can rarely find it and it’s impossible. "
#         2. "I was doing some research and I saw that XYZ company declared a whopping profit of 200M just this quarter. And I see grid intelligence and smart meter being highlighted. can you talk more about that?"
#         2. "I’m completely new to energy management space, but something about I believe is that I have to bring innovation into unconventional domains and that’s where the real success is. I’m an AI software product guy, have you thought incorporating AI into your platforms. There’s analytics, but what about AI. "
#         3. "If my understanding is correct, XYZ company’s main customers are the government and big utility companies. But ultimately the end users are common people or the company’s employees, are there any end user facing applications that XYZ company is working on? Building for customers vs End users?"
#         4. "What according to you is happiness and how do you define it?"
#         5. "Finally, what is one thing that you would advise for someone who is looking out for a job in this tough market?"

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
    logger.debug("get_llm_response() called")  # Add this debug log
    model = st.session_state['model']
    messages = st.session_state['messages']
    user_text = st.session_state['user_text']
    guest_text = st.session_state['guest_text']
    # logger.debug(messages)
    if not st.session_state['first_interaction']:
        final_prompt = messages
    else:
        final_prompt = f"""User profile: {user_text}\n Guest Profile: {guest_text}\n\n Generate 6 thoughtful questions, 
            - 2 personal question by find common ground. 
            - 2 career related question: Ask questions about the guest's company. 
            - 1 phiosophical open ended question about life.
            - 1 career advice question.
            Use simple english.
            If the user asks about something that is not related to the guest's profile, kindly ask them to ask something relevant.
            """
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
            
            if st.button("Re-upload profile", disabled=not st.session_state.preload_pdf):
                st.session_state.preload_pdf = False
                st.rerun()
        
        if not st.session_state.preload_pdf:
            st.subheader("Upload your profile")
            user_pdf = st.file_uploader("", type="pdf", key="main_pdf")
            user_pdf_uploaded = True
            # if user_pdf is not None:
            #     user_pdf_content = parse_pdf(uploaded_file)

        # New file uploader for guest PDF
        st.subheader("Upload guest's profile")
        guest_pdf = st.file_uploader("", type="pdf", key="guest_pdf")
        # if guest_pdf is not None:
        #     guest_pdf_content = parse_pdf(guest_pdf)
        

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
                db_funcs.save_user_if_not_exists(cursor, db, st.session_state['user_info']['email'], st.session_state.get('user_text', ''))
                st.rerun()
            else:
                st.error("Error: Please upload both your LinkedIn profile PDF and the guest's LinkedIn profile PDF.")

        # Add this at the end of the sidebar
        st.markdown("---")  # Horizontal line for visual separation
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
    
    # Add the refresh warning
    add_refresh_warning()
    
    # TO CHECK IF THE USER HAS LOGGED IN
    login_status_container = st.container()
    db, cursor = db_funcs.initialize_database()

    if 'user_info' not in st.session_state:
        st.session_state['credentials'] = None
        st.session_state['user_info'] = None
        st.session_state['variables_initialised'] = False
        st.session_state['model'] = None
        st.session_state['user_text'] = None
        st.session_state['guest_text'] = None
        st.session_state['messages'] = []
        st.session_state['display_messages'] = []
        st.session_state['first_interaction'] = True

    
    
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
        if st.session_state.get('pdfs_submitted', False) and not st.session_state.get('initial_response_generated', False):
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
    
    








