
import streamlit as st
import json
import os
from datetime import date, datetime
import pandas as pd

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Nashik Urban Forest Monitoring System",
    page_icon="🌿",
    layout="wide"
)

TREES_FILE = "trees.json"
USERS_FILE = "users.json"

# ---------------- NATURE UI ----------------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(to bottom, #dff5e1, #b8e0c0);
    color: black;
}
.gov-header {
    background: linear-gradient(90deg,#2c6e49,#40916c);
    color:white;
    padding:15px;
    border-radius:10px;
    text-align:center;
}
.card {
    background:white;
    padding:15px;
    border-radius:10px;
    box-shadow:0 4px 10px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATA FUNCTIONS ----------------
def load_json(file):
    if not os.path.exists(file):
        return []
    try:
        with open(file,"r") as f:
            return json.load(f)
    except:
        return []

def save_json(file,data):
    with open(file,"w") as f:
        json.dump(data,f,indent=4)

def days_since_update(d):
    try:
        last = datetime.strptime(d,"%Y-%m-%d").date()
        return (date.today()-last).days
    except:
        return 999

def valid_nashik(text):
    if not text:
        return False
    allowed = ["nashik","mhasrul","panchavati","cidco","satpur","ambad","gangapur"]
    return any(w in text.lower() for w in allowed)

def survival_ai(tree):
    score = 50
    if tree.get("status")=="Healthy": score+=20
    if days_since_update(tree.get("last_updated"))<5: score+=15
    if tree.get("soil",50)>60: score+=10
    if tree.get("rainfall",50)>40: score+=5
    return min(score,100)

trees = load_json(TREES_FILE)
users = load_json(USERS_FILE)

# ---------------- HEADER ----------------
st.markdown('<div class="gov-header"><h2>Nashik Smart Urban Forest Monitoring System</h2></div>', unsafe_allow_html=True)

# ---------------- FIRST TIME TUTORIAL ----------------
if "tutorial_seen" not in st.session_state:
    st.title("Welcome to Urban Forest Monitoring System 🌱")

    st.markdown("""
### Purpose
Track plantation survival across Nashik wards.

### How It Works
• Citizens register trees  
• Volunteers maintain them  
• Authorities monitor analytics  
• AI predicts survival probability  

### Features
✔ Tree health monitoring  
✔ Ward risk heatmap  
✔ Environmental indicators  
✔ Government-ready reports  
✔ Accountability tracking  

Click continue to start using the system.
""")

    col1,col2 = st.columns(2)
    if col1.button("Start Tutorial"):
        st.info("Step 1 → Register yourself\nStep 2 → Add tree\nStep 3 → Monitor dashboard\nStep 4 → Generate authority report")
        st.session_state["tutorial_seen"]=True
        st.rerun()

    if col2.button("Skip"):
        st.session_state["tutorial_seen"]=True
        st.rerun()

    st.stop()

# ---------------- USER REGISTRATION ----------------
if "user" not in st.session_state:

    st.subheader("User Registration")

    name = st.text_input("Full Name")
    ward = st.text_input("Ward")
    location = st.text_input("Location (Nashik region)")
    role = st.selectbox("Role",["Volunteer","Government Authority"])
    contact = st.text_input("Contact Number")

    if st.button("Register & Enter App"):
        if not valid_nashik(location):
            st.error("Only Nashik region users allowed")
        else:
            st.session_state["user"] = name
            users.append({
                "name":name,
                "ward":ward,
                "location":location,
                "role":role,
                "contact":contact
            })
            save_json(USERS_FILE,users)
            st.success("Registration successful")
            st.rerun()

    st.stop()

# ---------------- NAVIGATION ----------------
menu = st.sidebar.selectbox(
    "Navigation",
    ["Dashboard","Register Tree","Edit Tree",
     "Update Status","Map","Authority Report",
     "Export Report","App Manual"]
)

# ---------------- DASHBOARD ----------------
if menu=="Dashboard":

    st.subheader("City Monitoring Dashboard")

    total = len(trees)
    healthy = sum(1 for t in trees if t.get("status")=="Healthy")
    survival_rate = (healthy/total*100) if total else 0

    c1,c2 = st.columns(2)
    c1.metric("Total Trees",total)
    c2.metric("Survival Rate (%)",round(survival_rate,2))

    if trees:
        df = pd.DataFrame(trees)
        df["AI Survival %"] = df.apply(survival_ai,axis=1)
        st.dataframe(df)

# ---------------- REGISTER TREE ----------------
elif menu=="Register Tree":

    st.subheader("Register Tree")

    ward = st.text_input("Ward")
    location = st.text_input("Location (Nashik)")
    species = st.text_input("Species")
    nutrients = st.text_input("Nutrients / Minerals")
    temperature = st.text_input("Temperature Range")
    soil = st.slider("Soil Health Score",0,100,50)
    rainfall = st.slider("Rainfall Impact",0,100,50)

    lat = st.number_input("Latitude",format="%.6f")
    lon = st.number_input("Longitude",format="%.6f")

    if st.button("Register Tree"):
        if not valid_nashik(location):
            st.error("Tree must be in Nashik region")
        else:
            trees.append({
                "id":len(trees)+1,
                "ward":ward,
                "location":location,
                "species":species,
                "nutrients":nutrients,
                "temperature":temperature,
                "soil":soil,
                "rainfall":rainfall,
                "latitude":lat,
                "longitude":lon,
                "status":"Healthy",
                "last_updated":str(date.today()),
                "volunteer":st.session_state["user"]
            })
            save_json(TREES_FILE,trees)
            st.success("Tree registered")

# ---------------- EDIT TREE ----------------
elif menu=="Edit Tree":
    if trees:
        tree_id = st.selectbox("Select Tree",[t["id"] for t in trees])
        tree = next(t for t in trees if t["id"]==tree_id)

        new_status = st.selectbox("Status",["Healthy","Needs Water","Dead"])

        if st.button("Update"):
            tree["status"]=new_status
            tree["last_updated"]=str(date.today())
            save_json(TREES_FILE,trees)
            st.success("Updated")

# ---------------- MAP ----------------
elif menu=="Map":
    if trees:
        df = pd.DataFrame(trees)
        st.map(df[["latitude","longitude"]].dropna())

# ---------------- AUTHORITY REPORT ----------------
elif menu=="Authority Report":

    st.subheader("Municipal Environmental Report")

    if trees:
        df = pd.DataFrame(trees)

        ward_summary = df.groupby("ward").agg(
            Total=("id","count"),
            Avg_Soil=("soil","mean"),
            Avg_Rainfall=("rainfall","mean"),
            Healthy=("status", lambda x:(x=="Healthy").sum())
        ).reset_index()

        ward_summary["Survival %"] = round((ward_summary["Healthy"]/ward_summary["Total"])*100,2)
        ward_summary["Risk Level"] = ward_summary["Survival %"].apply(
            lambda x:"High Risk" if x<50 else "Moderate" if x<75 else "Healthy"
        )

        st.dataframe(ward_summary)
        st.bar_chart(ward_summary.set_index("ward")["Survival %"])

        st.markdown("Report Generated:",date.today())

# ---------------- EXPORT ----------------
elif menu=="Export Report":
    if trees:
        df = pd.DataFrame(trees)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Professional Report",csv,"nashik_environment_report.csv")

# ---------------- MANUAL ----------------
elif menu=="App Manual":
    st.title("Application Manual")

    st.markdown("""
### System Workflow
1. Register as Nashik user  
2. Add plantation details  
3. Monitor survival analytics  
4. Authorities generate reports  

### AI Prediction
Survival score uses:
• Maintenance frequency  
• Soil health  
• Rainfall impact  

### Intended Use
Urban forestry monitoring for Nashik municipality.
""")

