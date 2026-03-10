import streamlit as st
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
import time
import json
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Bluesky Moderation Study", page_icon="🔵", layout="centered"
)

# ── Styling ────────────────────────────────────────────────────────────────────

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Force light mode */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #f8fafc !important;
    color: #0f172a !important;
}
[class*="css"] { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 2rem; background-color: #f8fafc !important; }

/* Force all text dark */
p, li, span, label, h1, h2, h3, h4 { color: #0f172a !important; }

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
.cat-table { width: 100%; border-collapse: collapse; margin: 12px 0 20px; }
.cat-table th { background: #1e40af !important; color: #ffffff !important; padding: 10px 14px; text-align: left; font-size: 13px; }
.cat-table td { padding: 10px 14px; border-bottom: 1px solid #e2e8f0; font-size: 13px; vertical-align: top; line-height: 1.6; color: #0f172a !important; background: #ffffff !important; }
.cat-table tr:nth-child(even) td { background: #f8fafc !important; }
.cat-label { font-weight: 600; color: #1e293b !important; white-space: nowrap; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Config ─────────────────────────────────────────────────────────────────────

GOOGLE_APPS_SCRIPT_URL = st.secrets["GOOGLE_APPS_SCRIPT_URL"]
# Optional GET endpoint to read back saved rows for resume.
# If not set in secrets, resume is silently disabled.
GOOGLE_SHEET_READ_URL = st.secrets.get("GOOGLE_SHEET_READ_URL", "")
AUTOSAVE_EVERY = 10

# ── Session state ──────────────────────────────────────────────────────────────

for k, v in {
    "page": "intro",
    "annotator_name": "",
    "posts": [],
    "current_idx": 0,
    "feedback_data": [],
    "saved_post_ids": set(),  # post_ids already written to sheet
    "saved_up_to": -1,
    "submission_complete": False,
    "post_start_time": None,
    "resume_checked": False,
    "_do_autosave": False,
    "resumed_from": None,
    "_saved_rows_cache": [],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helpers ────────────────────────────────────────────────────────────────────


@st.cache_data
def load_posts(csv_path="data/survey_posts.csv"):
    df = pd.read_csv(csv_path)
    if "display_num" in df.columns:
        df = df.sort_values("display_num").reset_index(drop=True)
    return df.to_dict("records")


def shuffle_posts_for_annotator(posts, annotator_name):
    """Shuffle posts using annotator name as seed — reproducible, unique per annotator."""
    import random

    seed = sum(ord(c) for c in annotator_name.lower().strip())
    rng = random.Random(seed)
    shuffled = posts.copy()
    rng.shuffle(shuffled)
    return shuffled


def show_image(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return Image.open(BytesIO(r.content))
    except Exception:
        return None


def append_to_sheet(data, max_retries=3):
    """POST a single labeling row to Google Sheets via Apps Script."""
    payload = {
        "annotator_name": data["annotator_name"],
        "post_id": data["post_id"],
        "display_num": data["display_num"],
        "label": data["label"],
        "reason": data["reason"],
        "time_spent_sec": data["time_spent_sec"],
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
                    return (
                        (True, "OK")
                        if "success" in resp.text.lower()
                        else (False, resp.text[:200])
                    )
            if attempt < max_retries - 1:
                time.sleep(2)
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(3)
        except Exception as e:
            return False, str(e)
    return False, "Max retries exceeded"


def fetch_saved_progress(annotator_name):
    """
    GET rows already saved for this annotator from Google Sheets.
    Your Apps Script GET handler should accept ?annotator=<name> and return:
        {"rows": [{"display_num":1,"post_id":"...","label":"Safe",
                   "reason":"...","time_spent_sec":12.3}, ...]}
    Returns [] if the endpoint isn't configured or on any error.
    """
    if not GOOGLE_SHEET_READ_URL:
        return []
    try:
        resp = requests.get(
            GOOGLE_SHEET_READ_URL,
            params={"annotator": annotator_name},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json().get("rows", [])
    except Exception:
        pass
    return []


def autosave_pending(force=False):
    """
    Flush unsaved responses to Google Sheets.
    Tracks progress by post_id (since display order varies per annotator).
    """
    feedback = st.session_state.feedback_data
    saved_ids = st.session_state.get("saved_post_ids", set())
    pending = [r for r in feedback if r["post_id"] not in saved_ids]

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

    st.toast(f"💾 Progress saved ({len(saved_ids)}/100 posts)", icon="💾")
    return True


# ── Pages ──────────────────────────────────────────────────────────────────────


def intro_page():
    st.markdown(
        """
    <div style="text-align:center; padding:10px 0 24px;">
        <div style="font-size:2.8em; margin-bottom:10px;">🔵</div>
        <h1 style="color:#1e3a8a; margin:0; font-size:2em; font-weight:700;">Bluesky Content Moderation</h1>
        <p style="color:#64748b; margin:6px 0 0;">Internal Team Labeling Study &nbsp;·&nbsp; Max Planck Institute for Software Systems</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("### About this study")
    st.markdown(
        """
You will review **100 Bluesky posts** and label each one as **Safe** or **Unsafe**
according to Bluesky's Community Guidelines. For each post you must also provide
a brief written reasoning.

> ⚠️ Some posts may contain offensive language, hate speech, or explicit content.
> Please proceed only if you are comfortable.
    """
    )

    st.markdown("### Labeling guidelines")
    st.markdown(
        """
<table class="cat-table">
<tr><th style="width:22%">Category</th><th>Mark as <strong>Unsafe</strong> if the post…</th></tr>
<tr><td class="cat-label">Violence &amp; Threats</td>
    <td>Threatens death or serious harm; promotes, glorifies, or incites violence; shares graphic violent content to shock or intimidate.</td></tr>
<tr><td class="cat-label">Hate Speech</td>
    <td>Attacks or incites hatred based on protected characteristics (race, ethnicity, religion, gender identity, sexual orientation, disability, etc.). Includes slurs and dehumanizing comparisons.</td></tr>
<tr><td class="cat-label">Adult Content</td>
    <td>Explicit sexual content that is non-consensual, involves minors, or is unlabeled.</td></tr>
<tr><td class="cat-label">Self-Harm</td>
    <td>Promotes, instructs, or depicts self-harm, suicide, eating disorders, or extreme dieting.</td></tr>
<tr><td class="cat-label">Harassment</td>
    <td>Persistently targets or creates malicious content designed to humiliate or degrade individuals.</td></tr>
<tr><td class="cat-label">Spam &amp; Deception</td>
    <td>Spam, financial scams, phishing, artificial engagement manipulation, or impersonation.</td></tr>
</table>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
**Safe** — does not fall into any category above. Includes everyday content, news, humor,
strong language not targeting anyone, fictional violence in art/games, journalism, or labeled parody.
    """
    )

    st.markdown("---")
    st.markdown("### Your information")

    name = st.text_input("Your name or initials *", placeholder="e.g. Ines A.")
    name = name.strip()
    name_valid = len(name) >= 2

    # Check for saved progress once per session when a valid name is typed
    if name_valid and not st.session_state.resume_checked:
        with st.spinner("Checking for saved progress..."):
            rows = fetch_saved_progress(name)
        st.session_state._saved_rows_cache = rows
        st.session_state.resume_checked = True

    saved_rows = st.session_state._saved_rows_cache if name_valid else []
    resume_available = len(saved_rows) > 0
    resume = False

    if resume_available:
        completed = len(saved_rows)
        st.info(f"💾 Found saved progress: **{completed}/100 posts** already labeled.")
        resume = st.checkbox(f"Resume from post {completed + 1}", value=True)

    st.markdown("---")

    btn_label = (
        "Resume labeling →" if (resume_available and resume) else "Begin labeling →"
    )
    if st.button(
        btn_label, type="primary", disabled=not name_valid, use_container_width=True
    ):
        posts = shuffle_posts_for_annotator(load_posts(), name)
        st.session_state.annotator_name = name
        st.session_state.posts = posts

        if resume_available and resume:
            # Populate feedback_data from saved rows so autosave won't re-send them
            st.session_state.feedback_data = [
                {
                    "annotator_name": name,
                    "post_id": r.get("post_id", ""),
                    "display_num": int(r.get("display_num", 0)),
                    "label": r.get("label", ""),
                    "reason": r.get("reason", ""),
                    "time_spent_sec": float(r.get("time_spent_sec", 0)),
                }
                for r in saved_rows
            ]
            done_ids = {r["post_id"] for r in st.session_state.feedback_data}
            st.session_state.saved_post_ids = done_ids
            st.session_state.saved_up_to = len(done_ids)
            st.session_state.current_idx = next(
                (
                    i
                    for i, p in enumerate(posts)
                    if p.get("post_id", "") not in done_ids
                ),
                len(posts),
            )
            st.session_state.resumed_from = len(saved_rows)
        else:
            st.session_state.feedback_data = []
            st.session_state.saved_post_ids = set()
            st.session_state.saved_up_to = -1
            st.session_state.current_idx = 0
            st.session_state.resumed_from = None

        st.session_state.post_start_time = time.time()
        st.session_state.page = "survey"
        st.rerun()


def survey_page():
    posts = st.session_state.posts
    idx = st.session_state.current_idx
    total = len(posts)
    post = posts[idx]

    # One-time resume banner
    if st.session_state.resumed_from:
        n = st.session_state.resumed_from
        st.success(f"Resumed from post {n + 1} — posts 1–{n} are already saved.")
        st.session_state.resumed_from = None

    # Run autosave if flagged (fires after rerun, never blocks button click)
    if st.session_state.get("_do_autosave"):
        st.session_state._do_autosave = False
        autosave_pending(force=False)

    # Progress bar
    st.markdown(
        f'<p class="progress-label">Post {idx + 1} of {total}</p>',
        unsafe_allow_html=True,
    )
    st.progress((idx + 1) / total)
    st.markdown("---")

    # Post card
    text = str(post.get("text", ""))
    image_url = str(post.get("image_url", "")).strip()
    has_image = str(post.get("has_image", "")).strip().lower() in (
        "true",
        "1",
        "yes",
    ) and image_url not in ("", "nan", "none", "")

    st.markdown(
        f"""
<div class="post-card">
    <div style="margin-bottom:10px;">
        <div class="post-avatar"></div>
        <span style="font-size:12px;color:#94a3b8;vertical-align:middle;">@bluesky user</span>
    </div>
    <div class="post-text">{text}</div>
</div>
    """,
        unsafe_allow_html=True,
    )

    if has_image:
        img = show_image(image_url)
        if img:
            _, col, _ = st.columns([1, 3, 1])
            with col:
                st.image(img, use_container_width=True)
        else:
            st.caption("(Image could not be loaded)")

    st.markdown("---")

    label = st.radio(
        "**Is this post safe or unsafe?** *",
        options=["Safe", "Unsafe"],
        index=None,
        horizontal=True,
        key=f"label_{idx}",
    )
    reason = st.text_area(
        "**Briefly explain your reasoning:** *",
        key=f"reason_{idx}",
        placeholder="Why did you choose Safe or Unsafe?",
        height=100,
    )

    all_filled = label is not None and reason.strip() != ""
    if not all_filled:
        missing = []
        if label is None:
            missing.append("Safe/Unsafe selection")
        if not reason.strip():
            missing.append("reasoning")
        st.warning(f"Please complete: {', '.join(missing)}")

    is_last = idx >= total - 1
    btn_label = (
        "Submit all responses ✓" if is_last else f"Next post → ({idx + 2} of {total})"
    )

    if st.button(
        btn_label,
        type="primary",
        disabled=not all_filled,
        use_container_width=True,
        key=f"btn_{idx}",
    ):

        time_spent = time.time() - (st.session_state.post_start_time or time.time())
        st.session_state.feedback_data.append(
            {
                "annotator_name": st.session_state.annotator_name,
                "post_id": post.get("post_id", ""),
                "display_num": post.get("display_num", idx + 1),
                "label": label,
                "reason": reason.strip(),
                "time_spent_sec": round(time_spent, 1),
            }
        )

        if is_last:
            st.session_state.page = "submitting"
            st.rerun()
        else:
            st.session_state.current_idx += 1
            st.session_state.post_start_time = time.time()
            st.session_state._do_autosave = True
            st.rerun()


def submitting_page():
    st.markdown("## Saving your responses...")
    progress_bar = st.progress(0)
    status = st.empty()
    feedback = st.session_state.feedback_data
    saved_ids = st.session_state.get("saved_post_ids", set())
    pending = [r for r in feedback if r["post_id"] not in saved_ids]
    total = len(pending)

    failed = []
    for i, row in enumerate(pending):
        status.text(f"Saving {i + 1} of {total}...")
        progress_bar.progress((i + 1) / max(total, 1))
        ok, msg = append_to_sheet(row)
        if ok:
            saved_ids.add(row["post_id"])
        else:
            failed.append(row["post_id"])
            st.warning(f"Could not save post {row[chr(39)]}: {msg}")
        time.sleep(0.2)

    st.session_state.saved_post_ids = saved_ids
    st.session_state.submission_complete = len(failed) == 0
    st.session_state.page = "summary"
    st.rerun()


def summary_page():
    st.markdown(
        """
<div style="text-align:center; padding:40px 0 24px;">
    <div style="font-size:3em; margin-bottom:12px;">🎉</div>
    <h1 style="color:#1e3a8a; margin:0; font-weight:700;">All done!</h1>
    <p style="color:#64748b; margin:8px 0 0;">Thank you for contributing to the Bluesky moderation study.</p>
</div>
    """,
        unsafe_allow_html=True,
    )

    if st.session_state.submission_complete:
        st.success(
            f"All {len(st.session_state.feedback_data)} responses saved successfully."
        )
    else:
        st.warning(
            "Some responses may not have saved correctly. Please contact the research team."
        )

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
