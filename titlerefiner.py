import streamlit as st
import anthropic

st.set_page_config(page_title="Title Machine", page_icon="⚡", layout="centered")

st.markdown("""
<style>
    .block-container { max-width: 720px; padding-top: 2rem; }
    .title-card {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 10px;
        font-size: 15px;
        line-height: 1.5;
    }
    .card-num {
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.08em;
        color: #999;
        margin-bottom: 6px;
        text-transform: uppercase;
    }
    .stButton button {
        width: 100%;
        background-color: #e8ff47;
        color: #0a0a0a;
        font-weight: 700;
        font-size: 16px;
        border: none;
        padding: 12px;
        border-radius: 8px;
    }
    .stButton button:hover { background-color: #f0ff60; }
</style>
""", unsafe_allow_html=True)

st.markdown("## ⚡ Title Machine")
st.markdown("Drop a competitor's outlier topic → get 4 variations tuned to your channel's style.")

st.divider()

competitor_topic = st.text_area(
    "Competitor's outlier topic *",
    placeholder='e.g. "Alex Eala KICKED OUT of tournament after shocking incident"',
    height=80
)

st.markdown("---")
st.markdown("**Your context**")

viral_titles = st.text_area(
    "Your recent viral titles * — paste 3–5, one per line",
    placeholder="Alex Eala SILENCED Everyone With This…\nThey Didn't Expect Alex Eala To Do THIS\nAlex Eala Just Changed Everything",
    height=120
)

format_desc = st.text_area(
    "Describe your current title format *",
    placeholder='e.g. "All-caps trigger word at start, then a cliffhanger. No spoilers. Usually ends with … or a dramatic statement."',
    height=90
)

extra_context = st.text_input(
    "Extra context (optional)",
    placeholder="e.g. faceless channel, Filipino audience, uploads 3x/week"
)

st.markdown("")
generate = st.button("Generate 4 Variations →")

if generate:
    if not competitor_topic or not viral_titles or not format_desc:
        st.error("Please fill in the competitor topic, your viral titles, and current format.")
    else:
        prompt = f"""You are a YouTube title strategist for a faceless tennis channel focused on Alex Eala. Your job is to generate viral title variations.

Here is the competitor's outlier topic/title:
"{competitor_topic}"

Here are the channel's recent viral titles (learn from their format, style, and tone):
{viral_titles}

The creator describes their current title format as:
"{format_desc}"

{f"Extra context about the channel: {extra_context}" if extra_context else ""}

Your task:
1. Analyze the competitor's topic to extract the core hook/angle
2. Generate EXACTLY 4 title variations that:
   - Are unique (not a copy of the competitor)
   - Match the format and tone described above
   - Feel slightly rage-bait or emotionally charged to drive clicks
   - Are tailored for the Alex Eala / tennis audience
   - Vary from each other (don't repeat the same structure 4 times)
3. Each title should feel like it belongs on this specific channel

Return ONLY the 4 titles, numbered 1 to 4, one per line. No explanations, no preamble, no extra text. Just the titles."""

        try:
            client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

            with st.spinner("Cooking your titles..."):
                message = client.messages.create(
                    model="claude-opus-4-6",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}]
                )

            raw = message.content[0].text.strip()
            lines = [
                line.lstrip("1234567890.)- ").strip()
                for line in raw.split("\n")
                if line.strip()
            ]
            titles = [l for l in lines if l][:4]

            if titles:
                st.markdown("### Generated Variations")
                for i, title in enumerate(titles, 1):
                    st.markdown(f"""
                    <div class="title-card">
                        <div class="card-num">Variation {i:02d}</div>
                        {title}
                    </div>
                    """, unsafe_allow_html=True)
                    st.code(title, language=None)
            else:
                st.error("Couldn't parse titles. Please try again.")

        except Exception as e:
            st.error(f"Something went wrong: {e}")
