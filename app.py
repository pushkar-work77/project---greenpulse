
import streamlit as st
import json
import os
from datetime import date, datetime
import pandas as pd

# ================= FILE PATHS =================
TREE_DB = "trees.json"
USER_DB = "users.json"

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Urban Forest Survival Tracker",
    page_icon="🌳",
    layout="wide"
)

# ================= UI STYLE =================
st.markdown("""
<style>
body {background-color:#e6e6e6;}
.stButton>button {
    background-color:#00695c;
    color:white;
    border-radius:8px;
    padding:8px 16px;
    border:none;
}
.stButton>button:hover {
    background-color:#004d40;
}
</style>
""", unsafe_allow_html=True)

# ================= SAFE RERUN =================
def safe_rerun():
    try:
        st.rerun()
    except:
        pass

# ================= DATA FUNCTIONS =================
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

# ================= LOAD DATA =================
trees = load_json(TREE_DB)
users = load_json(USER_DB)

# ================= SESSION STATE =================
if "user" not in st.session_state:
    st.session_state.user = None

if "page" not in st.session_state:
    st.session_state.page = "login"   # login | register | app

# =====================================================
#                     LOGIN PAGE
# =====================================================
def login_flow():
    st.title("🌳 Urban Forest Survival System")
    st.subheader("Login")

    users = load_json(USER_DB)

    if not users:
        st.info("No users found. Please register first.")
        if st.button("Create New Account"):
            st.session_state.page = "register"
            safe_rerun()
        return

    names = [u["name"] for u in users]
    selected = st.selectbox("Select User", names)

    col1, col2 = st.columns(2)

    if col1.button("Login"):
        st.session_state.user = next(u for u in users if u["name"] == selected)
        st.session_state.page = "app"
        safe_rerun()

    if col2.button("New Registration"):
        st.session_state.page = "register"
        safe_rerun()

# =====================================================
#                  REGISTRATION PAGE
# =====================================================
def registration_flow():
    st.title("🌱 New User Registration")

    name = st.text_input("Full Name")
    role = st.selectbox("Role", ["Volunteer", "Government Authority"])
    ward = st.text_input("Ward")
    location = st.text_input("Location (Must include Nashik)")

    col1, col2 = st.columns(2)

    if col1.button("⬅ Back to Login"):
        st.session_state.page = "login"
        safe_rerun()

    if col2.button("Register"):
        if not name:
            st.warning("Please enter your name")
            return

        if "nashik" not in location.lower():
            st.error("Location must be Nashik")
            return

        users = load_json(USER_DB)

        if any(u["name"] == name for u in users):
            st.error("User already exists. Please login.")
            return

        new_user = {
            "name": name,
            "role": role,
            "ward": ward if ward else "Unknown",
            "location": location
        }

        users.append(new_user)
        save_json(USER_DB, users)

        st.session_state.user = new_user
        st.session_state.page = "app"

        st.success("Registration successful!")
        safe_rerun()

# =====================================================
#                    MAIN APP
# =====================================================
def main_app():
    st.title("🌳 Urban Forest Survival Tracker — Nashik")

    menu = st.sidebar.selectbox(
        "Menu",
        ["Dashboard", "Register Tree", "Edit/Delete Tree",
         "Update Status", "Map View", "Authority Summary",
         "Export Report", "Logout"]
    )

    # ---------- DASHBOARD ----------
    if menu == "Dashboard":
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

    # ---------- REGISTER TREE ----------
    elif menu == "Register Tree":
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
            safe_rerun()

    # ---------- EDIT DELETE ----------
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

    # ---------- UPDATE STATUS ----------
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

    # ---------- MAP ----------
    elif menu == "Map View":
        if trees:
            df = pd.DataFrame(trees)
            if "latitude" in df and "longitude" in df:
                st.map(df[["latitude", "longitude"]])

    # ---------- AUTHORITY SUMMARY ----------
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

    # ---------- EXPORT ----------
    elif menu == "Export Report":
        if trees:
            df = pd.DataFrame(trees)
            csv = df.to_csv(index=False).encode()
            st.download_button("Download Report", csv, "nashik_report.csv")

    # ---------- LOGOUT ----------
    elif menu == "Logout":
        st.session_state.user = None
        st.session_state.page = "login"
        safe_rerun()

# =====================================================
#                   APP ENTRY
# =====================================================
if st.session_state.page == "login":
    login_flow()

elif st.session_state.page == "register":
    registration_flow()

elif st.session_state.page == "app":
    main_app()

