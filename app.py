import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from supabase import create_client, Client
import matplotlib.pyplot as plt

# -------------------------
# PASSWORD PROTECTION
# -------------------------
def check_password():
    def password_entered():
        if st.session_state["password"] == "reformerpilates2026":
            st.session_state["authenticated"] = True
        else:
            st.session_state["authenticated"] = False

    if "authenticated" not in st.session_state:
        st.text_input("Enter password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["authenticated"]:
        st.text_input("Enter password", type="password", on_change=password_entered, key="password")
        st.error("Wrong password")
        return False
    else:
        return True

if not check_password():
    st.stop()

# -------------------------
# DATABASE CONNECTION
# -------------------------
url = "https://pjeomsygofqwfjtyybzy.supabase.co"  # your Supabase URL
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqZW9tc3lnb2ZxdHl5Ynp5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM4NTU0NTQsImV4cCI6MjA4OTQzMTQ1NH0.JmnaMEwOTXAmopRi5D-PsYUSfvrNhm4Mz-BhtEw2Q-o"
supabase: Client = create_client(url, key)

# -------------------------
# HELPERS
# -------------------------
def parse_names(input_text):
    if not input_text:
        return []
    return [n.strip() for n in input_text.split(",") if n.strip()]

def get_or_create_person(name):
    name = name.strip()
    res = supabase.table("persons").select("*").eq("name", name).execute()
    if res.data:
        return res.data[0]["id"]
    supabase.table("persons").insert({"name": name}).execute()
    res2 = supabase.table("persons").select("*").eq("name", name).execute()
    return res2.data[0]["id"]

def get_or_create_set(name):
    name = name.strip().upper()
    if not name.startswith("T"):
        name = "T" + name
    res = supabase.table("training_sets").select("*").eq("name", name).execute()
    if res.data:
        return res.data[0]["id"]
    supabase.table("training_sets").insert({"name": name}).execute()
    res2 = supabase.table("training_sets").select("*").eq("name", name).execute()
    return res2.data[0]["id"]

def get_persons():
    res = supabase.table("persons").select("*").execute()
    return pd.DataFrame(res.data)

def get_sets():
    res = supabase.table("training_sets").select("*").execute()
    return pd.DataFrame(res.data)

def get_sessions():
    sessions_res = supabase.table("sessions").select("*").execute()
    sessions = sessions_res.data
    result = []
    for s in sessions:
        ts_res = supabase.table("training_sets").select("*").eq("id", s["training_set_id"]).execute()
        ts_name = ts_res.data[0]["name"] if ts_res.data else ""
        att_res = supabase.table("attendance").select("*").eq("session_id", s["id"]).execute()
        attendees = []
        for a in att_res.data:
            p_res = supabase.table("persons").select("*").eq("id", a["person_id"]).execute()
            if p_res.data:
                attendees.append(p_res.data[0]["name"])
        result.append({
            "id": s["id"],
            "date": s["date"],
            "training_set": ts_name,
            "attendees": ", ".join(attendees)
        })
    return pd.DataFrame(result)

# -------------------------
# UI
# -------------------------
st.title("Fitness Training Scheduler")
tab1, tab2, tab3 = st.tabs(["Recommend Training","Training Sessions","Statistics"])

# =========================================================
# TAB 1 — RECOMMEND
# =========================================================
with tab1:
    persons_df = get_persons()
    sets_df = get_sets()
    selected_people = st.multiselect("Select attendees", persons_df["name"] if not persons_df.empty else [])

    if st.button("Get Recommendations"):
        if not selected_people:
            st.warning("Select at least one person")
            st.stop()
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
            results.append((s["name"], seen_count))
        results.sort(key=lambda x: x[1])
        for name, seen in results:
            if seen == 0:
                st.write(f"🟢 {name} (NEW)")
            else:
                st.write(f"{name} (seen by {seen})")

# =========================================================
# TAB 2 — TRAINING SESSIONS
# =========================================================
with tab2:
    st.header("Training Sessions")
    persons_df = get_persons()
    sets_df = get_sets()

    # -------------------------
    # ADD SESSION
    # -------------------------
    st.subheader("Add New Session")
    d = st.date_input("Date", value=date.today())
    set_name = st.text_input("Training set (T1...)")
    attendees = st.multiselect("Attendees", persons_df["name"])
    new_people_input = st.text_input("Add new persons (comma separated)")
    attendees.extend(parse_names(new_people_input))

    if st.button("Add Session"):
        set_id = get_or_create_set(set_name)
        sess_res = supabase.table("sessions").insert({"date": d.isoformat(), "training_set_id": set_id}).execute()
        sid = sess_res.data[0]["id"]
        for name in attendees:
            pid = get_or_create_person(name)
            supabase.table("attendance").insert({"session_id": sid, "person_id": pid}).execute()
        st.success("Session added")
        st.experimental_rerun()

    # -------------------------
    # IMPORT EXCEL
    # -------------------------
    st.subheader("Import Excel")
    file = st.file_uploader("Upload Excel", type=["xlsx"])
    if file:
        df = pd.read_excel(file)
        st.dataframe(df)
        if st.button("Import Data"):
            for _, row in df.iterrows():
                session_date = pd.to_datetime(row["date"]).date().isoformat()
                set_id = get_or_create_set(str(row["training_set"]))
                sess_res = supabase.table("sessions").insert({"date": session_date, "training_set_id": set_id}).execute()
                sid = sess_res.data[0]["id"]
                names = parse_names(str(row["attendees"]))
                for n in names:
                    pid = get_or_create_person(n)
                    supabase.table("attendance").insert({"session_id": sid, "person_id": pid}).execute()
            st.success("Imported")
            st.experimental_rerun()

    # -------------------------
    # FILTERS
    # -------------------------
    st.subheader("Filters")
    filter_person = st.selectbox("Filter by person", ["All"] + persons_df["name"].tolist())
    filter_set = st.selectbox("Filter by training set", ["All"] + sets_df["name"].tolist())
    start_date = st.date_input("From date", value=date(2024,1,1))
    end_date = st.date_input("To date", value=date.today())

    sessions_df = get_sessions()
    mask = (pd.to_datetime(sessions_df["date"]) >= pd.to_datetime(start_date)) & (pd.to_datetime(sessions_df["date"]) <= pd.to_datetime(end_date))
    if filter_person != "All":
        mask &= sessions_df["attendees"].str.contains(filter_person)
    if filter_set != "All":
        mask &= sessions_df["training_set"] == filter_set
    sessions_df = sessions_df[mask]
    st.dataframe(sessions_df)

    # -------------------------
    # VIEW / EDIT / DELETE
    # -------------------------
    if not sessions_df.empty:
        selected_id = st.selectbox("Select session", sessions_df["id"])
        session = sessions_df[sessions_df["id"] == selected_id].iloc[0]
        edit_date = st.date_input("Edit date", value=datetime.strptime(session["date"], "%Y-%m-%d"))
        edit_set = st.text_input("Edit training set", value=session["training_set"])
        current_attendees = session["attendees"].split(",") if session["attendees"] else []
        edit_attendees = st.multiselect("Edit attendees", get_persons()["name"], default=current_attendees)
        edit_attendees.extend(parse_names(st.text_input("Add new persons (edit)")))

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Session"):
                set_id = get_or_create_set(edit_set)
                supabase.table("sessions").update({"date": edit_date.isoformat(), "training_set_id": set_id}).eq("id", selected_id).execute()
                supabase.table("attendance").delete().eq("session_id", selected_id).execute()
                for name in edit_attendees:
                    pid = get_or_create_person(name)
                    supabase.table("attendance").insert({"session_id": selected_id, "person_id": pid}).execute()
                st.success("Updated")
                st.experimental_rerun()
        with col2:
            if st.button("Delete Session"):
                supabase.table("attendance").delete().eq("session_id", selected_id).execute()
                supabase.table("sessions").delete().eq("id", selected_id).execute()
                st.success("Deleted")
                st.experimental_rerun()

    # -------------------------
    # MANAGE PERSONS
    # -------------------------
    st.subheader("Manage Persons")
    st.dataframe(persons_df)

    if not persons_df.empty:
        selected_person = st.selectbox("Select person", persons_df["id"])
        new_name = st.text_input("Rename to")
        if st.button("Rename Person"):
            supabase.table("persons").update({"name": new_name.strip()}).eq("id", selected_person).execute()
            st.experimental_rerun()
        if st.button("Delete Person"):
            supabase.table("attendance").delete().eq("person_id", selected_person).execute()
            supabase.table("persons").delete().eq("id", selected_person).execute()
            st.experimental_rerun()
        st.subheader("Merge Persons")
        source = st.selectbox("Source (delete)", persons_df["id"], key="m1")
        target = st.selectbox("Target (keep)", persons_df["id"], key="m2")
        if st.button("Merge"):
            if source != target:
                supabase.table("attendance").update({"person_id": target}).eq("person_id", source).execute()
                # Remove duplicates
                all_att = supabase.table("attendance").select("*").execute().data
                unique = {}
                for a in all_att:
                    key = (a["session_id"], a["person_id"])
                    if key in unique:
                        supabase.table("attendance").delete().eq("session_id", a["session_id"]).eq("person_id", a["person_id"]).execute()
                    else:
                        unique[key] = True
                supabase.table("persons").delete().eq("id", source).execute()
                st.success("Merged")
                st.experimental_rerun()

# =========================================================
# TAB 3 — STATISTICS
# =========================================================
with tab3:
    st.header("Statistics Dashboard")
    persons_df = get_persons()

    st.subheader("Person History")
    person_name = st.selectbox("Select person", persons_df["name"] if not persons_df.empty else [])
    if person_name:
        sessions = get_sessions()
        df = sessions[sessions["attendees"].str.contains(person_name)]
        df_plot = df[["date", "training_set"]]
        st.dataframe(df_plot)
        if not df_plot.empty:
            freq = df_plot["training_set"].value_counts()
            fig, ax = plt.subplots()
            freq.plot(kind="bar", ax=ax)
            st.pyplot(fig)

    st.subheader("Training Set Usage")
    sessions = get_sessions()
    df_sets = sessions[["date", "training_set"]]
    st.dataframe(df_sets)
    if not df_sets.empty:
        freq = df_sets["training_set"].value_counts()
        fig, ax = plt.subplots()
        freq.plot(kind="bar", ax=ax)
        st.pyplot(fig)
        df_sets["date"] = pd.to_datetime(df_sets["date"])
        timeline = df_sets.groupby("date").size()
        fig2, ax2 = plt.subplots()
        timeline.plot(ax=ax2)
        st.pyplot(fig2)