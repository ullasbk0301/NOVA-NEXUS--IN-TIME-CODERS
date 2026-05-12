import streamlit as st
import pandas as pd
import json

from auth import register_user, login_user
from database import (
    add_order,
    get_orders,
    get_all_orders,
    update_order_status
)

from llm import llm_extract

st.set_page_config(page_title="AI Order System", layout="wide")

# =============================
# SESSION STATE
# =============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "role" not in st.session_state:
    st.session_state.role = ""

# =============================
# SIDEBAR AUTH
# =============================
st.sidebar.title("🔐 Login System")

menu = st.sidebar.radio("Choose", ["Login", "Register"])

# =============================
# REGISTER
# =============================
if menu == "Register":

    st.subheader("📝 Register")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    role = st.selectbox("Register As", ["user", "vendor"])

    if st.button("Register"):

        register_user(username, password, role)
        st.success(f"Registered as {role}")

# =============================
# LOGIN
# =============================
elif menu == "Login":

    st.subheader("🔑 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        user = login_user(username, password)

        if user:
            st.session_state.logged_in = True
            st.session_state.username = user["username"]
            st.session_state.role = user["role"]

            st.success(f"Welcome {user['role']}")
            st.rerun()

        else:
            st.error("Invalid credentials")

# =============================
# MAIN APP
# =============================
if st.session_state.logged_in:

    st.title("🤖 AI Order System")

    role = st.session_state.role

    st.write(f"Logged in as: **{st.session_state.username} ({role})**")

    # =====================================================
    # USER DASHBOARD
    # =====================================================
    if role == "user":

        st.subheader("👤 User Dashboard")

        msg = st.chat_input("Place your order")

        if msg:

            data = llm_extract(msg)

            if data.get("items"):

                add_order(
                    st.session_state.username,
                    data["items"],
                    data["deadline"],
                    "Received"
                )

                st.success("Order placed successfully")

        # ---------------- TABLE VIEW ----------------
        orders = get_orders(st.session_state.username)

        if not orders:
            st.info("No orders yet")

        else:

            rows = []

            for o in orders:

                items = json.loads(o[2])

                item_text = ", ".join(
                    [f"{i['name']} (x{i['quantity']})" for i in items]
                )

                rows.append({
                    "Order ID": o[0],
                    "Items": item_text,
                    "Deadline": o[3],
                    "Status": o[4]
                })

            df = pd.DataFrame(rows)

            st.dataframe(df, use_container_width=True, hide_index=True)

    # =====================================================
    # VENDOR DASHBOARD
    # =====================================================
    elif role == "vendor":

        st.subheader("👨‍💼 Vendor Dashboard")

        orders = get_all_orders()

        if not orders:
            st.info("No orders available")

        else:

            rows = []

            for o in orders:

                items = json.loads(o[2])

                item_text = ", ".join(
                    [f"{i['name']} (x{i['quantity']})" for i in items]
                )

                rows.append({
                    "Order ID": o[0],
                    "User": o[1],
                    "Items": item_text,
                    "Deadline": o[3],
                    "Status": o[4]
                })

            df = pd.DataFrame(rows)

            st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown("### Update Order Status")

            order_id = st.number_input("Order ID", min_value=1)

            status = st.selectbox(
                "Set Status",
                ["Received", "In Review", "Dispatched"]
            )

            if st.button("Update Status"):

                update_order_status(order_id, status)
                st.success("Order updated successfully")
                st.rerun()

# =============================
# LOGOUT
# =============================
if st.session_state.logged_in:

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.rerun()