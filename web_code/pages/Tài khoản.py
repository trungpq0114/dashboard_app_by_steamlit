import streamlit as st
import streamlit_authenticator as stauth
from sqlalchemy import create_engine
import pandas as pd
import streamlit_authenticator as stauth
import json
from query import *
from urllib.parse import quote  

def run_sql(list_query, engine):
    c = engine.raw_connection()
    cursor = c.cursor()
    for i in list_query:
        try:
            result = cursor.execute(i)
        except:
            print("Error")
    c.commit()
    c.close()

credentials = {"usernames":{}}
authenticator = stauth.Authenticate(credentials, "homepage", "random_key", cookie_expiry_days=10)
name, authentication_status, username = authenticator.login("Login", "main")


with open("/root/dashboard_app_by_steamlit/web_code/config_web/config_conn.json") as file:
   config_conn = json.load(file)

host_account = config_conn['database_web_account']['host']
user_account = config_conn['database_web_account']['user']  
password_account = config_conn['database_web_account']['password']

connection_string_account_web = 'mysql+pymysql://%s:%s@103.170.118.214/web_data' % (user_account, quote(password_account))


if authentication_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.title(f"Xin chào {name}")
    st.sidebar.header(f"Username: {username}")
    engine_full = create_engine(f'mysql+pymysql://trungpq:1234@103.170.118.214/test'
                            .format(user="trungpq",
                                    pw="1234",
                                    db="test"))
    @st.cache_data(ttl=150)
    def get_infor(username):
        engine = create_engine(connection_string_account_web.format(user=user_account,
                                                                    pw=password_account,
                                                                    db='web_data'))

        get_role = query_get_role(username)
        c = engine.raw_connection()
        cursor = c.cursor()
        result = cursor.execute(get_role)
        role = cursor.fetchone()[0]
        get_pos = query_get_pos(username)
        c = engine.raw_connection()
        cursor = c.cursor()
        result = cursor.execute(get_pos)
        pos = cursor.fetchone()[0]
        engine.dispose()
        return role, pos
        

    role, pos = get_infor(username)

    @st.cache_data(ttl=20)
    def get_data_account():
        engine = create_engine(f'mysql+pymysql://trungpq:1234@103.170.118.214/test'
                    .format(user="trungpq",
                            pw="1234",
                            db="test"))
        df = pd.read_sql(f""" SELECT * FROM web_data.account_web """, engine)
        engine.dispose()
        return df

    
    @st.cache_data(ttl=20)
    def get_marketer_names():
        engine_full = create_engine('mysql+pymysql://trungpq:1234@103.170.118.214/test'
                    .format(user="trungpq",
                            pw="1234",
                            db="test"))
        df = pd.read_sql(f"""SELECT DISTINCT `user.name` employee from hpl_malay.employee_temp
                        UNION
                        SELECT DISTINCT `user.name` employee from hpl_phil.employee_temp""", engine_full)
        engine_full.dispose()
        return df
    if "role" not in st.session_state:
        st.session_state.role = role
    if st.session_state.role != 'nhan_vien':
        df_account = get_data_account()
        df_emplyee = get_marketer_names()
        st.header(f"Bạn có thể đổi mật khẩu tại đây:")
        with st.form("change_pw_form", clear_on_submit=True):
            st.selectbox("Chọn tài khoản:", df_account['username'].values.tolist(), key="username_to_change")
            with st.expander("Nhập mật khẩu mới?"):
                new_password = st.text_area("", placeholder="Nhập mật khẩu...")
            submitted = st.form_submit_button("Đổi mật khẩu!")
            if submitted:
                username_to_change = st.session_state["username_to_change"]
                hashed_passwords = stauth.Hasher([new_password,]).generate()[0]
                update_password = f""" 
                
                    UPDATE web_data.account_web
                    SET hash_password = '{hashed_passwords}'
                    WHERE username = '{username_to_change}';
                
                """
                
                run_sql([update_password,], engine_full)
                st.success("Đã cập nhật dữ liệu!")

        "---"
        st.header(f"Bạn có thể cập nhật team, leader và link sheet mkt tại đây:")
        with st.form("change_team_form", clear_on_submit=True):
            st.selectbox("Chọn tài khoản:", df_account['username'].values.tolist(), key="username_team_to_change")
            with st.expander("Nhập thêm thông tin tại đây?"):
                st.text("Nhập tên team")
                new_team = st.text_area("", placeholder="Tên team là ...")
                st.text("Nhập link sheet của mkt nếu mkt nhập trên google sheet")
                linksheet_mkt = st.text_area("", placeholder="Link sheet nhập mkt là ...")
                st.selectbox("Là leader của team:", df_account['team'].sort_values().unique(), key="new_leader")
            submitted = st.form_submit_button("Cập nhật leader!")
            if submitted:
                username_team_to_change = st.session_state["username_team_to_change"]
                new_leader = st.session_state["new_leader"]
                update_password = f""" 
                
                    UPDATE web_data.account_web
                    SET team = '{new_team}', leader = '{new_leader}', linksheet_mkt = '{linksheet_mkt}'
                    WHERE username = '{username_team_to_change}';
                
                """
                
                run_sql([update_password,], engine_full)
                st.success("Đã cập nhật dữ liệu!")

        "---"
        st.header(f"Bạn có thể tạo thêm tài khoản mới tại đây:")
        with st.form("create_account_form", clear_on_submit=True):
            col_1, col_2 = st.columns(2)
            market = col_1.selectbox("Chọn thị trường:", ["hpl_malay", "hpl_hil"], key="market")
            col_2.selectbox("Chọn nhân viên:", df_emplyee['employee'].values.tolist(), key="new_employee")
            col_3, col_4 = st.columns(2)
            new_username = col_3.text_area("Nhập email", placeholder="email@...")
            new_password = col_4.text_area("Nhập mật khẩu", placeholder="Nhập mật khẩu...")
            submitted = st.form_submit_button("Tạo tài khoản!")


            if submitted:
                new_employee = st.session_state["new_employee"]
                hashed_passwords = stauth.Hasher([new_password,]).generate()[0]

                if st.session_state["market"] == "Malay":
                    database_choose = 'hpl'
                else:
                    database_choose = 'hpl_phil'

                create_query = f""" 
                
                    INSERT INTO web_data.account_web (name, username, hash_password, pos) 
                    VALUES('{new_employee}', '{new_username}', '{hashed_passwords}', '{database_choose}');

                
                """
                
                run_sql([create_query,], engine_full)
                st.success("Đã tạo tài khoản thành công!")

        st.header(f"Danh sách tài khoản:")
        st.dataframe(df_account, use_container_width=True)
