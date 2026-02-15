
import streamlit as st
import json
import os
from datetime import date

DB_FILE = "trees.json"

def load_data():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

st.title("🌳 Urban Forest Survival Tracker")
st.subheader("Nashik Tree Monitoring Dashboard")

menu = st.sidebar.selectbox(
    "Choose Action",
    ["Dashboard", "Register Tree", "Update Tree Status"]
)

trees = load_data()

if menu == "Dashboard":
    total = len(trees)
    healthy = sum(1 for t in trees if t["status"] == "Healthy")
    needs_water = sum(1 for t in trees if t["status"] == "Needs Water")
    dead = sum(1 for t in trees if t["status"] == "Dead")

    survival_rate = (healthy / total * 100) if total else 0

    st.metric("Total Trees", total)
    st.metric("Survival Rate (%)", round(survival_rate, 2))
    st.metric("Needs Water", needs_water)
    st.metric("Dead Trees", dead)

    st.write("### Tree Records")
    st.write(trees)

elif menu == "Register Tree":
    st.write("### Register New Tree")
    location = st.text_input("Location")
    species = st.text_input("Species")

    if st.button("Register"):
        tree = {
            "id": len(trees) + 1,
            "location": location,
            "species": species,
            "status": "Healthy",
            "last_updated": str(date.today())
        }
        trees.append(tree)
        save_data(trees)
        st.success("Tree registered successfully!")

elif menu == "Update Tree Status":
    st.write("### Update Tree Health")

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
