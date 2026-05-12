import streamlit as st
import pandas as pd
import json
import re

from auth import register_user, login_user
from database import (
    add_order,
    get_orders,
    update_order_status,
    delete_order,
    delete_all_orders,
    get_all_orders
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

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# =============================
# SIDEBAR NAVIGATION
# =============================
st.sidebar.title("Navigation")

auth_menu = st.sidebar.selectbox("Auth", ["Login", "Register"])
page = st.sidebar.selectbox("Page", ["User Panel", "Vendor Panel"])

# =============================
# REGISTER
# =============================
if auth_menu == "Register":

    st.title("📝 Register")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        try:
            register_user(username, password)
            st.success("✅ Registered Successfully")
        except:
            st.error("❌ Username already exists")

# =============================
# LOGIN
# =============================
elif auth_menu == "Login":

    st.title("🔑 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if login_user(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("✅ Login Successful")
        else:
            st.error("❌ Invalid Credentials")

# =========================================================
# 👤 USER PANEL
# =========================================================
if page == "User Panel" and st.session_state.logged_in:

    st.title("🤖 Smart AI Order Assistant")
    st.write(f"Welcome, {st.session_state.username}")

    col1, col2 = st.columns([2, 3])

    # -----------------------------
    # CHAT SECTION
    # -----------------------------
    with col1:

        st.subheader("💬 Chat")

        user_input = st.chat_input("Type your message")

        if user_input:

            text = user_input.lower()
            st.session_state.chat_history.append(("user", user_input))

            # CREATE ORDER
            data = llm_extract(user_input)

            if data.get("items"):

                add_order(
                    st.session_state.username,
                    data["items"],
                    data["deadline"],
                    "Received"
                )

                st.session_state.chat_history.append(
                    ("bot", "✅ Order Created Successfully")
                )

            # SHOW ORDERS
            elif "my orders" in text:

                orders = get_orders(st.session_state.username)

                msg = "📭 No orders found" if not orders else ""

                for order in orders:
                    items = json.loads(order[2])
                    msg += f"\n📦 #{order[0]} | {items} | {order[3]} | {order[4]}"

                st.session_state.chat_history.append(("bot", msg))

            # DELETE ORDER
            elif "delete order" in text:

                match = re.search(r'#(\d+)', text)

                if match:
                    delete_order(int(match.group(1)))
                    msg = f"🗑️ Order #{match.group(1)} deleted"
                else:
                    msg = "❌ Use format #ID"

                st.session_state.chat_history.append(("bot", msg))

            # DELETE ALL
            elif "delete all" in text:

                delete_all_orders(st.session_state.username)
                st.session_state.chat_history.append(("bot", "🧨 All orders deleted"))

            else:
                st.session_state.chat_history.append(("bot", "🤖 Not understood"))

        # CHAT DISPLAY
        for role, msg in st.session_state.chat_history:

            if role == "user":
                st.markdown(f"**🧑 You:** {msg}")
            else:
                st.markdown(f"**🤖 Bot:** {msg}")

    # -----------------------------
    # DASHBOARD
    # -----------------------------
    with col2:

        st.subheader("📊 Dashboard")

        orders = get_orders(st.session_state.username)

        if not orders:
            st.info("No orders yet")
        else:

            rows = []

            for idx, order in enumerate(orders, start=1):

                items = json.loads(order[2])

                clean = ", ".join(
                    [f"{i['name']} (x{i['quantity']})" for i in items]
                )

                rows.append({
                    "ID": idx,
                    "Items": clean,
                    "Deadline": order[3],
                    "Status": order[4]
                })

            st.dataframe(pd.DataFrame(rows), use_container_width=True)

            st.metric("Total Orders", len(rows))

# =========================================================
# 👨‍💼 VENDOR PANEL
# =========================================================
elif page == "Vendor Panel":

    if not st.session_state.logged_in:
        st.warning("Please login first")
        st.stop()

    st.title("📦 Vendor Dashboard")

    orders = get_all_orders()

    if not orders:
        st.info("No orders available")
    else:

        for order in orders:

            order_id = order[0]
            username = order[1]
            items = json.loads(order[2])
            deadline = order[3]
            status = order[4]

            st.markdown("---")

            pretty_items = ", ".join(
                [f"{i['name']} (x{i['quantity']})" for i in items]
            )

            st.write(f"👤 User: **{username}**")
            st.write(f"📦 Items: {pretty_items}")
            st.write(f"📅 Deadline: {deadline}")
            st.write(f"📌 Status: {status}")

            new_status = st.selectbox(
                f"Update Status {order_id}",
                ["Received", "In Review", "Dispatched"],
                key=f"status_{order_id}"
            )

            if st.button(f"Update {order_id}", key=f"btn_{order_id}"):

                update_order_status(order_id, new_status)
                st.success(f"Order {order_id} → {new_status}")
                st.rerun()