
import streamlit as st
import pandas as pd
import json, os, re
from datetime import date, datetime

# -------------------- FILES --------------------
USER_FILE = "users.json"
DB_FILE = "trees.json"

# -------------------- DATA FUNCTIONS --------------------
def load_data(file):
    if not os.path.exists(file):
        return []
    with open(file, "r") as f:
        try:
            return json.load(f)
        except:
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

# -------------------- VALIDATION --------------------
USERNAME_PATTERN = r"^[A-Za-z0-9_-]+$"

# -------------------- LOAD DATA --------------------
users = load_data(USER_FILE)
trees = load_data(DB_FILE)

# -------------------- SESSION STATE --------------------
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['current_user'] = None

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="Urban Forest Survival Tracker", page_icon="🌳", layout="wide")

# -------------------- STYLES --------------------
st.markdown("""
<style>
body {background-color:#dbe8d6; color:#000;}
.badge {padding:6px 12px;border-radius:12px;color:white;font-weight:bold;}
.healthy {background:#2ecc71;}
.needswater {background:#f39c12;}
.dead {background:#e74c3c;}
button, .stButton>button {color:white !important; background-color:#2e7d32 !important; border:none;}
</style>
""", unsafe_allow_html=True)

# -------------------- APP TITLE --------------------
st.title("🌳 Urban Forest Survival Tracker — Nashik")
st.markdown("---")

# -------------------- USER AUTH --------------------
if not st.session_state['logged_in']:
    auth_choice = st.selectbox("Choose Action", ["Login", "Register"])
    
    if auth_choice == "Register":
        st.subheader("📝 New User Registration")
        st.info("Username: letters, digits, underscores (_) and dashes (-). Example: John_Doe123")
        
        name = st.text_input("Full Name")
        ward = st.text_input("Ward Name/Number")
        location = st.text_input("Location (must be Nashik)")
        role = st.selectbox("Role", ["Volunteer", "Government Authority"])
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Register"):
            if not all([name, ward, location, role, username, password]):
                st.error("Please fill all fields")
            elif not re.match(USERNAME_PATTERN, username):
                st.error("Invalid username! Only letters, digits, _ and - are allowed")
            elif any(u.get("username") == username for u in users):
                st.error("Username already exists. Please choose another.")
            else:
                users.append({"name":name,"ward":ward,"location":location,
                              "role":role,"username":username,"password":password})
                save_data(users, USER_FILE)
                st.success("User registered successfully! Please login now.")
                
    elif auth_choice == "Login":
        st.subheader("🔐 Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = next((u for u in users if u.get("username")==username and u.get("password")==password), None)
            if user:
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = user
                st.success(f"Welcome {user['name']}!")
            else:
                st.error("Invalid username or password")

# -------------------- MAIN APP --------------------
if st.session_state['logged_in']:
    user = st.session_state['current_user']
    st.info(f"Logged in as: {user['name']} ({user['role']})")
    if st.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['current_user'] = None
        st.experimental_rerun()

    # -------------------- TABS --------------------
    tabs = st.tabs(["Dashboard", "Register Tree"])
    
    # -------------------- DASHBOARD --------------------
    with tabs[0]:
        st.subheader("📊 Dashboard")
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
        c2.metric("Survival Rate (%)", round(survival_rate,2))
        c3.metric("Needs Water", needs_water)
        c4.metric("Dead Trees", dead)
        
        neglected = [t for t in filtered if days_since_update(t.get("last_updated"))>10 and t.get("status")!="Dead"]
        if neglected:
            st.error(f"{len(neglected)} trees need attention!")

        # SAFE DISPLAY: Ensure all columns exist
        if filtered:
            df = pd.DataFrame(filtered)
            df = df.copy()
            df["status_badge"] = df.get("status","Unknown")
            # Ensure mandatory columns exist
            for col in ["id","ward","location","species","volunteer"]:
                if col not in df.columns:
                    df[col] = "Unknown"
            st.dataframe(df[["id","ward","location","species","status_badge","volunteer"]])

    # -------------------- REGISTER TREE --------------------
    with tabs[1]:
        st.subheader("🌱 Register New Tree")
        ward = st.text_input("Ward Name/Number", key="ward_reg")
        location = st.text_input("Location", key="loc_reg")
        species_list = ["Neem","Mango","Peepal","Banyan","Other"]
        species = st.selectbox("Species", species_list, key="species_reg")
        volunteer = st.text_input("Volunteer Name", key="vol_reg")
        lat = st.number_input("Latitude", format="%.6f", key="lat_reg")
        lon = st.number_input("Longitude", format="%.6f", key="lon_reg")
        
        species_temp_range = {"Neem":(20,40),"Mango":(25,35),"Peepal":(20,38),"Banyan":(22,36),"Other":(15,40)}
        current_temp = 32
        can_survive = current_temp>=species_temp_range.get(species,(0,100))[0] and current_temp<=species_temp_range.get(species,(0,100))[1]
        
        if st.button("Register Tree", key="btn_register_tree"):
            if any(t.get("ward")==ward and t.get("location")==location and t.get("species")==species for t in trees):
                st.warning("Tree already exists in this location")
            elif not can_survive:
                st.error(f"{species} cannot survive at this location (temp {current_temp}°C)")
            else:
                nutrients = {"Nitrogen":"High","Phosphorus":"Medium","Potassium":"Medium"}
                trees.append({"id":len(trees)+1,"ward":ward,"location":location,"species":species,
                              "volunteer":volunteer,"latitude":lat,"longitude":lon,"status":"Healthy",
                              "last_updated":str(date.today()),"nutrients":nutrients})
                save_data(trees, DB_FILE)
                st.success("Tree registered successfully")
