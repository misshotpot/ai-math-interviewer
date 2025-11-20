import streamlit as st
from openai import OpenAI
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="🧮 AI Math Interviewer",
    page_icon="🧮",
    layout="wide"
)

# Initialize OpenAI client
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("⚠️ Please add OPENAI_API_KEY to your Streamlit secrets.")
    st.stop()


# ============ System prompt ============

SYSTEM_PROMPT = """You are an AI mathematics education researcher specializing in multiplicative reasoning,
multidigit multiplication, and multidigit division. Your work is informed by researchers such as
Karl Kosko, Amy Hackenberg, Les Steffe, Erik Tillema, and Karen Zwanch.

Your role is to conduct a qualitative INTERVIEW with an elementary classroom teacher about how they
teach multiplication and division of multidigit whole numbers, with attention to area models and
other visual/concrete representations.

CRITICAL RULES:
- Ask ONLY ONE question per message
- Use open-ended, non-leading questions
- Do NOT suggest specific algorithms or answers
- Keep responses short: 1–3 sentences plus ONE question
- Show cognitive empathy and curiosity
- Focus on: algorithms, visual representations (concrete manipulatives, pictorial), sequencing, and teacher beliefs
- Ask follow-up questions for clarity and depth
- Encourage specific classroom examples

INTERVIEW CONTEXT:
You are currently in the middle of the interview. The introduction has already been completed.
Continue asking thoughtful follow-up questions based on what the teacher shares.

Part I focuses on: Multidigit multiplication
Part II focuses on: Multidigit division

Remember: Be non-directive, non-leading, and genuinely curious about their teaching practices.
"""


# ============ Generate report ============

def generate_report(messages):
    """Generate interview summary report."""
    
    transcript = "\n\n".join([
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in messages
    ])

    prompt = f"""You are a mathematics education researcher writing an interview summary.

Based on this interview transcript, write a concise summary in markdown format.

TRANSCRIPT:
{transcript}

Create a report with these sections:

# Teacher Interview Report: Multidigit Multiplication & Division

## Teacher & Classroom Context
## Approaches to Multidigit Multiplication
## Approaches to Multidigit Division
## Beliefs, Rationales, and Student Thinking
## Open Questions & Possible Follow-Ups

---
**Report Generated:** {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
**Session ID:** {st.session_state.conversation_id}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert in qualitative math education research."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating report: {str(e)}"


# ============ Auto-save ============

def auto_save():
    """Auto-save transcript to JSON."""
    try:
        filename = f"interview_{st.session_state.conversation_id}.json"
        data = {
            "session_id": st.session_state.conversation_id,
            "timestamp": datetime.now().isoformat(),
            "messages": st.session_state.messages,
            "interview_stage": st.session_state.get("interview_stage", "introduction"),
            "mult_questions": st.session_state.mult_questions,
            "div_questions": st.session_state.div_questions
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return filename
    except:
        return None


# ============ Initialize session state ============

if "messages" not in st.session_state:
    st.session_state.messages = []
    welcome = (
        "Hello! Thank you for participating in this interview.\n\n"
        "Before we begin, could you please tell me a bit about yourself? "
        "What is your name, what grade level do you teach, and which school or district are you from?"
    )
    st.session_state.messages.append({"role": "assistant", "content": welcome})

if "interview_stage" not in st.session_state:
    st.session_state.interview_stage = "introduction"  # 'introduction', 'self_intro', 'multiplication', 'division', 'done'

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")

if "mult_questions" not in st.session_state:
    st.session_state.mult_questions = 0  # Start at 0 since first question comes after intro

if "div_questions" not in st.session_state:
    st.session_state.div_questions = 0

if "report_generated" not in st.session_state:
    st.session_state.report_generated = False

if "current_report" not in st.session_state:
    st.session_state.current_report = None


# ============ UI Layout ============

st.title("🧮 AI Math Interviewer")
st.markdown("""
**Interviewing Teachers about Multidigit Multiplication & Division**

