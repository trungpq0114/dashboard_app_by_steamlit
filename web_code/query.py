def query_get_role(username):
    return f"SELECT role FROM web_data.account_web where username = '{username}'"