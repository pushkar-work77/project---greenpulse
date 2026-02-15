
import streamlit as st
import json
import os
from datetime import date, datetime
import pandas as pd

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Urban Forest Survival Tracker",
    page_icon="🌳",
    layout="wide"
)

# ---------- STYLES ----------
st.markdown("""
<style>
.badge {
    padding: 6px 12px;
    border-radius: 12px;
    color: white;
    font-weight: bold;
    display: inline-block;
}
.healthy {background-color: #2ecc71;}
.needswater {background-color: #f39c12;}
.dead {background-color: #e74c3c;}
.section {
    padding: 10px;
    border-radius: 10px;
    background-color: #f5f5f5;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

DB_FILE = "trees.json"

def load_data():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def days_since_update(d):
    last = datetime.strptime(d, "%Y-%m-%d").date()
    return (date.today() - last).days

def status_badge(status):
    if status == "Healthy":
        return '<span class="badge healthy">Healthy</span>'
    elif status == "Needs Water":
        return '<span class="badge needswater">Needs Water</span>'
    else:
        return '<span class="badge dead">Dead</span>'

st.title("🌳 Urban Forest Survival Tracker")
st.caption("Smart Monitoring Dashboard — Nashik")

menu = st.sidebar.selectbox(
    "Choose Action",
    [
        "Dashboard",
        "Register Tree",
        "Update Tree Status",
        "Map View",
        "Leaderboard",
        "Export Report"
    ]
)

trees = load_data()

# ---------- DASHBOARD ----------
if menu == "Dashboard":

    st.markdown("## 📊 Dashboard Overview")

    wards = sorted(set(t["ward"] for t in trees)) if trees else []
    selected_ward = st.selectbox("Filter by Ward", ["All"] + wards)

    if selected_ward != "All":
        filtered = [t for t in trees if t["ward"] == selected_ward]
    else:
        filtered = trees

    total = len(filtered)
    healthy = sum(1 for t in filtered if t["status"] == "Healthy")
    needs_water = sum(1 for t in filtered if t["status"] == "Needs Water")
    dead = sum(1 for t in filtered if t["status"] == "Dead")

    survival_rate = (healthy / total * 100) if total else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Trees", total)
    col2.metric("Survival Rate (%)", round(survival_rate, 2))
    col3.metric("Needs Water", needs_water)
    col4.metric("Dead Trees", dead)

    # ---------- STATUS CHART ----------
    st.markdown("### 🌿 Tree Health Distribution")
    status_df = pd.DataFrame({
        "Status": ["Healthy", "Needs Water", "Dead"],
        "Count": [healthy, needs_water, dead]
    })
    st.bar_chart(status_df.set_index("Status"))

    # ---------- WARD PERFORMANCE ----------
    st.markdown("### 🏙 Ward Performance Comparison")
    if filtered:
        df = pd.DataFrame(filtered)
        ward_stats = df.groupby("ward")["status"].apply(lambda x: (x == "Healthy").sum())
        st.bar_chart(ward_stats)

    # ---------- WATER RECOMMENDATION ----------
    st.markdown("### 💧 Needs Water Recommendation")
    water_days = st.slider("Recommend watering if not updated for days >", 2, 30, 5)

    water_recommend = [
        t for t in filtered
        if days_since_update(t["last_updated"]) > water_days
        and t["status"] == "Healthy"
    ]

    if water_recommend:
        st.warning(f"{len(water_recommend)} trees should be checked/watered")
        for t in water_recommend:
            st.markdown(
                f"{t['location']} | Ward {t['ward']} | Volunteer: {t['volunteer']}",
                unsafe_allow_html=True
            )
    else:
        st.success("No watering needed right now")

    # ---------- NEGLECT ALERT ----------
    st.markdown("### 🚨 Neglected Trees Alert")
    neglect_days = st.slider("Alert if not updated for days >", 3, 60, 10)

    neglected = [
        t for t in filtered
        if days_since_update(t["last_updated"]) > neglect_days
        and t["status"] != "Dead"
    ]

    if neglected:
        st.error(f"{len(neglected)} trees need attention!")
    else:
        st.success("No neglected trees 🎉")

    # ---------- TABLE ----------
    st.markdown("### 📋 Tree Records")
    if filtered:
        df = pd.DataFrame(filtered)
        df["status"] = df["status"].apply(lambda s: status_badge(s))
        st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)

# ---------- REGISTER ----------
elif menu == "Register Tree":

    st.markdown("## 🌱 Register New Tree")

    ward = st.text_input("Ward Name / Number")
    location = st.text_input("Location")
    species = st.text_input("Species")
    volunteer = st.text_input("Volunteer Name")

    lat = st.number_input("Latitude", format="%.6f")
    lon = st.number_input("Longitude", format="%.6f")

    if st.button("Register"):
        if ward and location and species and volunteer:
            tree = {
                "id": len(trees) + 1,
                "ward": ward,
                "location": location,
                "species": species,
                "volunteer": volunteer,
                "latitude": lat,
                "longitude": lon,
                "status": "Healthy",
                "last_updated": str(date.today())
            }
            trees.append(tree)
            save_data(trees)
            st.success("Tree registered successfully!")
        else:
            st.warning("Please fill all fields.")

# ---------- UPDATE ----------
elif menu == "Update Tree Status":

    st.markdown("## 🔄 Update Tree Health")

    if trees:
        tree_id = st.selectbox("Select Tree ID", [t["id"] for t in trees])
        new_status = st.selectbox("Status", ["Healthy", "Needs Water", "Dead"])

        if st.button("Update"):
            for t in trees:
                if t["id"] == tree_id:
                    t["status"] = new_status
                    t["last_updated"] = str(date.today())
            save_data(trees)
            st.success("Status updated!")
    else:
        st.info("No trees registered yet.")

# ---------- MAP ----------
elif menu == "Map View":

    st.markdown("## 🗺 Tree Locations Map")

    if trees:
        df = pd.DataFrame(trees)
        map_data = df[["latitude", "longitude"]].dropna()
        st.map(map_data)
    else:
        st.info("No trees registered yet.")

# ---------- LEADERBOARD ----------
elif menu == "Leaderboard":

    st.markdown("## 🏆 Volunteer Leaderboard")

    if trees:
        df = pd.DataFrame(trees)
        leaderboard = df["volunteer"].value_counts().reset_index()
        leaderboard.columns = ["Volunteer", "Trees Maintained"]

        st.dataframe(leaderboard)
        st.bar_chart(leaderboard.set_index("Volunteer"))
    else:
        st.info("No data available.")

# ---------- EXPORT ----------
elif menu == "Export Report":

    st.markdown("## 📤 Export Tree Report")

    if trees:
        df = pd.DataFrame(trees)
        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download CSV Report",
            data=csv,
            file_name="nashik_tree_report.csv",
            mime="text/csv"
        )
    else:
        st.info("No data available.")



