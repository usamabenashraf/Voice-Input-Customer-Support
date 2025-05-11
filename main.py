# ---------- main.py ----------
import streamlit as st
from audio_recorder_streamlit import audio_recorder
import whisper
from agents import CoordinatorAgent, OrderTrackingAgent, ReturnsAgent
from database import init_db
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, message="Tried to instantiate class")

init_db()

def main():
    st.title("Voice-Enabled Customer Service")
    
        # Initialize session state
    if 'conversation' not in st.session_state:
        st.session_state.conversation = []
    if 'current_order_id' not in st.session_state:
        st.session_state.current_order_id = None

    # Audio recording
    st.markdown("---")
    st.subheader("🎙️ Speak your query below")
    audio_bytes = audio_recorder(pause_threshold=2.0)
    
    if audio_bytes:
        # Transcribe audio
        with open("input.wav", "wb") as f:
            f.write(audio_bytes)
            
        model = whisper.load_model("base")
        result = model.transcribe("input.wav")
        user_input = result["text"]
        
        # Initialize agents
        order_agent = OrderTrackingAgent()
        return_agent = ReturnsAgent()
        coordinator = CoordinatorAgent(order_agent, return_agent)


        # Get agent type and process
        agent_type = coordinator.route(user_input, "GeneralAgent")
        if agent_type['agent'] in ["OrdersAgent", "ReturnsAgent"]:  # Handle specialized agents
            if agent_type['agent'] == "OrdersAgent":
                selected_agent = order_agent
                agent_response = selected_agent.process( query=user_input,
                    current_order_id=coordinator.extract_order_id(user_input)
                )
            else:
                selected_agent = return_agent
                extracted_order_id = coordinator.extract_order_id(user_input)
                agent_response = selected_agent.process(query=user_input, order_id=extracted_order_id)
        else:  # Handle general responses
            agent_response = {
                "response": "I can only help with orders and returns. How can I assist you?",
                "order_id": None
            }
        # Update conversation history
        st.session_state.conversation.extend([
            ("user", user_input),
            ("system", f"Routing decision: {agent_type['reasoning']}"),
            ("Customer Service" if agent_type == "GeneralAgent" else agent_type['agent'], agent_response["response"])
        ])
    # Display formatted conversation first
    for speaker, message in st.session_state.conversation:
        if speaker == "user":
            st.markdown(f"👤 **User:** {message}")
        elif speaker == "system":
            st.caption(f"⚙️ {message}")
        else:
            st.markdown(f"🤖 **{speaker}:** {message}")

if __name__ == "__main__":
    main()