This AI interviewer conducts structured, qualitative interviews with elementary teachers about:
- How they teach multidigit multiplication and division
- How they use area models and other visual or concrete representations
- Why they choose particular algorithms and sequences
""")

st.markdown("---")


# ============ Sidebar ============

with st.sidebar:
    st.header("📋 Session Information")
    st.caption(f"Session: {st.session_state.conversation_id}")

    st.subheader("📊 Interview Status")
    stage_display = {
        "introduction": "Introduction - Participant Info",
        "ready_to_start": "Ready to Begin",
        "multiplication": "Part I - Multiplication",
        "division": "Part II - Division"
    }
    current_stage = st.session_state.get("interview_stage", "introduction")
    st.write(f"**Stage:** {stage_display.get(current_stage, current_stage)}")
    st.write(f"**Multiplication questions:** {st.session_state.mult_questions}")
    st.write(f"**Division questions:** {st.session_state.div_questions}")
    st.write(f"**Total messages:** {len(st.session_state.messages)}")

    st.markdown("---")

    # Actions
    st.subheader("⚙️ Actions")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 New Session", use_container_width=True):
            if len(st.session_state.messages) > 2:
                auto_save()
            st.session_state.clear()
            st.rerun()

    with col2:
        if len(st.session_state.messages) > 2:
            download_data = {
                "session_id": st.session_state.conversation_id,
                "timestamp": datetime.now().isoformat(),
                "messages": st.session_state.messages,
                "interview_stage": st.session_state.get("interview_stage", "introduction"),
                "mult_questions": st.session_state.mult_questions,
                "div_questions": st.session_state.div_questions
            }
            st.download_button(
                label="💾 Save Chat",
                data=json.dumps(download_data, indent=2),
                file_name=f"MathInterview_{st.session_state.conversation_id}.json",
                mime="application/json",
                use_container_width=True
            )

    st.markdown("---")

    # Report generation
    st.subheader("📋 Generate Report")

    if len(st.session_state.messages) < 6:
        remaining = 6 - len(st.session_state.messages)
        st.info(f"💬 Continue interview ({remaining} more messages).")
    else:
        st.success("✅ Ready to generate report")

        if st.button("📝 Generate Report", type="primary", use_container_width=True):
            with st.spinner("Generating report..."):
                report = generate_report(st.session_state.messages)
                st.session_state.current_report = report
                st.session_state.report_generated = True
                st.success("✅ Report generated!")
                st.rerun()

        if st.session_state.report_generated and st.session_state.current_report:
            st.download_button(
                label="📥 Download Report (MD)",
                data=st.session_state.current_report,
                file_name=f"Report_{st.session_state.conversation_id}.md",
                mime="text/markdown",
                use_container_width=True
            )

    st.markdown("---")

    with st.expander("ℹ️ How to Use"):
        st.markdown("""
        **Steps:**
        1. Explore multiplication teaching (Part I)
        2. Transition to division teaching (Part II)
        3. Generate summary report
        
        **Features:**
        - One question at a time
        - Auto-saves every 4 messages
        - Download chat as JSON
        - Generate research report
        """)


# ============ Main conversation ============

st.subheader("💬 Interview Conversation")

# Display message history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input
if prompt := st.chat_input("Reply as the teacher...", key="chat_input"):
    # Add user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Auto-save every 4 messages
    if len(st.session_state.messages) % 4 == 0:
        auto_save()

    # Check if should transition to division
    insert_transition = False
    if st.session_state.get("interview_stage") == "multiplication":
        if st.session_state.mult_questions >= 5 and st.session_state.div_questions == 0:
            insert_transition = True

    # Generate AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Handle different interview stages
            if st.session_state.interview_stage == "introduction":
                # After participant introduces themselves, AI introduces itself
                response_text = (
                    "Thank you for sharing that information! It's wonderful to meet you.\n\n"
                    "Let me introduce myself: I'm an AI research interviewer specializing in mathematics education, "
                    "particularly in how teachers approach multidigit multiplication and division. "
                    "My research is informed by the work of scholars like Karl Kosko, Amy Hackenberg, and Les Steffe.\n\n"
                    "Today, I'd like to learn about your teaching practices - specifically how you teach multidigit "
                    "multiplication and division, what algorithms and visual representations you use, and why you make "
                    "the instructional choices you do. This interview has two parts: first we'll discuss multiplication, "
                    "then division.\n\n"
                    "There are no right or wrong answers - I'm simply interested in understanding your approach and perspective. "
                    "Shall we begin?"
                )
                st.session_state.interview_stage = "ready_to_start"
            
            elif st.session_state.interview_stage == "ready_to_start":
                # Start with the first multiplication question
                response_text = (
                    "Wonderful! Let's begin with multiplication.\n\n"
                    "Thinking specifically about **multidigit multiplication**, "
                    "what algorithms, strategies, or visuals do you typically use with your students, "
                    "and why do you choose those approaches?"
                )
                st.session_state.interview_stage = "multiplication"
                st.session_state.phase = "multiplication"
                st.session_state.mult_questions = 1
            
            elif insert_transition:
                # Fixed transition message to division
                response_text = (
                    "Thank you for sharing how you teach multidigit multiplication.\n\n"
                    "Now let's talk about **division**. Thinking about multidigit division "
                    "(for example long division, partial quotients, or box/area methods), "
                    "what algorithms, strategies, or visuals do you usually use with your students, "
                    "and why do you choose those approaches?"
                )
                st.session_state.phase = "division"
                st.session_state.interview_stage = "division"
                st.session_state.div_questions = 1
            
            else:
                # Normal interview flow - call API
                api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                for msg in st.session_state.messages[-20:]:
                    api_messages.append({"role": msg["role"], "content": msg["content"]})

                # Call OpenAI API with streaming
                try:
                    stream = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=api_messages,
                        stream=True,
                        temperature=0.7,
                        max_tokens=800
                    )
                    response_text = st.write_stream(stream)
                except Exception as e:
                    response_text = f"❌ Error: {str(e)}"
                    st.error(response_text)

            # Save assistant response
            st.session_state.messages.append({"role": "assistant", "content": response_text})

            # Update counters (only during actual interview, not introduction)
            if st.session_state.interview_stage == "multiplication" and not insert_transition:
                st.session_state.mult_questions += 1
            elif st.session_state.interview_stage == "division" and not insert_transition:
                st.session_state.div_questions += 1

    st.rerun()


# Show report if generated
if st.session_state.report_generated and st.session_state.current_report:
    st.markdown("---")
    st.subheader("📊 Generated Interview Report")
    with st.expander("📄 View Report", expanded=True):
        st.markdown(st.session_state.current_report)


# Footer
st.markdown("---")
st.caption("🧮 AI Math Interviewer | Research by Dr. Karl Kosko | Developed by James Pellegrino")
