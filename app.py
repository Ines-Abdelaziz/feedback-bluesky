import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import base64
import time
import json
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Bluesky Moderation Study", page_icon="🔵", layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Styling ────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #f8fafc !important;
    color: #0f172a !important;
}
[class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Mobile responsive ── */
.block-container {
    padding-top: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    background-color: #f8fafc !important;
    max-width: 860px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}
@media (max-width: 768px) {
    .block-container {
        padding-top: 1rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
        max-width: 100% !important;
    }
    /* Bigger touch targets for radio buttons and checkboxes */
    [data-testid="stRadio"] label,
    [data-testid="stCheckbox"] label {
        font-size: 16px !important;
        padding: 10px 0 !important;
        min-height: 44px !important;
        display: flex !important;
        align-items: center !important;
    }
    /* Bigger buttons on mobile */
    [data-testid="stButton"] button {
        font-size: 16px !important;
        min-height: 52px !important;
        padding: 12px 20px !important;
    }
    /* Bigger text areas */
    [data-testid="stTextArea"] textarea {
        font-size: 16px !important;  /* prevents iOS zoom on focus */
        min-height: 100px !important;
    }
    [data-testid="stTextInput"] input {
        font-size: 16px !important;  /* prevents iOS zoom on focus */
        min-height: 44px !important;
    }
    /* Post card full width */
    .post-card {
        padding: 14px 14px !important;
        border-radius: 10px !important;
    }
    .post-text { font-size: 15px !important; }
    /* Full-width images on mobile */
    .blurred-image-wrap { width: 100% !important; }
    .blurred-image-wrap img { width: 100% !important; }
    /* Stack media grid to single column on mobile */
    .media-grid-cols > div { flex: 1 1 100% !important; min-width: 100% !important; }
    /* Hide sidebar toggle */
    [data-testid="collapsedControl"] { display: none !important; }
    /* Multiselect bigger */
    [data-testid="stMultiSelect"] { font-size: 16px !important; }
    /* Category table scrollable */
    .cat-table { display: block; overflow-x: auto; font-size: 12px !important; }
    /* Progress label */
    .progress-label { font-size: 14px !important; }
    /* Badges */
    .media-badge { font-size: 12px !important; padding: 3px 10px !important; }
}

p, li, span, label, h1, h2, h3, h4 { color: #0f172a !important; }
[data-testid="stWidgetLabel"] * { color: #0f172a !important; }
[data-testid="stMarkdownContainer"] * { color: #0f172a !important; }
textarea, input { background-color: #ffffff !important; color: #0f172a !important; }
[data-testid="stTextInput"] input,
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea,
[data-testid="stTextArea"] textarea:focus {
    background-color: #ffffff !important;
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
    color: #94a3b8 !important;
    -webkit-text-fill-color: #94a3b8 !important;
}
[data-testid="stMultiSelect"] > div > div {
    background-color: #ffffff !important;
    border-color: #e2e8f0 !important;
}
[data-testid="stMultiSelect"] input {
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
}
[data-testid="stMultiSelect"] [data-baseweb="select"] span {
    color: #94a3b8 !important;
    -webkit-text-fill-color: #94a3b8 !important;
}
div[data-baseweb="tag"] { background-color: #e2e8f0 !important; }
div[data-baseweb="tag"] span {
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
    background-color: transparent !important;
}
[data-baseweb="popover"], [data-baseweb="popover"] ul,
[data-baseweb="menu"], [data-baseweb="menu"] ul,
[role="listbox"], [role="option"] {
    background-color: #ffffff !important;
    color: #0f172a !important;
}
[role="option"]:hover, [role="option"][aria-selected="true"] {
    background-color: #eff6ff !important;
    color: #1e40af !important;
}
[data-baseweb="popover"] input {
    background-color: #ffffff !important;
    color: #0f172a !important;
}
[data-baseweb="menu"] [role="option"] {
    background-color: #ffffff !important;
    color: #0f172a !important;
}
[data-baseweb="select"] div,
[data-baseweb="select"] span,
[data-baseweb="select"] input {
    background-color: #ffffff !important;
    color: #0f172a !important;
}
[data-testid="stExpander"] {
    background-color: #ffffff !important;
    border-color: #e2e8f0 !important;
}

.post-card {
    background: #ffffff !important;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.post-avatar {
    width: 38px; height: 38px; border-radius: 50%;
    background: linear-gradient(135deg, #0ea5e9, #2563eb);
    display: inline-block; vertical-align: middle; margin-right: 10px;
}
.post-text { font-size: 15px; line-height: 1.65; color: #0f172a !important; }
.progress-label { font-size: 13px; color: #64748b !important; margin-bottom: 6px; }
.media-badge {
    display: inline-block; font-size: 11px; font-weight: 600;
    padding: 2px 8px; border-radius: 20px; margin: 4px 4px 0 0;
    letter-spacing: 0.03em;
}
.badge-image { background: #dbeafe; color: #1e40af; }
.badge-video { background: #dcfce7; color: #15803d; }
.badge-audio { background: #fef9c3; color: #a16207; }

.cat-table { width: 100%; border-collapse: collapse; margin: 12px 0 20px; }
.cat-table th {
    background: #1e40af !important; color: #ffffff !important;
    padding: 10px 14px; text-align: left; font-size: 13px;
}
.cat-table td {
    padding: 10px 14px; border-bottom: 1px solid #e2e8f0;
    font-size: 13px; vertical-align: top; line-height: 1.6;
    color: #0f172a !important; background: #ffffff !important;
}
.cat-table tr:nth-child(even) td { background: #f8fafc !important; }
.cat-label { font-weight: 600; color: #1e293b !important; white-space: nowrap; }

.blurred-image-wrap {
    position: relative; display: flex; justify-content: center;
    margin: 8px 0; cursor: pointer;
}
.blurred-image-wrap img {
    max-width: 100%; border-radius: 10px;
    filter: blur(64px);
    transition: filter 0.3s ease;
    user-select: none;
}
.blurred-image-wrap:hover img { filter: blur(0px); }
.blur-hint {
    position: absolute; top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(0,0,0,0.55); color: #fff;
    padding: 7px 16px; border-radius: 20px;
    font-size: 13px; pointer-events: none;
    transition: opacity 0.3s ease; white-space: nowrap;
}
.blurred-image-wrap:hover .blur-hint { opacity: 0; }
.media-grid { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0; }
.media-grid .blurred-image-wrap { flex: 1 1 calc(50% - 8px); min-width: 140px; }
</style>
""", unsafe_allow_html=True)

# ── Config ─────────────────────────────────────────────────────────────────────

GOOGLE_APPS_SCRIPT_URL = st.secrets["GOOGLE_APPS_SCRIPT_URL"]
GOOGLE_SHEET_READ_URL  = st.secrets.get("GOOGLE_SHEET_READ_URL", "")
HF_TOKEN               = st.secrets.get("HF_TOKEN", "")
HF_JSONL_URL           = st.secrets.get("HF_JSONL_URL", "")
# e.g. https://huggingface.co/datasets/ines-abdelaziz/neurips-content-moderation/resolve/main/data/pilot_1k.jsonl

AUTOSAVE_EVERY = 1

# ── Labels ─────────────────────────────────────────────────────────────────────

LABELS = {
    "S1": ("porn",             "Contain pornographic material, including explicit depictions of sexual acts or genitalia intended to elicit sexual arousal, regardless of artistic, humorous, or educational context."),
    "S2": ("sexual",           "Contain sexually suggestive or provocative content that does not reach the threshold of pornography, including innuendo, partial nudity in a sexual context, or implied sexual acts."),
    "S3": ("sexual-figurative","Contain figurative or symbolic sexual content, such as stylized, cartoon, or abstract representations of sexual themes that may not involve real people or explicit realism but convey sexual meaning or intent."),
    "S4": ("self-harm",        "Promote self-harm, including graphic images, glorifying discussions, or triggering stories."),
    "S5": ("nudity",           "Contain non-sexual nudity, such as depictions of bare bodies or body parts presented without an overt sexual context, including artistic, documentary, or casual exposure."),
    "S6": ("intolerant",       "Contain discrimination against protected groups."),
    "S7": ("graphic-media",    "Contain graphic or gory media, including depictions of violence, injury, death, or bodily harm, whether real or fictional."),
    "S8": ("rude",             "Contain rude or impolite content, including crude language and disrespectful comments, without constructive purpose."),
    "S9": ("threat",           "Promote violence or harm towards others, including threats, incitement, or advocacy of harm."),
}

# ── Session state ──────────────────────────────────────────────────────────────

for k, v in {
    "page":               "intro",
    "annotator_name":     "",
    "posts":              [],
    "current_idx":        0,
    "feedback_data":      [],
    "saved_post_ids":     set(),
    "saved_up_to":        -1,
    "submission_complete":False,
    "post_start_time":    None,
    "resume_checked":     False,
    "_do_autosave":       False,
    "resumed_from":       None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Data loading ───────────────────────────────────────────────────────────────

@st.cache_data
def load_posts_from_hf(url: str, token: str) -> list:
    """Load posts from a HuggingFace JSONL URL."""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        posts = []
        for line in r.text.splitlines():
            line = line.strip()
            if line:
                posts.append(json.loads(line))
        return posts
    except Exception as e:
        st.error(f"Failed to load posts from HuggingFace: {e}")
        return []


def load_posts() -> list:
    if HF_JSONL_URL:
        return load_posts_from_hf(HF_JSONL_URL, HF_TOKEN)
    # Fallback: legacy CSV
    try:
        import pandas as pd
        df = pd.read_csv("data/survey_posts.csv")
        if "display_num" in df.columns:
            df = df.sort_values("display_num").reset_index(drop=True)
        return df.to_dict("records")
    except Exception as e:
        st.error(f"No data source configured. Set HF_JSONL_URL in secrets. ({e})")
        return []


def shuffle_posts_for_annotator(posts, annotator_name):
    import random, hashlib
    seed = int(hashlib.sha256(annotator_name.lower().strip().encode()).hexdigest(), 16) % (2**32)
    rng  = random.Random(seed)
    shuffled = posts.copy()
    rng.shuffle(shuffled)
    return shuffled

# ── Media helpers ──────────────────────────────────────────────────────────────

def fetch_image(url: str, token: str = "") -> Image.Image | None:
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        return Image.open(BytesIO(r.content))
    except Exception:
        return None


def image_to_b64(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def render_blurred_image(b64: str, label: str = "Hover to reveal image"):
    st.markdown(f"""
<div class="blurred-image-wrap">
    <img src="data:image/png;base64,{b64}" alt="post image">
    <div class="blur-hint">{label}</div>
</div>""", unsafe_allow_html=True)


def render_video(url: str, token: str = ""):
    """Fetch video bytes and render inline."""
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        r = requests.get(url, headers=headers, timeout=60, stream=True)
        r.raise_for_status()
        video_bytes = r.content
        st.video(video_bytes)
    except Exception:
        st.caption("⚠️ Video could not be loaded.")


def get_post_media(post: dict) -> dict:
    """
    Normalise media fields from both old CSV format and new JSONL format.
    Returns: {images: [url,...], video: url|None, has_image, has_video}
    """
    # New JSONL format
    images_field = post.get("images") or []
    video_field  = post.get("video")

    image_urls = []
    if isinstance(images_field, list):
        for item in images_field:
            if isinstance(item, dict):
                url = item.get("file") or item.get("url") or ""
            else:
                url = str(item)
            url = url.strip()
            if url and url.lower() not in ("nan", "none", ""):
                image_urls.append(url)
    elif isinstance(images_field, str):
        # Legacy: comma-separated or single URL
        for u in images_field.split(","):
            u = u.strip()
            if u and u.lower() not in ("nan", "none", ""):
                image_urls.append(u)

    video_url = None
    if video_field and str(video_field).strip().lower() not in ("nan", "none", ""):
        video_url = str(video_field).strip()

    # Legacy CSV fallback
    if not image_urls and not video_url:
        legacy_img = str(post.get("image_url", "")).strip()
        if legacy_img and legacy_img.lower() not in ("nan", "none", ""):
            image_urls = [legacy_img]

    return {
        "image_urls": image_urls,
        "video_url":  video_url,
        "has_image":  len(image_urls) > 0,
        "has_video":  video_url is not None,
    }

# ── Google Sheets ──────────────────────────────────────────────────────────────

def append_to_sheet(data: dict, max_retries: int = 3):
    payload = {
        "annotator_name":    data["annotator_name"],
        "post_id":           data["post_id"],
        "display_num":       data["display_num"],
        "label":             data["label"],
        "reason":            data["reason"],
        "time_spent_sec":    data["time_spent_sec"],
        "unsafe_categories": data.get("unsafe_categories", ""),
        "attribution_source":data.get("attribution_source", ""),
    }
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                GOOGLE_APPS_SCRIPT_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            if resp.status_code == 200:
                try:
                    result = resp.json()
                    if result.get("status") == "success":
                        return True, "OK"
                    return False, result.get("message", "Unknown error")
                except json.JSONDecodeError:
                    return (True, "OK") if "success" in resp.text.lower() else (False, resp.text[:200])
            if attempt < max_retries - 1:
                time.sleep(2)
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(3)
        except Exception as e:
            return False, str(e)
    return False, "Max retries exceeded"


def fetch_saved_progress(annotator_name: str) -> list:
    if not GOOGLE_SHEET_READ_URL:
        return []
    try:
        resp = requests.get(GOOGLE_SHEET_READ_URL, params={"annotator": annotator_name}, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("rows", [])
    except Exception:
        pass
    return []


def autosave_pending(force: bool = False):
    feedback  = st.session_state.feedback_data
    saved_ids = st.session_state.get("saved_post_ids", set())
    pending   = [r for r in feedback if r["post_id"] not in saved_ids]

    if not pending:
        return True
    if not force and len(pending) < AUTOSAVE_EVERY:
        return True

    failed = []
    for row in pending:
        ok, _ = append_to_sheet(row)
        if ok:
            saved_ids.add(row["post_id"])
        else:
            failed.append(row["post_id"])

    st.session_state.saved_post_ids = saved_ids
    if failed:
        st.toast(f"⚠️ Autosave failed for {len(failed)} posts. Will retry.", icon="⚠️")
        return False
    st.toast(f"💾 Progress saved ({len(saved_ids)}/3,000 posts)", icon="💾")
    return True

# ── Pages ──────────────────────────────────────────────────────────────────────

def intro_page():
    st.markdown("""
<div style="text-align:center; padding:10px 0 24px;">
    <div style="font-size:2.8em; margin-bottom:10px;">🔵</div>
    <h1 style="color:#1e3a8a; margin:0; font-size:2em; font-weight:700;">Bluesky Content Moderation</h1>
    <p style="color:#64748b; margin:6px 0 0;">Internal Team Labeling Study &nbsp;·&nbsp; Max Planck Institute for Software Systems</p>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### About this study")
    st.markdown("""
You will review **3,000 Bluesky posts** and label each one as **Safe** or **Unsafe**
according to Bluesky's Community Guidelines. For each post you must also provide
a brief written reasoning.

> ⚠️ Some posts may contain offensive language, hate speech, or explicit content.
> Please proceed only if you are comfortable.
    """)

    st.markdown("### Unsafe content categories")
    st.markdown("A post is **Unsafe** if it falls into one or more of the following categories:")
    rows_html = "".join(
        f'<tr><td class="cat-label">{name}</td><td>{desc}</td></tr>'
        for (name, desc) in LABELS.values()
    )
    st.markdown(f"""
<table class="cat-table">
<tr><th style="width:22%">Category</th><th>Mark as <strong>Unsafe</strong> if the post…</th></tr>
{rows_html}
</table>
""", unsafe_allow_html=True)

    st.markdown("""
**Safe** — does not fall into any category above. Includes everyday content, news, humor,
strong language not targeting anyone, fictional violence in art/games, journalism, or labeled parody.
    """)

    st.markdown("---")
    st.markdown("### Your information")

    name = st.text_input("Your name or initials *", placeholder="e.g. Ines A.")
    name = name.strip()
    name_valid = len(name) >= 2

    # Always fetch fresh from sheet — no caching
    saved_rows = []
    if name_valid:
        with st.spinner("Checking for saved progress..."):
            saved_rows = fetch_saved_progress(name)
    resume_available = len(saved_rows) > 0
    resume           = False

    if resume_available:
        completed = len(saved_rows)
        st.info(f"💾 Found saved progress: **{completed}/3,000 posts** already labeled.")
        resume = st.checkbox(f"Resume from post {completed + 1}", value=True)

    st.markdown("---")
    btn_label = "Resume labeling →" if (resume_available and resume) else "Begin labeling →"

    if st.button(btn_label, type="primary", disabled=not name_valid, use_container_width=True):
        posts = shuffle_posts_for_annotator(load_posts(), name)
        st.session_state.annotator_name = name
        st.session_state.posts = posts

        if resume_available and resume:
            st.session_state.feedback_data = [
                {
                    "annotator_name":  name,
                    "post_id":         r.get("post_id", ""),
                    "display_num":     int(r.get("display_num", 0)),
                    "label":           r.get("label", ""),
                    "reason":          r.get("reason", ""),
                    "time_spent_sec":  float(r.get("time_spent_sec", 0)),
                }
                for r in saved_rows
            ]
            done_ids = {r["post_id"] for r in st.session_state.feedback_data}
            st.session_state.saved_post_ids = done_ids
            st.session_state.saved_up_to    = len(done_ids)

            def post_key(p):
                return p.get("post_id") or p.get("uri") or p.get("cid") or ""

            st.session_state.current_idx    = next(
                (i for i, p in enumerate(posts) if post_key(p) not in done_ids),
                len(posts),
            )
            st.session_state.resumed_from = len(saved_rows)
        else:
            st.session_state.feedback_data   = []
            st.session_state.saved_post_ids  = set()
            st.session_state.saved_up_to     = -1
            st.session_state.current_idx     = 0
            st.session_state.resumed_from    = None

        st.session_state.post_start_time = time.time()
        st.session_state.page            = "survey"
        st.rerun()


def survey_page():
    posts = st.session_state.posts
    idx   = st.session_state.current_idx
    total = len(posts)
    post  = posts[idx]

    if st.session_state.resumed_from:
        n = st.session_state.resumed_from
        st.success(f"✅ Resumed — posts 1–{n} are already saved. Continuing from post {n + 1}.")
        st.session_state.resumed_from = None

    if st.session_state.get("_do_autosave"):
        st.session_state._do_autosave = False
        autosave_pending(force=False)

    # Progress
    st.markdown(f'<p class="progress-label">Post {idx + 1} of {total}</p>', unsafe_allow_html=True)
    st.progress((idx + 1) / total)
    st.markdown("---")

    # ── Post card ──────────────────────────────────────────────────────────────
    raw_text = str(post.get("text", "")).strip()
    text     = "" if raw_text.lower() in ("nan", "none", "") else raw_text
    media    = get_post_media(post)

    # Media type badges
    badges = ""
    if media["has_image"]:
        badges += f'<span class="media-badge badge-image">🖼 {len(media["image_urls"])} image{"s" if len(media["image_urls"]) > 1 else ""}</span>'
    if media["has_video"]:
        badges += '<span class="media-badge badge-video">▶ video</span>'
        # Heuristic: treat as potentially having audio if it's a video
        badges += '<span class="media-badge badge-audio">🔊 audio</span>'

    text_display = text if text else '<span style="color:#94a3b8;font-style:italic;">(no text)</span>'
    st.markdown(f"""
<div class="post-card">
    <div style="margin-bottom:10px;">
        <div class="post-avatar"></div>
        <span style="font-size:12px;color:#94a3b8;vertical-align:middle;">@bluesky user</span>
    </div>
    <div class="post-text">{text_display}</div>
    {f'<div style="margin-top:8px;">{badges}</div>' if badges else ''}
</div>
""", unsafe_allow_html=True)

    # ── Images ─────────────────────────────────────────────────────────────────
    if media["has_image"]:
        if len(media["image_urls"]) == 1:
            img = fetch_image(media["image_urls"][0], HF_TOKEN)
            if img:
                render_blurred_image(image_to_b64(img))
            else:
                st.caption("(Image could not be loaded)")
        else:
            # Multi-image grid
            st.markdown('<div class="media-grid-cols" style="display:flex;flex-wrap:wrap;gap:8px;">', unsafe_allow_html=True)
            cols = st.columns(min(len(media["image_urls"]), 2))
            for i, url in enumerate(media["image_urls"]):
                with cols[i % 2]:
                    img = fetch_image(url, HF_TOKEN)
                    if img:
                        render_blurred_image(image_to_b64(img), f"Hover to reveal image {i+1}")
                    else:
                        st.caption(f"(Image {i+1} could not be loaded)")
            st.markdown('</div>', unsafe_allow_html=True)

    # ── Video ──────────────────────────────────────────────────────────────────
    if media["has_video"]:
        with st.expander("▶ Click to reveal and play video", expanded=False):
            render_video(media["video_url"], HF_TOKEN)

    # ── Category reference ─────────────────────────────────────────────────────
    with st.expander("📋 View unsafe category definitions"):
        rows_html = "".join(
            f'<tr><td class="cat-label">{name}</td><td style="font-size:12px;">{desc}</td></tr>'
            for (name, desc) in LABELS.values()
        )
        st.markdown(
            f'<table class="cat-table"><tr><th style="width:28%">Category</th><th>Description</th></tr>{rows_html}</table>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Label ──────────────────────────────────────────────────────────────────
    label = st.radio(
        "**Is this post safe or unsafe?** *",
        options=["Safe", "Unsafe"],
        index=None,
        horizontal=True,
        key=f"label_{idx}",
    )

    # Unsafe categories multiselect
    unsafe_labels = []
    if label == "Unsafe":
        label_options = [f"{name} — {desc[:60]}…" for name, desc in LABELS.values()] + ["Other"]
        label_keys    = list(LABELS.keys()) + ["Other"]
        selected_display = st.multiselect(
            "**Which categories apply?** * (select all that apply)",
            options=label_options,
            key=f"unsafe_cats_{idx}",
        )
        unsafe_labels = [label_keys[label_options.index(s)] for s in selected_display]

    # ── Attribution checkboxes ─────────────────────────────────────────────────
    # Always shown; options depend on what media is present
    st.markdown("**Your Safe/Unsafe judgment is based on:** * (check all that apply)")

    attribution_options = ["Text"]
    if media["has_image"]:
        attribution_options.append("Image")
    if media["has_video"]:
        attribution_options.append("Video")
        attribution_options.append("Audio")

    # On mobile, 2 columns max to avoid cramped layout
    n_cols = min(len(attribution_options), 2)
    attr_cols = st.columns(n_cols)
    attribution_checked = {}
    for i, opt in enumerate(attribution_options):
        with attr_cols[i % n_cols]:
            attribution_checked[opt] = st.checkbox(opt, key=f"attr_{idx}_{opt}")

    selected_attributions = [opt for opt, checked in attribution_checked.items() if checked]

    # Reason
    reason = st.text_area(
        "**Briefly explain your reasoning:** *",
        key=f"reason_{idx}",
        placeholder="Why did you choose Safe or Unsafe?",
        height=100,
    )

    # ── Validation ────────────────────────────────────────────────────────────
    cats_filled  = label != "Unsafe" or len(unsafe_labels) > 0
    attr_filled  = len(selected_attributions) > 0
    all_filled   = (
        label is not None
        and reason.strip() != ""
        and attr_filled
        and cats_filled
    )

    if not all_filled:
        missing = []
        if label is None:            missing.append("Safe/Unsafe selection")
        if not cats_filled:          missing.append("at least one unsafe category")
        if not attr_filled:          missing.append("at least one attribution source")
        if not reason.strip():       missing.append("reasoning")
        st.warning(f"Please complete: {', '.join(missing)}")

    is_last   = idx >= total - 1
    btn_label = "Submit all responses ✓" if is_last else f"Next post → ({idx + 2} of {total})"

    if st.button(btn_label, type="primary", disabled=not all_filled,
                 use_container_width=True, key=f"btn_{idx}"):

        time_spent = time.time() - (st.session_state.post_start_time or time.time())
        st.session_state.feedback_data.append({
            "annotator_name":    st.session_state.annotator_name,
            "post_id":           post.get("post_id") or post.get("uri") or post.get("cid") or str(idx),
            "display_num":       post.get("display_num", idx + 1),
            "label":             label,
            "unsafe_categories": ",".join(unsafe_labels) if unsafe_labels else "",
            "reason":            reason.strip(),
            "time_spent_sec":    round(time_spent, 1),
            "attribution_source":"|".join(selected_attributions),
        })

        if is_last:
            st.session_state.page = "submitting"
            st.rerun()
        else:
            st.session_state.current_idx    += 1
            st.session_state.post_start_time = time.time()
            st.session_state._do_autosave    = True
            st.rerun()


def submitting_page():
    st.markdown("## Saving your responses...")
    progress_bar = st.progress(0)
    status       = st.empty()
    feedback     = st.session_state.feedback_data
    saved_ids    = st.session_state.get("saved_post_ids", set())
    pending      = [r for r in feedback if r["post_id"] not in saved_ids]
    total        = len(pending)
    failed       = []

    for i, row in enumerate(pending):
        status.text(f"Saving {i + 1} of {total}...")
        progress_bar.progress((i + 1) / max(total, 1))
        ok, msg = append_to_sheet(row)
        if ok:
            saved_ids.add(row["post_id"])
        else:
            failed.append(row["post_id"])
            st.warning(f"Could not save post {row['post_id']}: {msg}")
        time.sleep(0.2)

    st.session_state.saved_post_ids    = saved_ids
    st.session_state.submission_complete = len(failed) == 0
    st.session_state.page              = "summary"
    st.rerun()


def summary_page():
    st.markdown("""
<div style="text-align:center; padding:40px 0 24px;">
    <div style="font-size:3em; margin-bottom:12px;">🎉</div>
    <h1 style="color:#1e3a8a; margin:0; font-weight:700;">All done!</h1>
    <p style="color:#64748b; margin:8px 0 0;">Thank you for contributing to the Bluesky moderation study.</p>
</div>
""", unsafe_allow_html=True)

    if st.session_state.submission_complete:
        st.success(f"All {len(st.session_state.feedback_data)} responses saved successfully.")
    else:
        st.warning("Some responses may not have saved correctly. Please contact the research team.")

    st.markdown("---")
    st.markdown(f"**Annotator:** {st.session_state.annotator_name}")
    st.markdown(f"**Posts labeled:** {len(st.session_state.feedback_data)}")


# ── Router ─────────────────────────────────────────────────────────────────────

def main():
    page = st.session_state.page
    if page == "intro":
        intro_page()
    elif page == "survey":
        survey_page()
    elif page == "submitting":
        submitting_page()
    elif page == "summary":
        summary_page()
    else:
        intro_page()

if __name__ == "__main__":
    main()