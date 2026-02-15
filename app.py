
import streamlit as st
import json
import os
from datetime import date, datetime
import pandas as pd
import random

# ---------- CONFIG ----------
st.set_page_config(page_title="Urban Forest Survival Tracker", page_icon="🌳", layout="wide")

DB_FILE = "trees.json"
USER_FILE = "users.json"

# ---------- SESSION STATE ----------
if "user" not in st.session_state:
    st.session_state.user = None
if "show_tutorial" not in st.session_state:
    st.session_state.show_tutorial = True

# ---------- UTILITY FUNCTIONS ----------
def load_data(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return []

def save_data(data, file):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def days_since_update(d):
    try:
        last = datetime.strptime(d, "%Y-%m-%d").date()
        return (date.today() - last).days
    except:
        return 999

def status_badge(status):
    if status == "Healthy": return '<span class="badge healthy">Healthy</span>'
    if status == "Needs Water": return '<span class="badge needswater">Needs Water</span>'
    return '<span class="badge dead">Dead</span>'

# ---------- STYLES ----------
st.markdown("""
<style>
body {background-color:#e0f2f1; color:#000000;}
.badge {padding:6px 12px;border-radius:12px;color:white;font-weight:bold;}
.healthy {background:#2ecc71;}
.needswater {background:#f39c12;}
.dead {background:#e74c3c;}
button {background-color:#0277bd; color:white;}
</style>
""", unsafe_allow_html=True)

# ---------- LOAD DATA ----------
trees = load_data(DB_FILE)
users = load_data(USER_FILE)

# ---------- SPECIES DATA ----------
SPECIES_LIST = ["Mango","Neem","Peepal","Banyan","Jamun"]
SPECIES_TEMP_RANGE = {
    "Mango": (24, 35),
    "Neem": (25, 40),
    "Peepal": (20, 38),
    "Banyan": (22, 38),
    "Jamun": (24, 36)
}

# ---------- TUTORIAL ----------
if st.session_state.show_tutorial:
    st.title("🌳 Welcome to Urban Forest Survival Tracker")
    st.markdown("""
    **Tutorial for Beginners**
    1. Register as a volunteer or government authority.
    2. Add trees with correct species, ward, location.
    3. Dashboard shows survival, watering needs, neglect alerts.
    4. AI predicts survival chances and shows ward-wise risk heatmap.
    5. Export professional reports for authorities.
    """)
    if st.button("Skip Tutorial"):
        st.session_state.show_tutorial = False
        st.experimental_rerun()

# ---------- USER REGISTRATION ----------
if st.session_state.user is None:
    st.title("📝 User Registration / Login")
    option = st.radio("Do you want to Register or Login?", ["Register", "Login"])
    
    if option == "Register":
        name = st.text_input("Name")
        ward = st.text_input("Ward (Nashik)")
        location = st.text_input("Location (Nashik area)")
        role = st.selectbox("Role", ["Volunteer", "Government Authority"])
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Register"):
            if not all([name, ward, location, username, password]):
                st.error("Please fill all fields")
            elif any(u["username"]==username for u in users):
                st.error("Username already exists")
            else:
                users.append({"name":name,"ward":ward,"location":location,"role":role,"username":username,"password":password})
                save_data(users, USER_FILE)
                st.success("User registered! Please login")
    
    elif option == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = next((u for u in users if u["username"]==username and u["password"]==password), None)
            if user:
                st.session_state.user = user
                st.success(f"Welcome {user['name']}!")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")

else:
    # ---------- LOGOUT ----------
    if st.button("Logout"):
        st.session_state.user = None
        st.experimental_rerun()

    # ---------- TABS ----------
    tabs = st.tabs(["Dashboard","Register Tree","Edit Tree","Update Status","Map View","Leaderboard","Authority Summary","Export Report","Profile"])
    
    # ---------- DASHBOARD ----------
    with tabs[0]:
        st.title("📊 Dashboard")
        wards = sorted(set(t.get("ward","Unknown") for t in trees)) if trees else []
        selected_ward = st.selectbox("Filter by Ward", ["All"]+wards)
        filtered = [t for t in trees if t.get("ward","Unknown")==selected_ward] if selected_ward!="All" else trees
        total = len(filtered)
        healthy = sum(1 for t in filtered if t.get("status")=="Healthy")
        needs_water = sum(1 for t in filtered if t.get("status")=="Needs Water")
        dead = sum(1 for t in filtered if t.get("status")=="Dead")
        survival_rate = (healthy/total*100) if total else 0
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Total Trees", total)
        c2.metric("Survival Rate (%)",round(survival_rate,2))
        c3.metric("Needs Water", needs_water)
        c4.metric("Dead Trees", dead)
        st.subheader("Tree Health Distribution")
        st.bar_chart(pd.DataFrame({"Status":["Healthy","Needs Water","Dead"],"Count":[healthy,needs_water,dead]}).set_index("Status"))

    # ---------- REGISTER TREE ----------
    with tabs[1]:
        st.title("🌱 Register Tree")
        ward_input = st.text_input("Ward")
        location_input = st.text_input("Location")
        species_input = st.selectbox("Species", SPECIES_LIST)
        volunteer_input = st.text_input("Volunteer Name", value=st.session_state.user["name"])
        lat_input = st.number_input("Latitude", format="%.6f")
        lon_input = st.number_input("Longitude", format="%.6f")
        # Species survival check
        NASHIK_TEMP = 30
        min_temp,max_temp = SPECIES_TEMP_RANGE.get(species_input,(24,32))
        survival_ok = min_temp<=NASHIK_TEMP<=max_temp
        if not survival_ok:
            st.warning(f"{species_input} may not survive in Nashik (Recommended: {min_temp}-{max_temp}°C)")
        if st.button("Register Tree"):
            if not survival_ok:
                st.error("Cannot register: species unsuitable")
            elif any(t["ward"]==ward_input and t["location"]==location_input and t["species"]==species_input for t in trees):
                st.warning("Tree already exists. Please re-enter")
            else:
                tree = {"id":len(trees)+1,"ward":ward_input,"location":location_input,"species":species_input,
                        "volunteer":volunteer_input,"latitude":lat_input,"longitude":lon_input,"status":"Healthy",
                        "last_updated":str(date.today())}
                trees.append(tree)
                save_data(trees,DB_FILE)
                st.success("Tree registered!")

    # ---------- EDIT TREE ----------
    with tabs[2]:
        st.title("✏️ Edit or Delete Tree")
        if trees:
            tree_id = st.selectbox("Select Tree ID",[t["id"] for t in trees])
            tree = next((t for t in trees if t["id"]==tree_id), None)
            if tree:
                new_ward = st.text_input("Ward",tree["ward"])
                new_location = st.text_input("Location",tree["location"])
                new_species = st.selectbox("Species",SPECIES_LIST,index=SPECIES_LIST.index(tree["species"]))
                new_volunteer = st.text_input("Volunteer",tree["volunteer"])
                new_lat = st.number_input("Latitude",value=float(tree["latitude"]),format="%.6f")
                new_lon = st.number_input("Longitude",value=float(tree["longitude"]),format="%.6f")
                col1,col2=st.columns(2)
                if col1.button("💾 Save Changes"):
                    tree.update({"ward":new_ward,"location":new_location,"species":new_species,
                                 "volunteer":new_volunteer,"latitude":new_lat,"longitude":new_lon,
                                 "last_updated":str(date.today())})
                    save_data(trees,DB_FILE)
                    st.success("Updated successfully!")
                if col2.button("🗑 Delete Tree"):
                    trees.remove(tree)
                    save_data(trees,DB_FILE)
                    st.warning("Tree deleted!")
        else:
            st.info("No trees registered yet.")

    # ---------- UPDATE STATUS ----------
    with tabs[3]:
        st.title("🔄 Update Tree Status")
        if trees:
            tree_id = st.selectbox("Select Tree ID",[t["id"] for t in trees])
            new_status = st.selectbox("Status",["Healthy","Needs Water","Dead"])
            if st.button("Update Status"):
                for t in trees:
                    if t["id"]==tree_id:
                        t["status"]=new_status
                        t["last_updated"]=str(date.today())
                save_data(trees,DB_FILE)
                st.success("Status updated!")

    # ---------- MAP VIEW ----------
    with tabs[4]:
        st.title("🗺 Tree Locations Map")
        if trees:
            df=pd.DataFrame(trees)
            if "latitude" in df and "longitude" in df:
                st.map(df[["latitude","longitude"]].dropna())

    # ---------- LEADERBOARD ----------
    with tabs[5]:
        st.title("🏆 Volunteer Leaderboard")
        if trees:
            df=pd.DataFrame(trees)
            leaderboard=df["volunteer"].value_counts().reset_index()
            leaderboard.columns=["Volunteer","Trees Maintained"]
            st.dataframe(leaderboard)
            st.bar_chart(leaderboard.set_index("Volunteer"))

    # ---------- AUTHORITY SUMMARY ----------
    with tabs[6]:
        st.title("📋 Authority Summary")
        if trees:
            df=pd.DataFrame(trees)
            total=len(df)
            healthy=len(df[df["status"]=="Healthy"])
            dead=len(df[df["status"]=="Dead"])
            survival_rate = round(healthy/total*100,2)
            st.metric("Total Trees",total)
            st.metric("Survival Rate (%)",survival_rate)
            ward_summary=df.groupby("ward").agg(Total=("id","count"),Healthy=("status",lambda x:(x=="Healthy").sum())).reset_index()
            ward_summary["Survival %"]=round(ward_summary["Healthy"]/ward_summary["Total"]*100,2)
            st.dataframe(ward_summary)
            st.bar_chart(ward_summary.set_index("ward")["Survival %"])

    # ---------- EXPORT REPORT ----------
    with tabs[7]:
        st.title("📤 Export Report")
        if trees:
            df=pd.DataFrame(trees)
            df["Status Icon"]=df["status"].apply(lambda s:"🟢" if s=="Healthy" else "🟡" if s=="Needs Water" else "🔴")
            summary = f"Urban Forest Report - Nashik\nTotal Trees: {len(df)}\nHealthy: {(df['status']=='Healthy').sum()}\nNeeds Water: {(df['status']=='Needs Water').sum()}\nDead: {(df['status']=='Dead').sum()}\nGenerated on {date.today()}"
            csv=df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV",data=csv,file_name="nashik_report.csv",mime="text/csv")
            st.text(summary)

    # ---------- PROFILE ----------
    with tabs[8]:
        st.title("👤 User Profile")
        user=st.session_state.user
        name=st.text_input("Name",user["name"])
        ward=st.text_input("Ward",user["ward"])
        location=st.text_input("Location",user["location"])
        role=st.selectbox("Role",["Volunteer","Government Authority"],index=0 if user["role"]=="Volunteer" else 1)
        if st.button("Save Profile"):
            user.update({"name":name,"ward":ward,"location":location,"role":role})
            save_data(users,USER_FILE)
            st.success("Profile updated!")

