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
st.markdown("Drop a competitor's outlier topic → get 2 direct upgrades + one remix per viral title you paste.")

st.divider()

competitor_topic = st.text_area(
    "Competitor's outlier topic *",
    height=80
)

st.markdown("---")
st.markdown("**Your context**")

viral_titles_input = st.text_area(
    "Your recent viral titles * — paste as many as you want, one per line",
    height=150
)

extra_context = st.text_input(
    "Extra context (optional)"
)

st.markdown("")
generate = st.button("Generate Variations →")

if generate:
    if not competitor_topic or not viral_titles_input:
        st.error("Please fill in the competitor topic and your viral titles.")
    else:
        viral_titles = [t.strip() for t in viral_titles_input.strip().split("\n") if t.strip()]
        num_viral = len(viral_titles)
        viral_titles_formatted = "\n".join([f"{i+1}. {t}" for i, t in enumerate(viral_titles)])
        total = 2 + num_viral

        prompt = f"""You are a YouTube title strategist for a faceless tennis channel. Generate title variations based on a competitor's outlier topic.

Competitor's outlier topic:
"{competitor_topic}"

The channel's recent viral titles (each one has a distinct format/structure):
{viral_titles_formatted}

{f"Extra context: {extra_context}" if extra_context else ""}

Your task is to generate exactly {total} titles total, in two groups:

GROUP A — Direct Upgrades (always exactly 2):
Take the competitor's title and upgrade it directly. Keep the exact same structure, format, emoji style, and topic. Only change the power words — replace weak or generic words with stronger, more emotionally charged, rage-bait alternatives. The upgraded title should feel like a more explosive version of the original.

GROUP B — Format Remixes (exactly {num_viral}, one per viral title):
For each of the {num_viral} viral titles provided, remix the competitor's topic into that viral title's exact format and structure. Each remix must clearly mirror the pattern of its corresponding viral title. Apply the same structure, phrasing style, and dramatic technique from that viral title to the competitor's topic.

Rules:
- Keep the same player name(s) from the competitor's title in all variations
- No spoilers
- No explanations, no group labels, no preamble
- Output only the titles, numbered sequentially from 1 to {total}

Return ONLY the {total} titles, numbered 1 to {total}, one per line."""

        try:
            client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

            with st.spinner("Generating your titles..."):
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
            titles = [l for l in lines if l]

            if titles:
                upgrades = titles[:2]
                remixes = titles[2:2 + num_viral]

                st.markdown("### Direct Upgrades")
                for i, title in enumerate(upgrades, 1):
                    st.markdown(f"""
                    <div class="title-card">
                        <div class="card-num">Upgrade {i:02d}</div>
                        {title}
                    </div>
                    """, unsafe_allow_html=True)
                    st.code(title, language=None)

                st.markdown("### Format Remixes")
                for i, (title, source) in enumerate(zip(remixes, viral_titles), 1):
                    short_source = source[:60] + ('...' if len(source) > 60 else '')
                    st.markdown(f"""
                    <div class="title-card">
                        <div class="card-num">Remix {i:02d} — based on: {short_source}</div>
                        {title}
                    </div>
                    """, unsafe_allow_html=True)
                    st.code(title, language=None)
            else:
                st.error("Couldn't parse titles. Please try again.")

        except Exception as e:
            st.error(f"Something went wrong: {e}")
