
import streamlit as st
import json
import os
from datetime import date, datetime
import pandas as pd

# ---------------- APP CONFIG ----------------
st.set_page_config(
    page_title="Nashik Urban Forest Monitoring System",
    page_icon="🌿",
    layout="wide"
)

TREES_FILE = "trees.json"
USERS_FILE = "users.json"

# ---------------- HELPER FUNCTIONS ----------------
def load_json(file):
    if not os.path.exists(file):
        return []
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        # file corrupted or bad format
        return []

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def safe_days(d):
    try:
        last = datetime.strptime(d, "%Y-%m-%d").date()
        return (date.today() - last).days
    except:
        return 999

def valid_nashik_loc(loc):
    if not loc:
        return False
    allowed = [
        "nashik", "nashik road", "mhasrul", "cidco",
        "panchavati", "satpur", "ambad", "gangapur"
    ]
    loc = loc.lower()
    return any(k in loc for k in allowed)

def ai_survival(tree):
    score = 50
    if tree.get("status") == "Healthy":
        score += 20
    if safe_days(tree.get("last_updated")) < 7:
        score += 15
    score += (tree.get("soil_score", 50) - 50) * 0.2
    score += (tree.get("rainfall", 50) - 50) * 0.2
    return round(min(max(score, 0), 100), 2)

# ---------------- LOAD DATA ----------------
trees = load_json(TREES_FILE)
users = load_json(USERS_FILE)

# ---------------- NATURE THEME + COLOR FIX ----------------
st.markdown("""
<style>

/* APP BACKGROUND */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(to bottom, #d0f0c0, #b8e0c0);
}

/* HEADER CARD */
#header {
    background: #2a6f4f;
    color: white;
    padding: 15px;
    border-radius: 8px;
    text-align: center;
    font-weight: bold;
}

/* BUTTONS */
.stButton > button {
    background-color: #2a6f4f;
    color: white;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: bold;
}
.stButton > button:hover {
    background-color: #1f5a3d;
    color: white;
}

/* INPUTS */
.stTextInput input, .stNumberInput input {
    background-color: white;
    color: black;
    border-radius: 6px;
}

/* TABLE BACKGROUND */
table {
    background-color: white !important;
    color: black !important;
}

</style>
""", unsafe_allow_html=True)

# ---------------- TUTORIAL FIRST TIME ----------------
if "tutorial_seen" not in st.session_state:
    st.markdown('<div id="header"><h2>🌳 Nashik Urban Forest Monitoring — Tutorial</h2></div>', unsafe_allow_html=True)
    st.markdown("""
Welcome to your Urban Forest Monitoring System for Nashik!

This tutorial will guide you through:

🔹 Registering as a Nashik user  
🔹 Adding trees to monitor  
🔹 Updating tree health  
🔹 Viewing analytics dashboard  
🔹 Creating professional authority reports  
🔹 Exporting data for stakeholders

Click **Continue** to begin your journey.

You can also **Skip** the tutorial and proceed directly.
""")

    col1, col2 = st.columns(2)
    if col1.button("Continue Tutorial"):
        st.session_state["tutorial_seen"] = True
        st.rerun()
    if col2.button("Skip Tutorial"):
        st.session_state["tutorial_seen"] = True
        st.rerun()
    st.stop()

# ---------------- USER LOGIN/REGISTER ----------------
if "user" not in st.session_state:

    st.subheader("👤 User Registration / Login")

    tab1, tab2 = st.tabs(["Login","Register"])

    with tab1:
        uname = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        if st.button("Log In"):
            user = next((u for u in users if u["username"] == uname and u["password"] == pwd), None)
            if user:
                st.session_state["user"] = user
                st.success("Logged in successfully")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

    with tab2:
        name = st.text_input("Full Name")
        uname_new = st.text_input("Create Username")
        pwd_new = st.text_input("Create Password",type="password")
        ward_new = st.text_input("Your Ward")
        loc_new = st.text_input("Your Location (Must be Nashik)")
        role_new = st.selectbox("I am a",["Volunteer","Government Authority"])
        contact_new = st.text_input("Contact Number")

        if st.button("Register"):
            if not valid_nashik_loc(loc_new):
                st.error("Location must be Nashik region")
            elif any(u["username"]==uname_new for u in users):
                st.warning("Username already exists")
            else:
                new_user = {
                    "name":name,
                    "username":uname_new,
                    "password":pwd_new,
                    "ward":ward_new,
                    "location":loc_new,
                    "role":role_new,
                    "contact":contact_new
                }
                users.append(new_user)
                save_json(USERS_FILE,users)
                st.success("Registration successful! Please log in.")
    st.stop()

# ---------------- MAIN NAVIGATION ----------------
menu = st.sidebar.selectbox(
    "Navigate",
    ["Dashboard","Register Tree","Edit Tree",
     "Update Tree Status","Map View",
     "Authority Report","Export Report","App Manual"]
)

