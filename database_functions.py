import streamlit as st
import psycopg2
import json
from logzero import logger
import datetime

def initialize_database():
    database_url = st.secrets["database_url"]
    connection = psycopg2.connect(database_url)
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS linkedin_users (
        email TEXT PRIMARY KEY,
        user_pdf TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS linkedin_chat_messages (
        id SERIAL PRIMARY KEY,
        email TEXT,
        role TEXT,
        parts TEXT,
        timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(email) REFERENCES linkedin_users(email)
    )
    ''')
    connection.commit()
    return connection, cursor

def save_user_if_not_exists(cursor, connection, email: str, user_pdf: str):
    cursor.execute('INSERT INTO linkedin_users (email, user_pdf) VALUES (%s, %s) ON CONFLICT (email) DO NOTHING', (email, user_pdf))
    connection.commit()

def save_chat_message(cursor, connection, email: str, role: str, content: str):
    parts = json.dumps([content])
    cursor.execute('INSERT INTO linkedin_chat_messages (email, role, parts) VALUES (%s, %s, %s)', (email, role, parts))
    connection.commit()

def get_interaction_count(cursor, email, timeframe):
    current_time = datetime.datetime.now(datetime.timezone.utc)
    timeframe_start = current_time - timeframe
    cursor.execute(
        "SELECT COUNT(*) FROM linkedin_chat_messages WHERE email = %s AND timestamp >= %s AND role = 'user'",
        (email, timeframe_start)
    )
    message_count = cursor.fetchone()[0]
    return message_count

def get_user_pdf(cursor, email: str):
    cursor.execute('SELECT user_pdf FROM linkedin_users WHERE email = %s', (email,))
    result = cursor.fetchone()
    return result[0] if result else None