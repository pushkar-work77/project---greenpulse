
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
</style>
""", unsafe_allow_html=True)

DB_FILE = "trees.json"

# ---------- DATA FUNCTIONS ----------
def load_data():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def days_since_update(d):
    try:
        last = datetime.strptime(d, "%Y-%m-%d").date()
        return (date.today() - last).days
    except:
        return 999

def status_badge(status):
    if status == "Healthy":
        return '<span class="badge healthy">Healthy</span>'
    elif status == "Needs Water":
        return '<span class="badge needswater">Needs Water</span>'
    else:
        return '<span class="badge dead">Dead</span>'

trees = load_data()

st.title("🌳 Urban Forest Survival Tracker")
st.caption("Smart Monitoring Dashboard — Nashik")

menu = st.sidebar.selectbox(
    "Choose Action",
    ["Dashboard", "Register Tree", "Update Tree Status",
     "Map View", "Leaderboard", "Authority Summary", "Export Report"]
)

# ---------- DASHBOARD ----------
if menu == "Dashboard":

    wards = sorted(set(t.get("ward", "Unknown") for t in trees)) if trees else []
    selected_ward = st.selectbox("Filter by Ward", ["All"] + wards)

    if selected_ward != "All":
        filtered = [t for t in trees if t.get("ward", "Unknown") == selected_ward]
    else:
        filtered = trees

    total = len(filtered)
    healthy = sum(1 for t in filtered if t.get("status") == "Healthy")
    needs_water = sum(1 for t in filtered if t.get("status") == "Needs Water")
    dead = sum(1 for t in filtered if t.get("status") == "Dead")

    survival_rate = (healthy / total * 100) if total else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Trees", total)
    c2.metric("Survival Rate (%)", round(survival_rate, 2))
    c3.metric("Needs Water", needs_water)
    c4.metric("Dead Trees", dead)

    st.subheader("Tree Health Distribution")
    status_df = pd.DataFrame({
        "Status": ["Healthy", "Needs Water", "Dead"],
        "Count": [healthy, needs_water, dead]
    })
    st.bar_chart(status_df.set_index("Status"))

    st.subheader("Needs Water Recommendation")
    water_recommend = [
        t for t in filtered
        if days_since_update(t.get("last_updated")) > 5
        and t.get("status") == "Healthy"
    ]
    if water_recommend:
        st.warning(f"{len(water_recommend)} trees should be checked")
    else:
        st.success("No watering needed")

    st.subheader("Neglected Trees Alert")
    neglected = [
        t for t in filtered
        if days_since_update(t.get("last_updated")) > 10
        and t.get("status") != "Dead"
    ]
    if neglected:
        st.error(f"{len(neglected)} trees need attention")

    if filtered:
        df = pd.DataFrame(filtered)
        df["status"] = df["status"].apply(status_badge)
        st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)

# ---------- REGISTER ----------
elif menu == "Register Tree":

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

# ---------- UPDATE ----------
elif menu == "Update Tree Status":

    if trees:
        tree_id = st.selectbox("Select Tree ID", [t.get("id") for t in trees])
        new_status = st.selectbox("Status", ["Healthy", "Needs Water", "Dead"])

        if st.button("Update"):
            for t in trees:
                if t.get("id") == tree_id:
                    t["status"] = new_status
                    t["last_updated"] = str(date.today())
            save_data(trees)
            st.success("Status updated!")

# ---------- MAP ----------
elif menu == "Map View":

    if trees:
        df = pd.DataFrame(trees)
        if "latitude" in df and "longitude" in df:
            map_data = df[["latitude", "longitude"]].dropna()
            if not map_data.empty:
                st.map(map_data)

# ---------- LEADERBOARD ----------
elif menu == "Leaderboard":

    if trees:
        df = pd.DataFrame(trees)
        leaderboard = df["volunteer"].fillna("Unknown").value_counts().reset_index()
        leaderboard.columns = ["Volunteer", "Trees Maintained"]
        st.dataframe(leaderboard)
        st.bar_chart(leaderboard.set_index("Volunteer"))

# ---------- AUTHORITY SUMMARY ----------
elif menu == "Authority Summary":

    st.markdown("""
    <div style="text-align:center">
        <h1>🌳 Urban Forest Survival Report</h1>
        <h4>Nashik Smart Green Monitoring System</h4>
        <hr>
    </div>
    """, unsafe_allow_html=True)

    if not trees:
        st.warning("No data available.")
        st.stop()

    df = pd.DataFrame(trees)
    df["ward"] = df.get("ward", "Unknown").fillna("Unknown")
    df["volunteer"] = df.get("volunteer", "Unknown").fillna("Unknown")
    df["status"] = df.get("status", "Healthy")

    total = len(df)
    healthy = len(df[df["status"] == "Healthy"])
    dead = len(df[df["status"] == "Dead"])
    survival_rate = round((healthy / total) * 100, 2) if total else 0

    c1, c2 = st.columns(2)
    c1.metric("Total Trees", total)
    c2.metric("Survival Rate (%)", survival_rate)

    impact_score = round(
        (survival_rate * 0.6) +
        ((1 - dead / total) * 100 * 0.4 if total else 0),
        2
    )
    st.success(f"Urban Green Impact Score: {impact_score}/100")

    ward_summary = df.groupby("ward").agg(
        Total=("id", "count"),
        Healthy=("status", lambda x: (x == "Healthy").sum())
    ).reset_index()

    ward_summary["Survival %"] = round(
        (ward_summary["Healthy"] / ward_summary["Total"]) * 100, 2
    )

    st.dataframe(ward_summary)
    st.bar_chart(ward_summary.set_index("ward")["Survival %"])

    st.markdown("---")
    st.info("Use browser print → Save as PDF for submission")
    st.markdown(f"Report Generated: {date.today()}")

# ---------- EXPORT ----------
elif menu == "Export Report":

    if trees:
        df = pd.DataFrame(trees)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download CSV Report",
            data=csv,
            file_name="nashik_tree_report.csv",
            mime="text/csv"
        )

)

   



