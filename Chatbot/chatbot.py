import streamlit as st
import hashlib
import sqlite3
from datetime import datetime
from gpt4all import GPT4All

# Initialize GPT4All model
@st.cache_resource
def load_model():
    return GPT4All("orca-mini-3b-gguf2-q4_0.gguf")

model = load_model()

# Initialize session state variables
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Database functions
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users
        (username TEXT PRIMARY KEY, password TEXT)
    ''')
    conn.commit()
    conn.close()

def add_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    try:
        c.execute("INSERT INTO users VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password))
    result = c.fetchone() is not None
    conn.close()
    return result

# GPT4All chatbot response function
def get_bot_response(question):
    try:
        # Generate response
        response = model.generate(question, max_tokens=200)
        return response
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return "I apologize, but I'm having trouble generating a response at the moment. Please try again."

# Initialize database
init_db()

# Main app
def main():
    st.title("Local AI Chatbot (GPT4All)")
    
    # Model loading status
    if 'model_loaded' not in st.session_state:
        st.session_state.model_loaded = False
    
    if not st.session_state.model_loaded:
        with st.spinner("Loading AI model... This may take a minute..."):
            # This will use the cached model
            model = load_model()
            st.session_state.model_loaded = True
    
    if not st.session_state.logged_in:
        # Login/Register interface
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Login")
            login_username = st.text_input("Username", key="login_username")
            login_password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login"):
                if verify_user(login_username, login_password):
                    st.session_state.logged_in = True
                    st.session_state.username = login_username
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        with col2:
            st.subheader("Register")
            reg_username = st.text_input("Username", key="reg_username")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            if st.button("Register"):
                if add_user(reg_username, reg_password):
                    st.success("Registration successful! Please login.")
                else:
                    st.error("Username already exists")
    
    else:
        # Chatbot interface
        st.subheader(f"Welcome, {st.session_state.username}!")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.rerun()
        
        st.subheader("Chat")
        
        # Create a container for chat history
        chat_container = st.container()
        
        # User input at the bottom
        user_input = st.text_input("Ask anything:", key="user_input")
        
        if st.button("Send") and user_input:
            with st.spinner("Thinking... (This may take a few seconds)"):
                bot_response = get_bot_response(user_input)
                st.session_state.chat_history.append({
                    "user": user_input,
                    "bot": bot_response,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
        
        # Display chat history in the container
        with chat_container:
            for chat in reversed(st.session_state.chat_history):
                st.markdown(f"**You** ({chat['timestamp']}):")
                st.markdown(f">{chat['user']}")
                st.markdown(f"**Assistant** ({chat['timestamp']}):")
                st.markdown(f"{chat['bot']}")
                st.markdown("---")

if __name__ == "__main__":
    main()



