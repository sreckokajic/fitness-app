import streamlit as st

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

import sqlite3
from datetime import datetime, timedelta, date
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------
# DATABASE
# -------------------------
import psycopg2

conn = psycopg2.connect(
    host="db.pjeomsygofqwfjtyybzy.supabase.co",
    database="postgres",
    user="postgres",
    password="reformerpilates2026",
    port="5432"
)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS persons(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT UNIQUE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS training_sets(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT UNIQUE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS sessions(
id INTEGER PRIMARY KEY AUTOINCREMENT,
date TEXT,
training_set_id INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance(
session_id INTEGER,
person_id INTEGER
)
""")

conn.commit()

# -------------------------
# HELPERS
# -------------------------

def parse_names(input_text):
    if not input_text:
        return []
    return [n.strip() for n in input_text.split(",") if n.strip()]


def get_or_create_person(name):
    name = name.strip()

    cursor.execute("SELECT id FROM persons WHERE name=?", (name,))
    res = cursor.fetchone()

    if res:
        return res[0]

    cursor.execute("INSERT INTO persons(name) VALUES (?)", (name,))
    conn.commit()
    return cursor.lastrowid


def get_or_create_set(name):
    name = name.strip().upper()

    if not name.startswith("T"):
        name = "T" + name

    cursor.execute("SELECT id FROM training_sets WHERE name=?", (name,))
    res = cursor.fetchone()

    if res:
        return res[0]

    cursor.execute("INSERT INTO training_sets(name) VALUES (?)", (name,))
    conn.commit()
    return cursor.lastrowid


def get_persons():
    return pd.read_sql("SELECT * FROM persons", conn)


def get_sets():
    return pd.read_sql("SELECT * FROM training_sets", conn)


def get_sessions():
    return pd.read_sql("""
    SELECT 
        s.id,
        s.date,
        t.name as training_set,
        GROUP_CONCAT(p.name) as attendees
    FROM sessions s
    LEFT JOIN training_sets t ON s.training_set_id = t.id
    LEFT JOIN attendance a ON s.id = a.session_id
    LEFT JOIN persons p ON a.person_id = p.id
    GROUP BY s.id
    ORDER BY s.date DESC
    """, conn)


# -------------------------
# UI
# -------------------------

st.title("Fitness Training Scheduler")

tab1, tab2, tab3 = st.tabs([
    "Recommend Training",
    "Training Sessions",
    "Statistics"
])

# =========================================================
# TAB 1 — RECOMMEND
# =========================================================

with tab1:

    persons_df = get_persons()
    sets_df = get_sets()

    selected_people = st.multiselect(
        "Select attendees",
        persons_df["name"] if not persons_df.empty else []
    )

    if st.button("Get Recommendations"):

        if not selected_people:
            st.warning("Select at least one person")
            st.stop()

        selected_ids = persons_df[
            persons_df["name"].isin(selected_people)
        ]["id"].tolist()

        cutoff = (datetime.today() - timedelta(days=45)).date().isoformat()

        results = []

        for _, s in sets_df.iterrows():

            cursor.execute("""
            SELECT DISTINCT a.person_id
            FROM sessions s
            JOIN attendance a ON s.id = a.session_id
            WHERE s.training_set_id = ?
            AND s.date >= ?
            """, (s["id"], cutoff))

            seen_people = {r[0] for r in cursor.fetchall()}

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

    # -------------------------
    # ADD SESSION
    # -------------------------

    st.subheader("Add New Session")

    d = st.date_input("Date", value=date.today())
    set_name = st.text_input("Training set (T1...)")

    attendees = st.multiselect(
        "Attendees",
        persons_df["name"]
    )

    # ✅ NEW: multiple new persons
    new_people_input = st.text_input("Add new persons (comma separated)")
    attendees.extend(parse_names(new_people_input))

    if st.button("Add Session"):

        set_id = get_or_create_set(set_name)

        cursor.execute(
            "INSERT INTO sessions(date,training_set_id) VALUES (?,?)",
            (d.isoformat(), set_id)
        )

        sid = cursor.lastrowid

        for name in attendees:
            pid = get_or_create_person(name)
            cursor.execute(
                "INSERT INTO attendance VALUES (?,?)",
                (sid, pid)
            )

        conn.commit()
        st.success("Session added")
        st.rerun()

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

                cursor.execute(
                    "INSERT INTO sessions(date,training_set_id) VALUES (?,?)",
                    (session_date, set_id)
                )

                sid = cursor.lastrowid

                names = parse_names(str(row["attendees"]))

                for n in names:
                    pid = get_or_create_person(n)
                    cursor.execute(
                        "INSERT INTO attendance VALUES (?,?)",
                        (sid, pid)
                    )

            conn.commit()
            st.success("Imported")
            st.rerun()

    # -------------------------
    # FILTERS (ADDED ONLY)
    # -------------------------

    st.subheader("Filters")

    sets_df = get_sets()

    filter_person = st.selectbox(
        "Filter by person",
        ["All"] + persons_df["name"].tolist()
    )

    filter_set = st.selectbox(
        "Filter by training set",
        ["All"] + sets_df["name"].tolist()
    )

    start_date = st.date_input("From date", value=date(2024, 1, 1))
    end_date = st.date_input("To date", value=date.today())

    # -------------------------
    # VIEW / EDIT / DELETE
    # -------------------------

    st.subheader("View, Edit & Delete Sessions")

    query = """
    SELECT 
        s.id,
        s.date,
        t.name as training_set,
        GROUP_CONCAT(p.name) as attendees
    FROM sessions s
    LEFT JOIN training_sets t ON s.training_set_id = t.id
    LEFT JOIN attendance a ON s.id = a.session_id
    LEFT JOIN persons p ON a.person_id = p.id
    WHERE s.date BETWEEN ? AND ?
    """

    params = [start_date.isoformat(), end_date.isoformat()]

    if filter_person != "All":
        query += " AND p.name = ?"
        params.append(filter_person)

    if filter_set != "All":
        query += " AND t.name = ?"
        params.append(filter_set)

    query += " GROUP BY s.id ORDER BY s.date DESC"

    sessions_df = pd.read_sql(query, conn, params=params)

    st.dataframe(sessions_df)

    if not sessions_df.empty:

        selected_id = st.selectbox("Select session", sessions_df["id"])

        session = sessions_df[sessions_df["id"] == selected_id].iloc[0]

        edit_date = st.date_input(
            "Edit date",
            value=datetime.strptime(session["date"], "%Y-%m-%d")
        )

        edit_set = st.text_input(
            "Edit training set",
            value=session["training_set"]
        )

        current_attendees = session["attendees"].split(",") if session["attendees"] else []

        edit_attendees = st.multiselect(
            "Edit attendees",
            get_persons()["name"],
            default=current_attendees
        )

        # ✅ NEW here too
        edit_attendees.extend(parse_names(
            st.text_input("Add new persons (edit)")
        ))

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Update Session"):

                set_id = get_or_create_set(edit_set)

                cursor.execute(
                    "UPDATE sessions SET date=?, training_set_id=? WHERE id=?",
                    (edit_date.isoformat(), set_id, selected_id)
                )

                cursor.execute(
                    "DELETE FROM attendance WHERE session_id=?",
                    (selected_id,)
                )

                for name in edit_attendees:
                    pid = get_or_create_person(name)
                    cursor.execute(
                        "INSERT INTO attendance VALUES (?,?)",
                        (selected_id, pid)
                    )

                conn.commit()
                st.success("Updated")
                st.rerun()

        with col2:
            if st.button("Delete Session"):

                cursor.execute(
                    "DELETE FROM attendance WHERE session_id=?",
                    (selected_id,)
                )

                cursor.execute(
                    "DELETE FROM sessions WHERE id=?",
                    (selected_id,)
                )

                conn.commit()
                st.success("Deleted")
                st.rerun()

    # -------------------------
    # MANAGE PERSONS (UNCHANGED)
    # -------------------------

    st.subheader("Manage Persons")

    st.dataframe(persons_df)

    if not persons_df.empty:

        selected_person = st.selectbox("Select person", persons_df["id"])

        new_name = st.text_input("Rename to")

        if st.button("Rename Person"):
            cursor.execute(
                "UPDATE persons SET name=? WHERE id=?",
                (new_name.strip(), selected_person)
            )
            conn.commit()
            st.rerun()

        if st.button("Delete Person"):

            cursor.execute(
                "DELETE FROM attendance WHERE person_id=?",
                (selected_person,)
            )

            cursor.execute(
                "DELETE FROM persons WHERE id=?",
                (selected_person,)
            )

            conn.commit()
            st.rerun()

        st.subheader("Merge Persons")

        source = st.selectbox("Source (delete)", persons_df["id"], key="m1")
        target = st.selectbox("Target (keep)", persons_df["id"], key="m2")

        if st.button("Merge"):

            if source != target:

                cursor.execute("""
                UPDATE attendance
                SET person_id=?
                WHERE person_id=?
                """, (target, source))

                cursor.execute("""
                DELETE FROM attendance
                WHERE rowid NOT IN (
                    SELECT MIN(rowid)
                    FROM attendance
                    GROUP BY session_id, person_id
                )
                """)

                cursor.execute(
                    "DELETE FROM persons WHERE id=?",
                    (source,)
                )

                conn.commit()
                st.success("Merged")
                st.rerun()

# =========================================================
# TAB 3 — STATISTICS (UNCHANGED)
# =========================================================

with tab3:

    st.header("Statistics Dashboard")

    persons_df = get_persons()

    st.subheader("Person History")

    person_name = st.selectbox(
        "Select person",
        persons_df["name"] if not persons_df.empty else []
    )

    if person_name:

        df = pd.read_sql(f"""
        SELECT s.date, t.name as training_set
        FROM sessions s
        JOIN attendance a ON s.id = a.session_id
        JOIN persons p ON a.person_id = p.id
        JOIN training_sets t ON s.training_set_id = t.id
        WHERE p.name = '{person_name}'
        ORDER BY s.date DESC
        """, conn)

        st.dataframe(df)

        if not df.empty:
            freq = df["training_set"].value_counts()

            fig, ax = plt.subplots()
            freq.plot(kind="bar", ax=ax)
            st.pyplot(fig)

    st.subheader("Training Set Usage")

    df_sets = pd.read_sql("""
    SELECT s.date, t.name as training_set
    FROM sessions s
    JOIN training_sets t ON s.training_set_id = t.id
    ORDER BY s.date
    """, conn)

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