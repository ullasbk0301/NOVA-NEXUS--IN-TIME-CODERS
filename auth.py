from database import add_user, get_user

# =============================
# REGISTER (WITH ROLE SELECTION)
# =============================
def register_user(username, password, role):
    add_user(username, password, role)

# =============================
# LOGIN
# =============================
def login_user(username, password):

    user = get_user(username)

    if user and user[1] == password:
        return {
            "username": user[0],
            "role": user[2]
        }

    return None