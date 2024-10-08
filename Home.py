import google.generativeai as genai
import os
import streamlit as st
import fitz
from logzero import logger
import google.auth.transport.requests
import google.oauth2.id_token
from google_auth_oauthlib.flow import Flow

import utils

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
    st.write(f"[Login with Google]({authorization_url})")

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

        ###Few-Shot Example###

        **User's Experience Summary**: 
        - Experienced in Product Management within the tech industry, focused on artificial intelligence.
        - The User is currently studying engineering management at Duke University.
        - The user has 2 years of experience in product management at a startup.

        **Guest's Experience Summary**: 
        - The guest is a diretor of product management at Itron. 
        - The guest has over 20 years of experience. 
        - He has been in one company for 20 years and he recently started a new role as a director of product management. 
        - He is a big proponent of the product-led growth and he is a big advocate of the same. 
        

        **Generated Questions**:
        1. "first off, you’ve been in just 1 company all your life. And this is your 2nd company. That’s quite a commitment. Tell me your secret, because for us generation i can rarely find it and it’s impossible. "
        2. "I was doing some research and I saw that Itron declared a whopping profit of 200M just this quarter. And I see grid intelligence and smart meter being highlighted. can you talk more about that?"
        2. "I’m completely new to energy management space, but something about I believe is that I have to bring innovation into unconventional domains and that’s where the real success is. I’m an AI software product guy, have you thought incorporating AI into your platforms. There’s analytics, but what about AI. "
        3. "If my understanding is correct, Itron’s main customers are the government and big utility companies. But ultimately the end users are common people or the company’s employees, are there any end user facing applications that Itron is working on? Building for customers vs End users?"
        4. "What according to you is happiness and how do you define it?"
        5. "Finally, what is one thing that you would advise for someone who is looking out for a job in this tough market?"
        """
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

def get_llm_response(user_text, guest_text):
    """Send the parsed text to the Gemini model and return generated questions."""
    model = st.session_state['model']
    if model:
        prompt = f"""User profile: {user_text}\n Guest Profile: {guest_text}\n\n Generate 6 thoughtful questions, 
            - 2 personal question by find common ground. 
            - 2 career related question: Ask questions about the guest's company. 
            - 1 phiosophical open ended question about life.
            - 1 career advice question.
            Use simple english"""
        response = model.generate_content(prompt)
        return response.text
    return None

if __name__ =="__main__":
    # st.set_page_config(page_title='LinkedinAssistant', page_icon='', initial_sidebar_state='expanded', layout='wide')
    # st.write("HElloo")
    login_status_container = st.container()
    
    if 'user_info' not in st.session_state:
        st.session_state['credentials'] = None
        st.session_state['user_info'] = None
        st.session_state['variables_initialised'] = False
        st.session_state['model'] = None

    if st.session_state['user_info']:
        if not st.session_state['variables_initialised']:
            utils.initialize_variables()
            llm_setup()
        
        with login_status_container:
            st.success(f"Welcome {st.session_state['user_info']['email']}. Setup is ready!")
        st.toast("Setup Ready! You can now use the tool :)")
        logger.info(f"Welcome {st.session_state['user_info']['email']} ")

        user_pdf = st.file_uploader("Upload user pdf here", type=".pdf")
        guest_pdf = st.file_uploader("Upload guest pdf here", type=".pdf")

        if st.button("Submit", type="primary"):
            if user_pdf and guest_pdf:
                user_text = parse_pdf(user_pdf)
                guest_text = parse_pdf(guest_pdf)
                response = get_llm_response(user_text, guest_text)
                if response:
                    st.write("Generated Questions:")
                    st.write(response)
                else:
                    st.write("No response from the LLM.")
    else:
        user_info = process_auth_callback()
        if user_info:
            st.session_state['user_info'] = user_info
            # st.info(f"You've logged in as {user_info['email']}")
            st.rerun()
        else:
            with login_status_container:
                st.warning(body="You're not logged in, please login to use the assistant")
                google_oauth()

    st.markdown("""
    ---
    **Need help? Contact support at [santoshramakrishnan24@gmail.com](mailto:santoshramakrishnan24@gmail.com) \
    Reach out to me on [Twitter](https://x.com/SantoshKutti24)**
    """)