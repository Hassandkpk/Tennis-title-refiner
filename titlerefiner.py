import streamlit as st
import anthropic
import requests
from datetime import datetime, timedelta, timezone

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
    .viral-badge {
        background: #e8ff47;
        color: #0a0a0a;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
        margin-bottom: 8px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


def fetch_top_videos_this_week(api_key, channel_id, max_results=5):
    """Fetch top videos published in last 7 days, sorted by view count."""

    published_after = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Step 1: Get uploads playlist ID
    r = requests.get("https://www.googleapis.com/youtube/v3/channels", params={
        "part": "contentDetails",
        "id": channel_id,
        "key": api_key
    })
    r.raise_for_status()
    data = r.json()

    if not data.get("items"):
        raise ValueError("Channel not found. Check your CHANNEL_ID.")

    uploads_playlist = data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # Step 2: Get video IDs published in last 7 days from uploads playlist
    # Playlist is sorted newest-first so we stop as soon as we pass the 7-day window
    video_ids = []
    next_page_token = None

    while True:
        params = {
            "part": "contentDetails,snippet",
            "playlistId": uploads_playlist,
            "maxResults": 50,
            "key": api_key
        }
        if next_page_token:
            params["pageToken"] = next_page_token

        resp = requests.get("https://www.googleapis.com/youtube/v3/playlistItems", params=params)
        resp.raise_for_status()
        page = resp.json()

        stop_early = False
        for item in page.get("items", []):
            published_at = item["snippet"].get("publishedAt", "")
            if published_at >= published_after:
                video_ids.append(item["contentDetails"]["videoId"])
            else:
                stop_early = True
                break

        next_page_token = page.get("nextPageToken")
        if not next_page_token or stop_early:
            break

    if not video_ids:
        raise ValueError("No videos found in the last 7 days for this channel.")

    # Step 3: Get stats for all videos in batches of 50
    videos_data = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        resp = requests.get("https://www.googleapis.com/youtube/v3/videos", params={
            "part": "snippet,statistics",
            "id": ",".join(batch),
            "key": api_key
        })
        resp.raise_for_status()
        videos_data.extend(resp.json().get("items", []))

    # Step 4: Sort by views, return top N
    videos_data.sort(
        key=lambda v: int(v["statistics"].get("viewCount", 0)),
        reverse=True
    )

    return [
        {
            "title": v["snippet"]["title"],
            "views": int(v["statistics"].get("viewCount", 0)),
            "published": v["snippet"]["publishedAt"][:10]
        }
        for v in videos_data[:max_results]
    ]


# ── UI ────────────────────────────────────────────────────────────────────────

st.markdown("## ⚡ Title Machine")
st.markdown("Competitor topic in → top videos from last 7 days auto-loaded → variations out.")

st.divider()

st.markdown("### Select channel")

try:
    channels = dict(st.secrets["CHANNELS"])
    channel_names = list(channels.keys())
except KeyError:
    st.error("No CHANNELS found in secrets. Add them in Streamlit Cloud → Settings → Secrets.")
    st.stop()

col_sel, col_fetch = st.columns([3, 1])
with col_sel:
    selected_channel = st.selectbox("Which channel?", channel_names, label_visibility="collapsed")
with col_fetch:
    fetch_btn = st.button("Load This Week", use_container_width=True)

# Reset state on channel change
if "last_channel" not in st.session_state:
    st.session_state.last_channel = None
if "top_videos" not in st.session_state:
    st.session_state.top_videos = []
    st.session_state.viral_titles_text = ""

if selected_channel != st.session_state.last_channel:
    st.session_state.top_videos = []
    st.session_state.viral_titles_text = ""
    st.session_state.last_channel = selected_channel

st.markdown("### Top videos — last 7 days")

if fetch_btn or not st.session_state.top_videos:
    try:
        yt_api_key = st.secrets["YOUTUBE_API_KEY"]
        channel_id = channels[selected_channel]

        with st.spinner(f"Fetching last 7 days for **{selected_channel}**..."):
            top_videos = fetch_top_videos_this_week(yt_api_key, channel_id, max_results=5)
            st.session_state.top_videos = top_videos
            st.session_state.viral_titles_text = "\n".join([v["title"] for v in top_videos])
            st.session_state.last_channel = selected_channel

    except ValueError as e:
        st.warning(str(e))
    except KeyError as e:
        st.error(f"Missing secret: {e}. Add YOUTUBE_API_KEY and CHANNELS in Streamlit secrets.")
    except Exception as e:
        st.error(f"YouTube API error: {e}")

if st.session_state.top_videos:
    st.success(f"Top {len(st.session_state.top_videos)} videos from the last 7 days — **{selected_channel}**")
    for v in st.session_state.top_videos:
        st.markdown(f"""
        <div class="title-card">
            <div class="viral-badge">👁 {v['views']:,} views &nbsp;·&nbsp; {v['published']}</div><br>
            {v['title']}
        </div>
        """, unsafe_allow_html=True)

st.divider()

st.markdown("### Competitor's outlier topic")
competitor_topic = st.text_area("Paste the competitor's title here *", height=80)
extra_context = st.text_input("Extra context (optional)")

st.markdown("")
generate = st.button("Generate Variations →")

if generate:
    if not competitor_topic:
        st.error("Please paste the competitor's title.")
    elif not st.session_state.viral_titles_text:
        st.error("No videos loaded. Click 'Load This Week' first.")
    else:
        viral_titles = [t.strip() for t in st.session_state.viral_titles_text.strip().split("\n") if t.strip()]
        num_viral = len(viral_titles)
        viral_titles_formatted = "\n".join([f"{i+1}. {t}" for i, t in enumerate(viral_titles)])
        total = 2 + num_viral

        prompt = f"""You are a YouTube title strategist for a faceless tennis channel. Generate title variations based on a competitor's outlier topic.

Competitor's outlier topic:
"{competitor_topic}"

The channel's top viral titles from this week (each has a distinct proven format/structure):
{viral_titles_formatted}

{f"Extra context: {extra_context}" if extra_context else ""}

Generate exactly {total} titles total:

GROUP A — Direct Upgrades (exactly 2):
- Keep the exact same structure, format, emoji style, and topic as the competitor's title
- Replace weak or generic words with stronger, more emotionally charged, rage-bait alternatives
- The result should feel like a more explosive version of the original — same angle, harder language
- Keep the title length same as competitor's title


GROUP B — Format Remixes (exactly {num_viral}, one per viral title):
- For each viral title listed above, extract its unique format and structure
- Apply that exact format and structure to the competitor's topic
- Each remix must clearly mirror its corresponding viral title's pattern and feel like it belongs on this channel
- Keep the length between 80-90 characters 

Rules:
- Keep the same player name(s) from the competitor's title in all variations
- No spoilers
- Output ONLY the titles, one per line, no numbering, no labels, no explanations
- GROUP A first (2 titles), then GROUP B ({num_viral} titles)
- Total: exactly {total} lines"""

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
                st.markdown("### Direct upgrades")
                for i, title in enumerate(titles[:2], 1):
                    st.markdown(f"""
                    <div class="title-card">
                        <div class="card-num">Upgrade {i:02d}</div>
                        {title}
                    </div>
                    """, unsafe_allow_html=True)
                    st.code(title, language=None)

                st.markdown("### Format remixes")
                for i, (title, source) in enumerate(zip(titles[2:], viral_titles), 1):
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
