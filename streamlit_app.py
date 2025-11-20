import streamlit as st
import openai
import os

# Load API Key
openai.api_key = os.getenv("OPENAI_API_KEY")


def load_protocol():
    """Read the interview protocol from markdown file."""
    try:
        with open("interview_protocol.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Interview protocol file not found."


def build_system_message():
    base_prompt = """
You are an AI mathematics education researcher specializing in multiplicative reasoning 
and in studying how teachers teach multidigit multiplication and multidigit division.

Your job is to interview an elementary teacher.

You must:
- Ask ONLY ONE question per message.
- Ask open-ended, non-leading questions.
- Never teach or solve math problems.
- Focus on how the teacher teaches: algorithms, visuals, manipulatives, sequences of instruction,
  concrete classroom examples, and their reasons and beliefs.
- Show cognitive empathy and curiosity.
- Keep responses short: 1–3 sentences plus a single question.

The interview has 2 parts:
1. Part I — multidigit multiplication (about 5 questions).
2. Part II — multidigit division (about 5 questions).

Start with a friendly greeting and an opening question about multidigit multiplication.
Only after multiplication is discussed in depth, transition to division.
After both parts, thank the teacher and end the interview politely.

Below is your full research interview protocol. Follow it carefully:
"""
    full_prompt = base_prompt + "\n\n" + load_protocol()
    return {"role": "system", "content": full_prompt}


def ask_llm(messages):
    """Call OpenAI ChatCompletion API and return assistant reply."""
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # or another model you have access to
        messages=messages,
        temperature=0.7,
        max_tokens=300,
    )
    return response["choices"][0]["message"]["content"]


def init_session():
    """Initialize chat history and interview state."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append(build_system_message())

        # First interview question (Part I opening)
        opening = (
            "Hello! I’m glad to speak with you about how you teach multiplication and division "
            "of whole numbers.\n\n"
            "Let’s begin with multiplication. Thinking about multidigit multiplication, "
            "what algorithms, strategies, or visuals do you usually use with your students, "
            "and why do you choose those approaches?"
        )
        st.session_state.messages.append({"role": "assistant", "content": opening})

    if "phase" not in st.session_state:
        st.session_state.phase = "multiplication"  # 'multiplication', 'division', 'done'
    if "mult_q" not in st.session_state:
        st.session_state.mult_q = 0
    if "div_q" not in st.session_state:
        st.session_state.div_q = 0


def main():
    st.title("🧮 AI Math Interviewer")
    st.write(
        "This app conducts a qualitative interview with an elementary teacher about "
        "teaching multidigit multiplication and division, with attention to area models "
        "and visual representations."
    )

    init_session()

    # Sidebar status (optional, like crr-bot)
    with st.sidebar:
        st.markdown("### Interview status")
        st.write(f"Phase: {st.session_state.phase}")
        st.write(f"Multiplication questions: {st.session_state.mult_q}")
        st.write(f"Division questions: {st.session_state.div_q}")
        if st.button("🔄 Restart interview"):
            for key in ["messages", "phase", "mult_q", "div_q"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.experimental_rerun()

    # Show history (skip system message)
    for msg in st.session_state.messages:
        if msg["role"] == "system":
            continue
        with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
            st.markdown(msg["content"])

    # Input from teacher
    if st.session_state.phase != "done":
        user_text = st.chat_input("Please answer as the teacher here...")
    else:
        user_text = None

    if user_text:
        # Add teacher message
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        # Phase logic
        if st.session_state.phase == "multiplication":
            st.session_state.mult_q += 1
            if st.session_state.mult_q >= 5 and st.session_state.div_q == 0:
                # Transition to division with fixed text
                transition = (
                    "Thank you for sharing how you teach multidigit multiplication.\n\n"
                    "Now let’s talk about division. Thinking about multidigit division, "
                    "what algorithms, strategies, or visuals do you use with your students, "
                    "and why do you use them?"
                )
                st.session_state.messages.append(
                    {"role": "assistant", "content": transition}
                )
                st.session_state.phase = "division"
                with st.chat_message("assistant"):
                    st.markdown(transition)
                return

        elif st.session_state.phase == "division":
            st.session_state.div_q += 1
            if st.session_state.div_q >= 5:
                closing = "Thank you very much for your answers! This concludes our interview."
                st.session_state.messages.append(
                    {"role": "assistant", "content": closing}
                )
                st.session_state.phase = "done"
                with st.chat_message("assistant"):
                    st.markdown(closing)
                return

        # Ask next question from the model
        reply = ask_llm(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)


if __name__ == "__main__":
    main()
