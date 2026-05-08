import streamlit as st
import boto3
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize the AWS Bedrock Agent Client
client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

# Hardcode your Agent IDs here (Paste the ones you copied)
AGENT_ID = "YSCY4IMQWK"
AGENT_ALIAS_ID = "NSHBISC3ZK"

# 1. Create a unique session ID for the user's chat history
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# 2. THE FIX: Initialize the messages list so Streamlit doesn't crash
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("Allianz HealthGuard Assistant")

# 3. Draw existing messages to the screen on every reload
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Handle new user input
if prompt := st.chat_input("Ask a policy question..."):
    
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Analyzing policy..."):
        try:
            # Send the text to your Bedrock Agent in the cloud
            response = client.invoke_agent(
                agentId=AGENT_ID,
                agentAliasId=AGENT_ALIAS_ID,
                sessionId=st.session_state.session_id,
                inputText=prompt
            )
            
            # Parse the stream of data AWS sends back
            completion = ""
            for event in response.get('completion'):
                chunk = event.get('chunk')
                if chunk:
                    completion += chunk.get('bytes').decode()
            
            # Display the AI response
            st.chat_message("assistant").markdown(completion)
            st.session_state.messages.append({"role": "assistant", "content": completion})
            
        except Exception as e:
            st.error(f"AWS Bedrock Error: {e}")