current_user = st.session_state["user"]

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":

    st.markdown('<h3>📊 Dashboard Overview</h3>', unsafe_allow_html=True)

    total = len(trees)
    healthy = sum(1 for t in trees if t.get("status")=="Healthy")
    survival_rate = round((healthy/total)*100,2) if total else 0

    c1,c2 = st.columns(2)
    c1.metric("Total Trees",total)
    c2.metric("Survival %",survival_rate)

    if trees:
        df = pd.DataFrame(trees)
        df["AI Survival %"] = df.apply(ai_survival,axis=1)
        st.dataframe(df)

# ---------------- REGISTER TREE ----------------
elif menu == "Register Tree":

    st.markdown("<h3>🌱 Register New Tree</h3>", unsafe_allow_html=True)

    ward = st.text_input("Ward")
    loc = st.text_input("Location (Nashik)")
    species = st.text_input("Species")
    nutrients = st.text_input("Nutrients / Minerals")
    temp_range = st.text_input("Suitable Temp Range (°C)")
    soil_score = st.slider("Soil Health Score",0,100,50)
    rainfall = st.slider("Rainfall Impact",0,100,50)

    lat = st.number_input("Latitude",format="%.6f")
    lon = st.number_input("Longitude",format="%.6f")

    if st.button("Add Tree"):
        if not valid_nashik_loc(loc):
            st.error("Tree location must be within Nashik")
        else:
            trees.append({
                "id":len(trees)+1,
                "ward":ward,
                "location":loc,
                "species":species,
                "nutrients":nutrients,
                "temperature":temp_range,
                "soil_score":soil_score,
                "rainfall":rainfall,
                "latitude":lat,
                "longitude":lon,
                "status":"Healthy",
                "last_updated":str(date.today()),
                "registered_by":current_user["username"]
            })
            save_json(TREES_FILE,trees)
            st.success("Tree registered successfully")

# ---------------- EDIT TREE ----------------
elif menu == "Edit Tree":

    if trees:
        st.markdown("<h3>✏️ Edit Tree Record</h3>", unsafe_allow_html=True)
        tree_id = st.selectbox("Select Tree",[t["id"] for t in trees])
        tree = next(t for t in trees if t["id"]==tree_id)

        new_status = st.selectbox("Status",["Healthy","Needs Water","Dead"])
        new_soil = st.slider("Soil Score",0,100,int(tree.get("soil_score",50)))
        new_rain = st.slider("Rainfall Impact",0,100,int(tree.get("rainfall",50)))

        if st.button("Update Tree"):
            tree["status"]=new_status
            tree["soil_score"]=new_soil
            tree["rainfall"]=new_rain
            tree["last_updated"]=str(date.today())
            save_json(TREES_FILE,trees)
            st.success("Updated")

# ---------------- UPDATE TREE STATUS ----------------
elif menu == "Update Tree Status":

    if trees:
        tree_id = st.selectbox("Select Tree",[t["id"] for t in trees])
        new_status = st.selectbox("Status",["Healthy","Needs Water","Dead"])
        if st.button("Update Status"):
            for t in trees:
                if t["id"]==tree_id:
                    t["status"]=new_status
                    t["last_updated"]=str(date.today())
            save_json(TREES_FILE,trees)
            st.success("Status Updated")

# ---------------- MAP VIEW ----------------
elif menu == "Map View":
    if trees:
        df = pd.DataFrame(trees)
        if "latitude" in df and "longitude" in df:
            st.map(df[["latitude","longitude"]].dropna())

# ---------------- AUTHORITY REPORT ----------------
elif menu == "Authority Report":

    st.markdown("<h3>🏛 Authority Environmental Report</h3>", unsafe_allow_html=True)

    if trees:
        df = pd.DataFrame(trees)

        ward_summary = df.groupby("ward").agg(
            Total=("id","count"),
            Avg_Soil=("soil_score","mean"),
            Avg_Rainfall=("rainfall","mean"),
            Healthy=("status", lambda x:(x=="Healthy").sum())
        ).reset_index()

        ward_summary["Survival %"] = round((ward_summary["Healthy"]/ward_summary["Total"])*100,2)
        ward_summary["Risk Level"] = ward_summary["Survival %"].apply(
            lambda x:"High Risk" if x<50 else "Moderate" if x<75 else "Healthy"
        )

        st.dataframe(ward_summary)
        st.bar_chart(ward_summary.set_index("ward")["Survival %"])

# ---------------- EXPORT ----------------
elif menu == "Export Report":
    if trees:
        df = pd.DataFrame(trees)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Professional Report",csv,"nashik_urban_forest_report.csv")

# ---------------- APP MANUAL ----------------
elif menu == "App Manual":
    st.markdown("<h3>User Manual</h3>", unsafe_allow_html=True)
    st.markdown("""
✔ Login / Register  
✔ Dashboard → Overview  
✔ Register Tree → Add new  
✔ Edit / Update → Refine data  
✔ Authority Report → Ward analytics  
✔ Export → Professional CSV  
""")

