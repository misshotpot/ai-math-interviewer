import streamlit as st
from openai import OpenAI
import json
from datetime import datetime
import os

# Page configuration
st.set_page_config(
    page_title="🧮 AI Math Interviewer",
    page_icon="🧮",
    layout="wide"
)

# Read OpenAI API key from Streamlit Secrets
try:
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=openai_api_key)
    api_configured = True
except Exception as e:
    api_configured = False
    st.error("⚠️ API key not configured. Please contact administrator.")
    st.stop()


# ============ Load interview protocol from markdown ============

def load_protocol():
    """Load the detailed interview protocol from interview_protocol.md."""
    try:
        with open("interview_protocol.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # Fallback protocol if file not found
        return """Interview Protocol on Teachers' use of Area Models & Visual Representations

Role: You are a mathematics education researcher specializing in multiplicative reasoning, 
multidigit multiplication, and multidigit division.

Interview Structure:
- Part I: Focus on multidigit multiplication (approximately 5 questions)
- Part II: Focus on multidigit division (approximately 5 questions)

Ask open-ended questions, one at a time, focusing on algorithms, visual representations, 
sequencing, and teacher rationale."""


PROTOCOL_TEXT = load_protocol()


# ============ System prompt for math education researcher ============

SYSTEM_PROMPT = f"""You are an AI mathematics education researcher specializing in multiplicative reasoning,
multidigit multiplication, and multidigit division. Your work is informed by researchers such as
Karl Kosko, Amy Hackenberg, Les Steffe, Erik Tillema, and Karen Zwanch.

Your role is to conduct a qualitative INTERVIEW with an elementary classroom teacher about how they
teach multiplication and division of multidigit whole numbers, with particular attention to area
models and other visual / concrete representations.

CRITICAL INTERACTION RULES:
- You are interviewing, not teaching.
- Ask ONLY ONE question per message.
- Use open-ended, non-leading questions.
- Do NOT suggest specific algorithms, representations, or answers in your questions.
- Focus on:
  • which algorithms they teach for multidigit multiplication/division,
  • when and how they use area models, arrays, grid paper, and concrete manipulatives,
  • how they sequence different methods,
  • how students interact with these representations,
  • the teacher's beliefs, rationales, and examples from their classroom.
- Ask follow-up questions to clarify, get specific examples, and understand sequencing.
- Show cognitive empathy and curiosity; never be judgmental.
- Keep your responses short: 1–3 sentences plus ONE question.

INTERVIEW STRUCTURE:
- Part I: Multidigit multiplication (≈5 questions).
  Start with a friendly greeting and an opening question about how they teach multidigit multiplication.
- Part II: Multidigit division (≈5 questions).
  After multiplication has been discussed, briefly thank them and transition to division.
- When both parts are complete, thank the teacher and end the interview politely.

Below is your detailed interview protocol. Follow it carefully when planning questions and follow-ups:

{PROTOCOL_TEXT}
"""


# ============ Generate interview summary report ============

def generate_interview_report(conversation_history):
    """Generate a concise qualitative interview report about the teacher's practices."""

    conversation_text = "\n\n".join([
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in conversation_history
    ])

    report_prompt = f"""You are a mathematics education researcher writing up an interview.

Based on the following interview transcript with an elementary teacher, write a concise,
professionally worded summary in markdown format.

INTERVIEW TRANSCRIPT:
{conversation_text}

Please create a report with the following structure:

# Teacher Interview Report: Multidigit Multiplication & Division

## Teacher & Classroom Context
- Grade level(s), setting, and any contextual details mentioned
- Curriculum or standards references if noted

## Approaches to Multidigit Multiplication
- Algorithms and strategies the teacher reports using
- How they introduce and sequence different methods
- How concrete and pictorial representations (area models, arrays, manipulatives, etc.) are used
- Any examples or classroom routines they mention

## Approaches to Multidigit Division
- Algorithms and strategies the teacher reports using (e.g., long division, partial quotients, box/area method)
- How they introduce and sequence these approaches
- How concrete and pictorial representations are used
- Any examples or classroom routines they mention

## Beliefs, Rationales, and Student Thinking
- The teacher's stated reasons for using particular algorithms/visuals
- How they describe students' understanding or misconceptions
- Any references to equity, differentiation, or supporting diverse learners

## Open Questions & Possible Follow-Ups
- Aspects that are unclear or not discussed
- Potential questions for a future interview or classroom observation

---
**Report Generated:** {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
**Session ID:** {st.session_state.conversation_id}

If the interview is brief or incomplete, work carefully with what is available and mark missing
information as gaps rather than inventing content."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in qualitative math education research. "
                               "Write clear, analytic, and concise interview summaries."
                },
                {"role": "user", "content": report_prompt},
            ],
            temperature=0.7,
            max_tokens=1500,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating report: {str(e)}"


# ============ Auto-save function ============

def auto_save_transcript():
    """Automatically save transcript to JSON file"""
    try:
        filename = f"interview_{st.session_state.conversation_id}.json"
        save_data = {
            "session_id": st.session_state.conversation_id,
            "timestamp": datetime.now().isoformat(),
            "messages": st.session_state.messages,
            "phase": st.session_state.phase,
            "mult_questions": st.session_state.mult_questions,
            "div_questions": st.session_state.div_questions,
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        return filename
    except Exception as e:
        return None


# ============ Initialize session state ============

if "messages" not in st.session_state:
    st.session_state.messages = []
    welcome = (
        "Hello! I'm glad to have the opportunity to speak with you about how you teach "
        "multiplication and division of whole numbers.\n\n"
        "To begin, thinking specifically about **multidigit multiplication**, "
        "what algorithms, strategies, or visuals do you typically use with your students, "
        "and why do you choose those approaches?"
    )
    st.session_state.messages.append({"role": "assistant", "content": welcome})

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")

# Track interview phases and report
if "phase" not in st.session_state:
    st.session_state.phase = "multiplication"  # 'multiplication', 'division', 'done'
if "mult_questions" not in st.session_state:
    st.session_state.mult_questions = 1  # opening question already asked
if "div_questions" not in st.session_state:
    st.session_state.div_questions = 0
if "report_generated" not in st.session_state:
    st.session_state.report_generated = False
if "current_report" not in st.session_state:
    st.session_state.current_report = None


# ============ Layout: Title & intro ============

st.title("🧮 AI Math Interviewer")
st.markdown("""
**Interviewing Teachers about Multidigit Multiplication & Division**

This AI interviewer helps you conduct structured, qualitative interviews with elementary teachers about:

- how they teach multidigit multiplication and division  
- how they use area models and other visual or concrete representations  
- why they choose particular algorithms and sequences

You can save the chat and generate an interview summary report at any time.
""")

st.markdown("---")


# ============ Sidebar ============

with st.sidebar:
    st.header("📋 Session Information")
    st.caption(f"Session: {st.session_state.conversation_id}")

    st.subheader("📊 Interview Status")
    st.write(f"**Phase:** {st.session_state.phase}")
    st.write(f"**Multiplication questions:** {st.session_state.mult_questions}")
    st.write(f"**Division questions:** {st.session_state.div_questions}")
    st.write(f"**Total messages:** {len(st.session_state.messages)}")

    st.markdown("---")

    # Actions
    st.subheader("⚙️ Actions")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 New Session", use_container_width=True):
            # Auto-save before clearing
            if len(st.session_state.messages) > 2:
                auto_save_transcript()
            st.session_state.clear()
            st.rerun()

    with col2:
        if len(st.session_state.messages) > 2:
            download_data = {
                "session_id": st.session_state.conversation_id,
                "timestamp": datetime.now().isoformat(),
                "messages": st.session_state.messages,
                "phase": st.session_state.phase,
                "mult_questions": st.session_state.mult_questions,
                "div_questions": st.session_state.div_questions,
            }
            st.download_button(
                label="💾 Save Chat",
                data=json.dumps(download_data, indent=2),
                file_name=f"MathInterview_{st.session_state.conversation_id}.json",
                mime="application/json",
                use_container_width=True,
            )

    st.markdown("---")

    # Report generation
    st.subheader("📋 Generate Interview Report")

    if len(st.session_state.messages) < 6:
        remaining = 6 - len(st.session_state.messages)
        st.info(f"💬 Continue the interview ({remaining} more message(s) before report).")
    else:
        st.success("✅ Ready to generate report")

        if st.button("📝 Generate Report", type="primary", use_container_width=True):
            with st.spinner("Generating interview report..."):
                report = generate_interview_report(st.session_state.messages)
                st.session_state.current_report = report
                st.session_state.report_generated = True
                st.success("✅ Report generated!")
                st.rerun()

        if st.session_state.report_generated and st.session_state.current_report:
            st.download_button(
                label="📥 Download Report (MD)",
                data=st.session_state.current_report,
                file_name=f"MathInterview_Report_{st.session_state.conversation_id}.md",
                mime="text/markdown",
                use_container_width=True,
            )
            st.download_button(
                label="📄 Download Report (TXT)",
                data=st.session_state.current_report,
                file_name=f"MathInterview_Report_{st.session_state.conversation_id}.txt",
                mime="text/plain",
                use_container_width=True,
            )

    st.markdown("---")

    with st.expander("ℹ️ How to Use"):
        st.markdown("""
        **Suggested use:**
        1. Introduce the teacher and context.
        2. Explore their approaches to multidigit multiplication (Part I).
        3. After several questions, transition to multidigit division (Part II).
        4. Generate a summary report for documentation or analysis.

        The AI will:
        - ask one open-ended question at a time  
        - focus on algorithms, visuals, and reasoning  
        - keep the conversation on multiplication and division
        
        **Auto-save:** Conversations are automatically saved every 4 messages.
        """)


# ============ Main conversation area ============

st.subheader("💬 Interview Conversation")

# Show history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input
if prompt := st.chat_input("Reply as the teacher...", key="chat_input"):
    # Show user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Auto-save every 4 messages
    if len(st.session_state.messages) % 4 == 0:
        auto_save_transcript()

    # Decide if we should insert a fixed transition to division
    insert_transition = False
    if st.session_state.phase == "multiplication":
        if st.session_state.mult_questions >= 5 and st.session_state.div_questions == 0:
            insert_transition = True

    # Generate assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # If it's time to transition to division, use a fixed prompt
            if insert_transition:
                transition = (
                    "Thank you for sharing how you teach multidigit multiplication.\n\n"
                    "Now let's talk about **division**. Thinking about multidigit division "
                    "(for example long division, partial quotients, or box/area methods), "
                    "what algorithms, strategies, or visuals do you usually use with your students, "
                    "and why do you choose those approaches?"
                )
                response_text = transition
                st.session_state.phase = "division"
                st.session_state.div_questions = 1
            else:
                # Build messages for the model
                messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                for msg in st.session_state.messages[-20:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})

                # Call OpenAI with streaming
                try:
                    stream = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        stream=True,
                        temperature=0.7,
                        max_tokens=800,
                    )
                    response_text = st.write_stream(stream)
                except Exception as e:
                    response_text = f"❌ Error: {str(e)}\n\nPlease contact administrator."
                    st.error(response_text)

            st.session_state.messages.append({"role": "assistant", "content": response_text})

            # Update counters
            if st.session_state.phase == "multiplication" and not insert_transition:
                st.session_state.mult_questions += 1
            elif st.session_state.phase == "division" and not insert_transition:
                st.session_state.div_questions += 1

    st.rerun()

# Show report section if generated
if st.session_state.report_generated and st.session_state.current_report:
    st.markdown("---")
    st.subheader("📊 Generated Interview Report")

    with st.expander("📄 View Report", expanded=True):
        st.markdown(st.session_state.current_report)

# Footer
st.markdown("---")
st.caption("🧮 AI Math Interviewer | Qualitative interviews on multidigit multiplication & division")
st.caption("💡 Designed for research by Dr. Karl Kosko | Developed by James Pellegrino (AI Firefighter Course)")

