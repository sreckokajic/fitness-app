import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from supabase import create_client, Client
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(page_title="Pilates Scheduler", layout="wide", page_icon="🧘")

st.markdown("""
<style>
    /* ── Global typography ── */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    /* ── Hide Streamlit chrome ── */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }

    /* ── App header ── */
    .app-header {
        display: flex;
        align-items: baseline;
        gap: 12px;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 1.5px solid #f0ede8;
    }
    .app-title {
        font-size: 22px;
        font-weight: 600;
        color: #1a1a1a;
        letter-spacing: -0.02em;
    }
    .app-subtitle {
        font-size: 13px;
        color: #9e9b94;
        font-weight: 400;
    }

    /* ── Tab styling ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: transparent;
        border-bottom: 1.5px solid #f0ede8;
        padding-bottom: 0;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'DM Sans', sans-serif;
        font-size: 13px;
        font-weight: 500;
        color: #9e9b94;
        background: transparent;
        border: none;
        padding: 6px 16px 10px;
        border-radius: 0;
    }
    .stTabs [aria-selected="true"] {
        color: #1a1a1a !important;
        border-bottom: 2px solid #1a1a1a;
        background: transparent !important;
    }

    /* ── Session card ── */
    .session-card {
        background: #ffffff;
        border: 1px solid #f0ede8;
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: all 0.15s ease;
    }
    .session-card:hover {
        border-color: #d4cfc8;
        background: #fafaf8;
    }
    .session-card.active {
        border-color: #1a1a1a;
        background: #fafaf8;
    }
    .card-set {
        font-family: 'DM Mono', monospace;
        font-size: 13px;
        font-weight: 500;
        color: #1a1a1a;
        display: inline-block;
        background: #f0ede8;
        padding: 2px 8px;
        border-radius: 5px;
        margin-bottom: 5px;
    }
    .card-date {
        font-size: 12px;
        color: #9e9b94;
        margin-bottom: 6px;
    }
    .card-attendees {
        font-size: 12px;
        color: #5a5652;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* ── Attendee chip ── */
    .chip {
        display: inline-block;
        background: #f0ede8;
        color: #5a5652;
        font-size: 11px;
        font-weight: 500;
        padding: 2px 9px;
        border-radius: 20px;
        margin: 2px 3px 2px 0;
    }

    /* ── Panel headings ── */
    .panel-label {
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        color: #9e9b94;
        margin-bottom: 1rem;
    }

    /* ── Recommendation result ── */
    .rec-row {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 14px;
        border-radius: 8px;
        margin-bottom: 6px;
        background: #fafaf8;
        border: 1px solid #f0ede8;
        font-size: 13px;
    }
    .rec-set {
        font-family: 'DM Mono', monospace;
        font-weight: 500;
        min-width: 40px;
        color: #1a1a1a;
    }
    .rec-new {
        background: #eef7ee;
        border-color: #c3e0c3;
        color: #2e6b2e;
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 20px;
        font-weight: 600;
    }
    .rec-seen {
        font-size: 12px;
        color: #9e9b94;
    }

    /* ── Divider ── */
    .soft-divider {
        border: none;
        border-top: 1px solid #f0ede8;
        margin: 1.5rem 0;
    }

    /* ── Stat card ── */
    .stat-card {
        background: #fafaf8;
        border: 1px solid #f0ede8;
        border-radius: 10px;
        padding: 16px 18px;
        text-align: center;
    }
    .stat-number {
        font-size: 28px;
        font-weight: 600;
        color: #1a1a1a;
        letter-spacing: -0.03em;
    }
    .stat-label {
        font-size: 12px;
        color: #9e9b94;
        margin-top: 2px;
    }

    /* ── Buttons ── */
    .stButton > button {
        font-family: 'DM Sans', sans-serif;
        font-size: 13px;
        font-weight: 500;
        border-radius: 8px;
        border: 1px solid #d4cfc8;
        background: white;
        color: #1a1a1a;
        padding: 6px 16px;
        transition: all 0.12s;
    }
    .stButton > button:hover {
        background: #f0ede8;
        border-color: #b5b0a8;
    }
    button[kind="primary"] {
        background: #1a1a1a !important;
        color: white !important;
        border-color: #1a1a1a !important;
    }
    button[kind="primary"]:hover {
        background: #333 !important;
    }

    /* ── Inputs ── */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    .stDateInput > div > div > input {
        font-family: 'DM Sans', sans-serif;
        font-size: 13px;
        border-radius: 8px;
        border: 1px solid #e8e4df;
    }

    /* ── Success/warning ── */
    .stSuccess, .stWarning, .stError, .stInfo {
        border-radius: 8px;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PASSWORD PROTECTION
# ─────────────────────────────────────────────
def check_password():
    def password_entered():
        if st.session_state["password"] == "reformerpilates2026":
            st.session_state["authenticated"] = True
        else:
            st.session_state["authenticated"] = False

    if "authenticated" not in st.session_state:
        st.markdown("<div style='max-width:340px; margin:4rem auto;'>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:20px; font-weight:600; margin-bottom:1rem;'>Pilates Scheduler</p>", unsafe_allow_html=True)
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.markdown("</div>", unsafe_allow_html=True)
        return False
    elif not st.session_state["authenticated"]:
        st.markdown("<div style='max-width:340px; margin:4rem auto;'>", unsafe_allow_html=True)
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("Incorrect password")
        st.markdown("</div>", unsafe_allow_html=True)
        return False
    return True

if not check_password():
    st.stop()


# ─────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────
url = "https://pjeomsygofqwfjtyybzy.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqZW9tc3lnb2Zxd2ZqdHl5Ynp5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Mzg1NTQ1NCwiZXhwIjoyMDg5NDMxNDU0fQ.DmUFOtsxJCeo_cQonj1Hp_UYagdi_iZHZm7bidm7uGw"
supabase: Client = create_client(url, key)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def parse_names(text):
    if not text:
        return []
    return [n.strip() for n in text.split(",") if n.strip()]

def get_or_create_person(name):
    name = name.strip()
    res = supabase.table("persons").select("*").eq("name", name).execute()
    if res.data:
        return res.data[0]["id"]
    supabase.table("persons").insert({"name": name}).execute()
    return supabase.table("persons").select("*").eq("name", name).execute().data[0]["id"]

def get_or_create_set(name):
    name = name.strip().upper()
    if not name.startswith("T"):
        name = "T" + name
    res = supabase.table("training_sets").select("*").eq("name", name).execute()
    if res.data:
        return res.data[0]["id"]
    supabase.table("training_sets").insert({"name": name}).execute()
    return supabase.table("training_sets").select("*").eq("name", name).execute().data[0]["id"]

@st.cache_data(ttl=30)
def get_persons():
    res = supabase.table("persons").select("*").order("name").execute()
    df = pd.DataFrame(res.data)
    return df if not df.empty else pd.DataFrame(columns=["id", "name"])

@st.cache_data(ttl=30)
def get_sets():
    res = supabase.table("training_sets").select("*").order("name").execute()
    df = pd.DataFrame(res.data)
    return df if not df.empty else pd.DataFrame(columns=["id", "name"])

@st.cache_data(ttl=30)
def get_sessions():
    # 3 bulk fetches total — no per-row queries
    sessions_res  = supabase.table("sessions").select("*").order("date", desc=True).execute()
    sets_res      = supabase.table("training_sets").select("id, name").execute()
    persons_res   = supabase.table("persons").select("id, name").execute()
    attendance_res = supabase.table("attendance").select("session_id, person_id").execute()

    if not sessions_res.data:
        return pd.DataFrame(columns=["id", "date", "training_set", "attendees", "attendees_str"])

    # Build lookup dicts in memory
    set_name   = {r["id"]: r["name"] for r in sets_res.data}
    person_name = {r["id"]: r["name"] for r in persons_res.data}

    # Group attendees by session_id
    from collections import defaultdict
    attendees_by_session = defaultdict(list)
    for a in attendance_res.data:
        name = person_name.get(a["person_id"], "")
        if name:
            attendees_by_session[a["session_id"]].append(name)

    result = []
    for s in sessions_res.data:
        attendees = sorted(attendees_by_session.get(s["id"], []))
        result.append({
            "id":            s["id"],
            "date":          s["date"],
            "training_set":  set_name.get(s["training_set_id"], ""),
            "attendees":     attendees,
            "attendees_str": ", ".join(attendees),
        })

    return pd.DataFrame(result)

def invalidate_cache():
    get_persons.clear()
    get_sets.clear()
    get_sessions.clear()


# ─────────────────────────────────────────────
# SESSION STATE DEFAULTS
# ─────────────────────────────────────────────
for key_name, default in {
    "selected_session_id": None,
    "show_new_form": False,
    "confirm_delete": False,
}.items():
    if key_name not in st.session_state:
        st.session_state[key_name] = default


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <span class="app-title">Pilates Scheduler</span>
    <span class="app-subtitle">Training session tracker</span>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab_sessions, tab_recommend, tab_stats, tab_persons = st.tabs([
    "Sessions", "Recommend", "Statistics", "People"
])


# ═════════════════════════════════════════════
# TAB 1 — SESSIONS
# ═════════════════════════════════════════════
with tab_sessions:
    sessions_df = get_sessions()
    persons_df = get_persons()
    sets_df = get_sets()
    all_names = persons_df["name"].tolist() if not persons_df.empty else []
    all_set_names = sets_df["name"].tolist() if not sets_df.empty else []

    # ── Filters bar ──
    with st.expander("🔍 Filter sessions", expanded=False):
        fc1, fc2, fc3, fc4 = st.columns([2, 2, 1.5, 1.5])
        with fc1:
            filter_person = st.selectbox("Person", ["All"] + all_names, key="f_person")
        with fc2:
            filter_set = st.selectbox("Training set", ["All"] + all_set_names, key="f_set")
        with fc3:
            start_date = st.date_input("From", value=date(2024, 1, 1), key="f_start")
        with fc4:
            end_date = st.date_input("To", value=date.today(), key="f_end")

    # Apply filters
    if not sessions_df.empty:
        filtered = sessions_df.copy()
        filtered = filtered[
            (pd.to_datetime(filtered["date"]) >= pd.to_datetime(start_date)) &
            (pd.to_datetime(filtered["date"]) <= pd.to_datetime(end_date))
        ]
        if filter_person != "All":
            filtered = filtered[filtered["attendees_str"].str.contains(filter_person, na=False)]
        if filter_set != "All":
            filtered = filtered[filtered["training_set"] == filter_set]
    else:
        filtered = sessions_df

    # ── Two-column layout ──
    left_col, right_col = st.columns([2, 3], gap="large")

    with left_col:
        # New session button
        if st.button("＋ New session", use_container_width=True):
            st.session_state["show_new_form"] = True
            st.session_state["selected_session_id"] = None
            st.session_state["confirm_delete"] = False

        st.markdown("<div style='margin-bottom:0.75rem;'></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='panel-label'>{len(filtered)} session{'s' if len(filtered) != 1 else ''}</div>", unsafe_allow_html=True)

        if filtered.empty:
            st.markdown("<p style='font-size:13px; color:#9e9b94;'>No sessions found.</p>", unsafe_allow_html=True)
        else:
            for _, row in filtered.iterrows():
                is_active = st.session_state["selected_session_id"] == row["id"]
                card_class = "session-card active" if is_active else "session-card"
                attendee_preview = ", ".join(row["attendees"][:4])
                if len(row["attendees"]) > 4:
                    attendee_preview += f" +{len(row['attendees']) - 4}"

                card_html = f"""
                <div class="{card_class}">
                    <div><span class="card-set">{row["training_set"]}</span></div>
                    <div class="card-date">{row["date"]}</div>
                    <div class="card-attendees">{attendee_preview if attendee_preview else "—"}</div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                if st.button(f"Select", key=f"sel_{row['id']}", use_container_width=True,
                             help=f"Edit {row['training_set']} on {row['date']}"):
                    st.session_state["selected_session_id"] = row["id"]
                    st.session_state["show_new_form"] = False
                    st.session_state["confirm_delete"] = False
                    st.rerun()

    # ── Right panel ──
    with right_col:

        # ── NEW SESSION FORM ──
        if st.session_state["show_new_form"]:
            st.markdown("<div class='panel-label'>New session</div>", unsafe_allow_html=True)

            new_date = st.date_input("Date", value=date.today(), key="new_date")
            new_set = st.selectbox(
                "Training set",
                all_set_names + ["Enter manually…"],
                key="new_set_select"
            )
            if new_set == "Enter manually…":
                new_set = st.text_input("Training set name (e.g. T7)", key="new_set_manual")

            new_attendees = st.multiselect("Attendees", all_names, key="new_attendees")
            new_extra = st.text_input("Add new people (comma separated)", key="new_extra",
                                      placeholder="e.g. Ana, Petra")

            bcol1, bcol2 = st.columns([1, 1])
            with bcol1:
                if st.button("Save session", type="primary", use_container_width=True):
                    if not new_set:
                        st.error("Please enter a training set name.")
                    else:
                        set_id = get_or_create_set(new_set)
                        sess_res = supabase.table("sessions").insert({
                            "date": new_date.isoformat(),
                            "training_set_id": set_id
                        }).execute()
                        sid = sess_res.data[0]["id"]
                        all_new = list(new_attendees) + parse_names(new_extra)
                        for name in all_new:
                            pid = get_or_create_person(name)
                            supabase.table("attendance").insert({"session_id": sid, "person_id": pid}).execute()
                        st.success("Session saved!")
                        st.session_state["show_new_form"] = False
                        st.session_state["selected_session_id"] = sid
                        invalidate_cache()
                        st.rerun()
            with bcol2:
                if st.button("Cancel", use_container_width=True):
                    st.session_state["show_new_form"] = False
                    st.rerun()

        # ── EDIT EXISTING SESSION ──
        elif st.session_state["selected_session_id"] is not None:
            sid = st.session_state["selected_session_id"]
            session_row = sessions_df[sessions_df["id"] == sid]

            if session_row.empty:
                st.info("Session not found — it may have been deleted.")
                st.session_state["selected_session_id"] = None
            else:
                session_row = session_row.iloc[0]
                st.markdown("<div class='panel-label'>Edit session</div>", unsafe_allow_html=True)

                # Current attendees as chips
                chips_html = "".join([f"<span class='chip'>{a}</span>" for a in sorted(session_row["attendees"])])
                st.markdown(f"<div style='margin-bottom:1rem;'>{chips_html}</div>", unsafe_allow_html=True)

                edit_date = st.date_input(
                    "Date",
                    value=datetime.strptime(session_row["date"], "%Y-%m-%d").date(),
                    key=f"edit_date_{sid}"
                )
                edit_set = st.selectbox(
                    "Training set",
                    all_set_names + ["Enter manually…"],
                    index=all_set_names.index(session_row["training_set"]) if session_row["training_set"] in all_set_names else 0,
                    key=f"edit_set_{sid}"
                )
                if edit_set == "Enter manually…":
                    edit_set = st.text_input("Training set name", value=session_row["training_set"], key=f"edit_set_manual_{sid}")

                edit_attendees = st.multiselect(
                    "Attendees",
                    all_names,
                    default=[a for a in session_row["attendees"] if a in all_names],
                    key=f"edit_att_{sid}"
                )
                edit_extra = st.text_input(
                    "Add new people (comma separated)",
                    key=f"edit_extra_{sid}",
                    placeholder="e.g. Maja, Luka"
                )

                st.markdown("<hr class='soft-divider'>", unsafe_allow_html=True)

                bcol1, bcol2, bcol3 = st.columns([2, 1, 1])
                with bcol1:
                    if st.button("Save changes", type="primary", use_container_width=True, key=f"save_{sid}"):
                        set_id = get_or_create_set(edit_set)
                        supabase.table("sessions").update({
                            "date": edit_date.isoformat(),
                            "training_set_id": set_id
                        }).eq("id", sid).execute()
                        supabase.table("attendance").delete().eq("session_id", sid).execute()
                        all_edit = list(edit_attendees) + parse_names(edit_extra)
                        for name in all_edit:
                            pid = get_or_create_person(name)
                            supabase.table("attendance").insert({"session_id": sid, "person_id": pid}).execute()
                        st.success("Changes saved!")
                        invalidate_cache()
                        st.rerun()

                with bcol2:
                    if not st.session_state["confirm_delete"]:
                        if st.button("Delete", use_container_width=True, key=f"del_btn_{sid}"):
                            st.session_state["confirm_delete"] = True
                            st.rerun()
                    else:
                        st.warning("Sure?")
                        if st.button("Yes, delete", use_container_width=True, key=f"del_confirm_{sid}"):
                            supabase.table("attendance").delete().eq("session_id", sid).execute()
                            supabase.table("sessions").delete().eq("id", sid).execute()
                            st.session_state["selected_session_id"] = None
                            st.session_state["confirm_delete"] = False
                            invalidate_cache()
                            st.rerun()

                with bcol3:
                    if st.session_state["confirm_delete"]:
                        if st.button("Cancel", use_container_width=True, key=f"del_cancel_{sid}"):
                            st.session_state["confirm_delete"] = False
                            st.rerun()

        # ── EMPTY STATE ──
        else:
            st.markdown("""
            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center;
                        min-height:300px; color:#b5b0a8; text-align:center;">
                <div style="font-size:36px; margin-bottom:12px;">←</div>
                <div style="font-size:14px; font-weight:500;">Select a session to edit</div>
                <div style="font-size:12px; margin-top:6px;">or create a new one</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<hr class='soft-divider'>", unsafe_allow_html=True)

    # ── Import Excel ──
    with st.expander("📥 Import from Excel"):
        st.markdown("<p style='font-size:12px; color:#9e9b94;'>Expected columns: <code>date</code>, <code>training_set</code>, <code>attendees</code> (comma separated names)</p>", unsafe_allow_html=True)
        file = st.file_uploader("Upload .xlsx", type=["xlsx"])
        if file:
            df_import = pd.read_excel(file)
            st.dataframe(df_import, use_container_width=True)
            if st.button("Import all rows"):
                for _, row in df_import.iterrows():
                    session_date = pd.to_datetime(row["date"]).date().isoformat()
                    set_id = get_or_create_set(str(row["training_set"]))
                    sess_res = supabase.table("sessions").insert({"date": session_date, "training_set_id": set_id}).execute()
                    new_sid = sess_res.data[0]["id"]
                    for n in parse_names(str(row["attendees"])):
                        pid = get_or_create_person(n)
                        supabase.table("attendance").insert({"session_id": new_sid, "person_id": pid}).execute()
                st.success(f"Imported {len(df_import)} rows.")
                invalidate_cache()
                st.rerun()


# ═════════════════════════════════════════════
# TAB 2 — RECOMMEND
# ═════════════════════════════════════════════
with tab_recommend:
    persons_df = get_persons()
    sets_df = get_sets()

    st.markdown("<p style='font-size:13px; color:#5a5652; margin-bottom:1.5rem;'>Select who will attend the next session. The scheduler ranks training sets by how many of them have done each set in the last 45 days — sets ranked lower are fresher.</p>", unsafe_allow_html=True)

    selected_people = st.multiselect("Who is attending?", persons_df["name"] if not persons_df.empty else [])

    if st.button("Get recommendations", type="primary"):
        if not selected_people:
            st.warning("Select at least one person first.")
        else:
            selected_ids = persons_df[persons_df["name"].isin(selected_people)]["id"].tolist()
            cutoff = (datetime.today() - timedelta(days=45)).date().isoformat()
            results = []
            for _, s in sets_df.iterrows():
                sessions_res = supabase.table("sessions").select("*").eq("training_set_id", s["id"]).gte("date", cutoff).execute()
                seen_people = set()
                for sess in sessions_res.data:
                    att_res = supabase.table("attendance").select("*").eq("session_id", sess["id"]).execute()
                    for a in att_res.data:
                        seen_people.add(a["person_id"])
                seen_count = sum(1 for pid in selected_ids if pid in seen_people)
                results.append((s["name"], seen_count, len(selected_ids)))
            results.sort(key=lambda x: x[1])

            st.markdown("<div class='panel-label' style='margin-top:1rem;'>Ranked results</div>", unsafe_allow_html=True)
            for name, seen, total in results:
                if seen == 0:
                    st.markdown(f"""
                    <div class="rec-row" style="background:#eef7ee; border-color:#c3e0c3;">
                        <span class="rec-set">{name}</span>
                        <span class="rec-new">NEW for everyone</span>
                    </div>""", unsafe_allow_html=True)
                else:
                    pct = int(seen / total * 100) if total else 0
                    bar_w = max(4, pct)
                    st.markdown(f"""
                    <div class="rec-row">
                        <span class="rec-set">{name}</span>
                        <div style="flex:1; background:#f0ede8; border-radius:3px; height:4px;">
                            <div style="width:{bar_w}%; background:#1a1a1a; height:4px; border-radius:3px;"></div>
                        </div>
                        <span class="rec-seen">{seen}/{total} seen it recently</span>
                    </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════
# TAB 3 — STATISTICS
# ═════════════════════════════════════════════
with tab_stats:
    sessions_df = get_sessions()
    persons_df = get_persons()

    if sessions_df.empty:
        st.info("No session data yet.")
    else:
        # ── Summary numbers ──
        total_sessions = len(sessions_df)
        total_attendances = sessions_df["attendees"].apply(len).sum()
        avg_per_session = round(total_attendances / total_sessions, 1) if total_sessions else 0
        unique_people = len(set(name for names in sessions_df["attendees"] for name in names))

        c1, c2, c3, c4 = st.columns(4)
        for col, num, label in zip(
            [c1, c2, c3, c4],
            [total_sessions, total_attendances, avg_per_session, unique_people],
            ["Total sessions", "Total attendances", "Avg per session", "Unique people"]
        ):
            with col:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-number">{num}</div>
                    <div class="stat-label">{label}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<hr class='soft-divider'>", unsafe_allow_html=True)

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("<div class='panel-label'>Training set frequency</div>", unsafe_allow_html=True)
            freq = sessions_df["training_set"].value_counts()
            fig, ax = plt.subplots(figsize=(5, 3.5))
            bars = ax.barh(freq.index, freq.values, color="#1a1a1a", height=0.55)
            ax.set_xlabel("Sessions", fontsize=10, color="#9e9b94")
            ax.tick_params(colors="#5a5652", labelsize=9)
            ax.spines[["top", "right", "left"]].set_visible(False)
            ax.spines["bottom"].set_color("#f0ede8")
            ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
            fig.patch.set_alpha(0)
            ax.set_facecolor("none")
            plt.tight_layout()
            st.pyplot(fig)

        with chart_col2:
            st.markdown("<div class='panel-label'>Sessions over time</div>", unsafe_allow_html=True)
            sessions_df["date_dt"] = pd.to_datetime(sessions_df["date"])
            timeline = sessions_df.groupby(sessions_df["date_dt"].dt.to_period("W")).size()
            timeline.index = timeline.index.astype(str)
            fig2, ax2 = plt.subplots(figsize=(5, 3.5))
            ax2.plot(range(len(timeline)), timeline.values, color="#1a1a1a", linewidth=1.5, marker="o", markersize=3)
            ax2.fill_between(range(len(timeline)), timeline.values, alpha=0.08, color="#1a1a1a")
            ax2.set_xticks([])
            ax2.tick_params(colors="#5a5652", labelsize=9)
            ax2.spines[["top", "right", "left"]].set_visible(False)
            ax2.spines["bottom"].set_color("#f0ede8")
            ax2.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
            fig2.patch.set_alpha(0)
            ax2.set_facecolor("none")
            plt.tight_layout()
            st.pyplot(fig2)

        st.markdown("<hr class='soft-divider'>", unsafe_allow_html=True)

        # ── Per-person history ──
        st.markdown("<div class='panel-label'>Person history</div>", unsafe_allow_html=True)
        if not persons_df.empty:
            person_name = st.selectbox("Select person", persons_df["name"].tolist(), key="stats_person")
            if person_name:
                person_sessions = sessions_df[sessions_df["attendees_str"].str.contains(person_name, na=False)]
                if person_sessions.empty:
                    st.markdown("<p style='font-size:13px; color:#9e9b94;'>No sessions found for this person.</p>", unsafe_allow_html=True)
                else:
                    person_sessions = person_sessions[["date", "training_set"]].sort_values("date", ascending=False)
                    st.dataframe(person_sessions.rename(columns={"date": "Date", "training_set": "Training set"}),
                                 use_container_width=True, hide_index=True)


# ═════════════════════════════════════════════
# TAB 4 — PEOPLE
# ═════════════════════════════════════════════
with tab_persons:
    persons_df = get_persons()

    if persons_df.empty:
        st.info("No people in the database yet.")
    else:
        st.markdown("<div class='panel-label'>All people</div>", unsafe_allow_html=True)
        st.dataframe(persons_df[["name"]].rename(columns={"name": "Name"}),
                     use_container_width=True, hide_index=True)

        st.markdown("<hr class='soft-divider'>", unsafe_allow_html=True)

        p_col1, p_col2 = st.columns(2)

        with p_col1:
            st.markdown("<div class='panel-label'>Rename person</div>", unsafe_allow_html=True)
            rename_person = st.selectbox("Person to rename", persons_df["name"].tolist(), key="rename_sel")
            new_name = st.text_input("New name", key="rename_new")
            if st.button("Rename", type="primary", key="rename_btn"):
                if new_name.strip():
                    pid = persons_df[persons_df["name"] == rename_person]["id"].values[0]
                    supabase.table("persons").update({"name": new_name.strip()}).eq("id", pid).execute()
                    st.success(f"Renamed to {new_name.strip()}")
                    invalidate_cache()
                    st.rerun()
                else:
                    st.warning("Enter a new name.")

        with p_col2:
            st.markdown("<div class='panel-label'>Merge duplicates</div>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:12px; color:#9e9b94;'>All sessions from the source person will be moved to the target, then the source is deleted.</p>", unsafe_allow_html=True)
            source = st.selectbox("Source (will be deleted)", persons_df["name"].tolist(), key="merge_src")
            target = st.selectbox("Target (keep)", persons_df["name"].tolist(), key="merge_tgt")
            if st.button("Merge", key="merge_btn"):
                src_id = persons_df[persons_df["name"] == source]["id"].values[0]
                tgt_id = persons_df[persons_df["name"] == target]["id"].values[0]
                if src_id == tgt_id:
                    st.warning("Source and target are the same person.")
                else:
                    supabase.table("attendance").update({"person_id": tgt_id}).eq("person_id", src_id).execute()
                    # Remove duplicate attendance rows
                    all_att = supabase.table("attendance").select("*").execute().data
                    seen_keys = set()
                    for a in all_att:
                        k = (a["session_id"], a["person_id"])
                        if k in seen_keys:
                            supabase.table("attendance").delete().eq("id", a["id"]).execute()
                        else:
                            seen_keys.add(k)
                    supabase.table("persons").delete().eq("id", src_id).execute()
                    st.success(f"Merged {source} → {target}")
                    invalidate_cache()
                    st.rerun()

        st.markdown("<hr class='soft-divider'>", unsafe_allow_html=True)

        st.markdown("<div class='panel-label'>Delete person</div>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:12px; color:#9e9b94; margin-bottom:8px;'>This removes the person from all sessions and the database.</p>", unsafe_allow_html=True)
        del_person = st.selectbox("Person to delete", persons_df["name"].tolist(), key="del_person_sel")
        if st.button("Delete person", key="del_person_btn"):
            pid = persons_df[persons_df["name"] == del_person]["id"].values[0]
            supabase.table("attendance").delete().eq("person_id", pid).execute()
            supabase.table("persons").delete().eq("id", pid).execute()
            st.success(f"Deleted {del_person}")
            invalidate_cache()
            st.rerun()
