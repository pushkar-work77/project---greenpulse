
import streamlit as st
import json
import os
from datetime import date, datetime
import pandas as pd

# ---------------- SAFE RERUN ----------------
def safe_rerun():
    try:
        st.rerun()
    except:
        pass

# ---------------- FILE PATHS ----------------
TREE_DB = "trees.json"
USER_DB = "users.json"

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Urban Forest Survival Tracker",
    page_icon="🌳",
    layout="wide"
)

# ---------------- GOVERNMENT STYLE UI ----------------
st.markdown("""
<style>
body {background-color:#e6e6e6;}
.main {background-color:#e6e6e6;}
.stButton>button {
    background-color:#00695c;
    color:white;
    border-radius:8px;
    padding:8px 16px;
    border:none;
}
.stButton>button:hover {
    background-color:#004d40;
    color:white;
}
.card {
    padding:15px;
    border-radius:10px;
    background:white;
    box-shadow:0 2px 6px rgba(0,0,0,0.2);
    margin-bottom:10px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATA FUNCTIONS ----------------
def load_json(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return []

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def days_since_update(d):
    try:
        last = datetime.strptime(d, "%Y-%m-%d").date()
        return (date.today() - last).days
    except:
        return 999

trees = load_json(TREE_DB)
users = load_json(USER_DB)

# ---------------- SESSION STATE ----------------
if "user" not in st.session_state:
    st.session_state.user = None

if "reg_step" not in st.session_state:
    st.session_state.reg_step = 1

# =====================================================
#                 USER AUTHENTICATION
# =====================================================

def registration_flow():
    st.title("🌳 Nashik Urban Forest System")

    step = st.session_state.reg_step

    # STEP 1
    if step == 1:
        st.subheader("User Information")

        name = st.text_input("Full Name")
        role = st.selectbox("Role", ["Volunteer", "Government Authority"])

        col1, col2 = st.columns(2)
        if col2.button("Next ➜"):
            if name:
                st.session_state.reg_name = name
                st.session_state.reg_role = role
                st.session_state.reg_step = 2
                safe_rerun()
            else:
                st.warning("Enter name")

    # STEP 2
    elif step == 2:
        st.subheader("Location Details")

        ward = st.text_input("Ward")
        location = st.text_input("Location (Must be Nashik)")

        col1, col2 = st.columns(2)
        if col1.button("⬅ Back"):
            st.session_state.reg_step = 1
            safe_rerun()

        if col2.button("Register"):
            if "nashik" in location.lower():
                user = {
                    "name": st.session_state.reg_name,
                    "role": st.session_state.reg_role,
                    "ward": ward,
                    "location": location
                }
                users.append(user)
                save_json(USER_DB, users)

                st.session_state.user = user
                st.session_state.reg_step = 1
                st.success("Registration Successful")
                safe_rerun()
            else:
                st.error("Location must be Nashik")

def login_flow():
    st.title("🌳 Urban Forest Login")

    names = [u["name"] for u in users]

    if not names:
        st.info("No users registered. Please register.")
        registration_flow()
        return

    name = st.selectbox("Select User", names)

    col1, col2 = st.columns(2)
    if col1.button("Login"):
        st.session_state.user = next(u for u in users if u["name"] == name)
        safe_rerun()

    if col2.button("New Registration"):
        registration_flow()

# =====================================================
#                    MAIN APP
# =====================================================

def main_app():
    st.title("🌳 Urban Forest Survival Tracker — Nashik")

    menu = st.sidebar.selectbox(
        "Menu",
        ["Dashboard", "Register Tree", "Edit/Delete Tree",
         "Update Status", "Map View", "Leaderboard",
         "Authority Summary", "Export Report", "Logout"]
    )

    # ---------------- DASHBOARD ----------------
    if menu == "Dashboard":
        st.subheader("City Overview")

        total = len(trees)
        healthy = sum(1 for t in trees if t.get("status") == "Healthy")
        dead = sum(1 for t in trees if t.get("status") == "Dead")

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Trees", total)
        c2.metric("Healthy", healthy)
        c3.metric("Dead", dead)

        if trees:
            df = pd.DataFrame(trees)
            st.bar_chart(df["status"].value_counts())

    # ---------------- REGISTER TREE ----------------
    elif menu == "Register Tree":
        st.subheader("Register New Tree")

        ward = st.text_input("Ward")
        location = st.text_input("Location")
        species = st.text_input("Species")

        lat = st.number_input("Latitude", format="%.6f")
        lon = st.number_input("Longitude", format="%.6f")

        if st.button("Register"):
            tree = {
                "id": len(trees) + 1,
                "ward": ward,
                "location": location,
                "species": species,
                "latitude": lat,
                "longitude": lon,
                "status": "Healthy",
                "last_updated": str(date.today())
            }
            trees.append(tree)
            save_json(TREE_DB, trees)
            st.success("Tree Registered")

    # ---------------- EDIT DELETE ----------------
    elif menu == "Edit/Delete Tree":
        if not trees:
            st.info("No trees available")
            return

        ids = [t["id"] for t in trees]
        selected = st.selectbox("Select Tree", ids)
        tree = next(t for t in trees if t["id"] == selected)

        ward = st.text_input("Ward", tree["ward"])
        location = st.text_input("Location", tree["location"])

        col1, col2 = st.columns(2)
        if col1.button("Save"):
            tree["ward"] = ward
            tree["location"] = location
            tree["last_updated"] = str(date.today())
            save_json(TREE_DB, trees)
            st.success("Updated")
            safe_rerun()

        if col2.button("Delete"):
            trees.remove(tree)
            save_json(TREE_DB, trees)
            st.warning("Deleted")
            safe_rerun()

    # ---------------- UPDATE STATUS ----------------
    elif menu == "Update Status":
        if not trees:
            st.info("No trees available")
            return

        ids = [t["id"] for t in trees]
        selected = st.selectbox("Tree ID", ids)
        status = st.selectbox("Status", ["Healthy", "Needs Water", "Dead"])

        if st.button("Update"):
            for t in trees:
                if t["id"] == selected:
                    t["status"] = status
                    t["last_updated"] = str(date.today())
            save_json(TREE_DB, trees)
            st.success("Updated")

    # ---------------- MAP ----------------
    elif menu == "Map View":
        if trees:
            df = pd.DataFrame(trees)
            if "latitude" in df and "longitude" in df:
                st.map(df[["latitude", "longitude"]])

    # ---------------- LEADERBOARD ----------------
    elif menu == "Leaderboard":
        if trees:
            df = pd.DataFrame(trees)
            st.bar_chart(df["ward"].value_counts())

    # ---------------- AUTHORITY SUMMARY ----------------
    elif menu == "Authority Summary":
        if not trees:
            st.info("No data")
            return

        df = pd.DataFrame(trees)
        ward_summary = df.groupby("ward").agg(
            Total=("id", "count"),
            Healthy=("status", lambda x: (x == "Healthy").sum())
        )
        ward_summary["Survival %"] = (ward_summary["Healthy"] / ward_summary["Total"]) * 100
        st.dataframe(ward_summary)
        st.bar_chart(ward_summary["Survival %"])

    # ---------------- EXPORT ----------------
    elif menu == "Export Report":
        if trees:
            df = pd.DataFrame(trees)
            csv = df.to_csv(index=False).encode()
            st.download_button("Download Report", csv, "nashik_report.csv")

    # ---------------- LOGOUT ----------------
    elif menu == "Logout":
        st.session_state.user = None
        safe_rerun()

# =====================================================
#                   APP ENTRY POINT
# =====================================================

if st.session_state.user is None:
    login_flow()
else:
    main_app()

