
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

# ---------- GOVERNMENT STYLE UI ----------
st.markdown("""
<style>

/* MAIN BACKGROUND */
.stApp {
    background-color: #2f2f2f;
    color: white;
}

/* TEXT COLORS */
h1, h2, h3, h4, h5, h6, p, div, span, label {
    color: white !important;
}

/* METRIC BOXES */
.stMetric {
    background-color: #3a3a3a;
    padding: 15px;
    border-radius: 10px;
    border: 1px solid #555;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background-color: #1f1f1f;
}

/* TABLE BACKGROUND */
table {
    background-color: #3a3a3a !important;
    color: white !important;
}

/* BADGES */
.badge {
    padding: 6px 12px;
    border-radius: 12px;
    color: white;
    font-weight: bold;
}
.healthy {background:#2ecc71;}
.needswater {background:#f39c12;}
.dead {background:#e74c3c;}

</style>
""", unsafe_allow_html=True)


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

# ---------- AI PREDICTION ----------
def predict_survival(tree):
    score = 0

    days = days_since_update(tree.get("last_updated"))

    if days <= 7:
        score += 40
    elif days <= 15:
        score += 25
    else:
        score += 5

    status = tree.get("status")
    if status == "Healthy":
        score += 40
    elif status == "Needs Water":
        score += 20

    if tree.get("volunteer"):
        score += 20

    return min(score, 100)

trees = load_data()

st.title("🌳 Urban Forest Survival Tracker")
st.caption("Smart Monitoring Dashboard — Nashik")

menu = st.sidebar.selectbox(
    "Choose Action",
    ["Dashboard", "Register Tree", "Edit / Delete Tree",
     "Update Tree Status", "Map View", "Leaderboard",
     "Authority Summary", "Export Report"]
)

# ---------- DASHBOARD ----------
if menu == "Dashboard":

    wards = sorted(set(t.get("ward", "Unknown") for t in trees)) if trees else []
    selected_ward = st.selectbox("Filter by Ward", ["All"] + wards)

    filtered = [t for t in trees if t.get("ward", "Unknown") == selected_ward] if selected_ward != "All" else trees

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

    if filtered:
        avg_prediction = sum(predict_survival(t) for t in filtered) / len(filtered)
        st.info(f"AI Estimated Overall Survival: {round(avg_prediction, 2)}%")

    if filtered:
        df = pd.DataFrame(filtered)
        df["AI Survival %"] = df.apply(predict_survival, axis=1)
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
            trees.append({
                "id": len(trees) + 1,
                "ward": ward,
                "location": location,
                "species": species,
                "volunteer": volunteer,
                "latitude": lat,
                "longitude": lon,
                "status": "Healthy",
                "last_updated": str(date.today())
            })
            save_data(trees)
            st.success("Tree registered successfully!")

# ---------- EDIT DELETE ----------
elif menu == "Edit / Delete Tree":

    if not trees:
        st.info("No trees available.")
        st.stop()

    tree_id = st.selectbox("Select Tree ID", [t.get("id") for t in trees])
    tree = next((t for t in trees if t.get("id") == tree_id), None)

    if tree:
        new_ward = st.text_input("Ward", tree.get("ward"))
        new_location = st.text_input("Location", tree.get("location"))
        new_species = st.text_input("Species", tree.get("species"))
        new_volunteer = st.text_input("Volunteer", tree.get("volunteer"))
        new_lat = st.number_input("Latitude", value=float(tree.get("latitude", 0.0)))
        new_lon = st.number_input("Longitude", value=float(tree.get("longitude", 0.0)))

        col1, col2 = st.columns(2)

        if col1.button("Save Changes"):
            tree.update({
                "ward": new_ward,
                "location": new_location,
                "species": new_species,
                "volunteer": new_volunteer,
                "latitude": new_lat,
                "longitude": new_lon,
                "last_updated": str(date.today())
            })
            save_data(trees)
            st.success("Tree updated!")

        if col2.button("Delete Tree"):
            trees.remove(tree)
            save_data(trees)
            st.warning("Tree deleted!")
            st.rerun()

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
        map_df = df[["latitude", "longitude"]].dropna()
        if not map_df.empty:
            st.map(map_df)

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

    st.markdown("## 🌳 Urban Forest Survival Report — Nashik")

    if not trees:
        st.warning("No data available.")
        st.stop()

    df = pd.DataFrame(trees)
    df["AI Survival %"] = df.apply(predict_survival, axis=1)

    total = len(df)
    healthy = len(df[df["status"] == "Healthy"])
    dead = len(df[df["status"] == "Dead"])
    survival_rate = round((healthy / total) * 100, 2)

    c1, c2 = st.columns(2)
    c1.metric("Total Trees", total)
    c2.metric("Survival Rate (%)", survival_rate)

    st.subheader("AI Risk Assessment")
    st.write("High Risk Trees:", len(df[df["AI Survival %"] < 40]))
    st.write("Moderate Risk Trees:", len(df[(df["AI Survival %"] >= 40) & (df["AI Survival %"] < 70)]))
    st.write("Low Risk Trees:", len(df[df["AI Survival %"] >= 70]))

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

