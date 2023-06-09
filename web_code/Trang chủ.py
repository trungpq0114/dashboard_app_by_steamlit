from urllib.parse import quote  
import pickle
from pathlib import Path

import calendar 
from datetime import datetime 
import json
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_option_menu import option_menu
from sqlalchemy import create_engine
from query import *

st.set_page_config(page_title="Sales Dashboard", page_icon=":bar_chart:", layout="wide")

with open("/root/dashboard_app_by_steamlit/web_code/config_web/config_conn.json") as file:
   config_conn = json.load(file)

host_account = config_conn['database_web_account']['host']
user_account = config_conn['database_web_account']['user']
password_account = config_conn['database_web_account']['password']

connection_string_web_account = 'mysql+pymysql://%s:%s@103.170.118.214/web_data' % (user_account, quote(password_account))
# --- USER AUTHENTICATION ---
engine = create_engine(connection_string_web_account.format(user=user_account,
                               pw=password_account,
                               db='web_data'))
account_df = pd.read_sql('SELECT * FROM web_data.account_web where status is null or status = 1', engine)
engine.dispose()
names = account_df['name'].values.tolist()
usernames = account_df['username'].values.tolist()
hashed_passwords = account_df['hash_password'].values.tolist()

credentials = {"usernames":{}}
        
for uname,name,pwd in zip(usernames,names,hashed_passwords):
    user_dict = {"name": name, "password": pwd}
    credentials["usernames"].update({uname: user_dict})

authenticator = stauth.Authenticate(credentials, "homepage", "random_key", cookie_expiry_days=10)


name, authentication_status, username = authenticator.login("Login", "main")


if authentication_status == False:
    st.error("Username/password is incorrect")

if authentication_status == None:
    st.warning("Please enter your username and password")

# --- PREPARE ---
years = [datetime.today().year, datetime.today().year - 1]
months = list(range(1,13))
days = list(range(1,32))

if authentication_status:
    # Chạy list query:
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
    # @st.cache_data(ttl=1500)    
    def get_infor(username):
        engine = create_engine(connection_string_web_account.format(user=user_account,
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
    if "role" not in st.session_state:
        st.session_state.role = role
    
    # @st.cache_data(ttl=15)
    def get_data_mkt_spend(name, role):

        engine_full = create_engine(f'mysql+pymysql://trungpq:1234@103.170.118.214/test'
                    .format(user="trungpq",
                            pw="1234",
                            db="test"))
        if role == 'admin':
            df = pd.read_sql(all_spend(), engine_full)
        else:
            df = pd.read_sql(f"""SELECT marketer, '{pos}' market, year(date) year, month(date) month, day(date) day, date, channel, product_name, spend, note FROM {pos}.mkt_spent m where marketer = '{name}' and spend > 0
                                ORDER BY date DESC""", engine_full) 
        engine_full.dispose()
        return df
    
    # @st.cache_data(ttl=15)
    def get_data_mkt_bill(name, role):
        engine_full = create_engine(f'mysql+pymysql://trungpq:1234@103.170.118.214/test'
                    .format(user="trungpq",
                            pw="1234",
                            db="test"))
        if role == 'admin':
            df = pd.read_sql(all_bill(), engine_full)
        else:
            df = pd.read_sql(f"""SELECT	'{pos}' market,	marketer, `date` , type, year(date) year, month(date) month, day(date) day, nap, thanh_toan, note
                                FROM {pos}.mkt_bill WHERE  marketer = '{name}' and (nap <> 0 or thanh_toan <> 0) """, engine_full)            
        engine_full.dispose()
        return df

    # @st.cache_data(ttl=500)
    def get_product_names():
        engine_full = create_engine('mysql+pymysql://trungpq:1234@103.170.118.214/test'
                    .format(user="trungpq",
                            pw="1234",
                            db="test"))
        df = pd.read_sql(all_product_name_mkt(), engine_full)
        engine_full.dispose()
        return df
    
    # @st.cache_data(ttl=500)
    def get_marketer_names():
        engine_full = create_engine('mysql+pymysql://trungpq:1234@103.170.118.214/test'
                    .format(user="trungpq",
                            pw="1234",
                            db="test"))
        df = pd.read_sql(all_employee(), engine_full)
        engine_full.dispose()
        return df
    
    def streamlit_menu():
        selected = option_menu(
            menu_title=None,  # required
            options=["Chi phí ADS", "Lịch sử hóa đơn", "Check Campain"],  # required
            icons=["house", "book", "envelope"],  # optional
            menu_icon="cast",  # optional
            default_index=0,  # optional
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#198754"},
                "icon": {"color": "orange", "font-size": "25px"},
                "nav-link": {
                    "font-size": "25px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "#0083B8   ",
                },
                "nav-link-selected": {"background-color": "#0083B8", "font-family": "Source Sans Pro"},
            },
        )
        return selected

    df = get_data_mkt_spend(name, st.session_state['role'])
    if df.shape[0] == 0:
        df.loc[len(df.index)] = [name, 'hpl_malay', 2023 ,1 , 1, '', '', '', 0, 'Sản phẩm A: abcshop.com'] 
    df_hoa_don = get_data_mkt_bill(name, st.session_state['role'])
    df_product_names = get_product_names()
    df_marketer_names = get_marketer_names()
    selected = streamlit_menu()
    authenticator.logout("Logout", "sidebar")
    st.sidebar.title(f"Xin chào {name}")
    st.sidebar.header(f"Username: {username}")
    st.sidebar.header("Bộ lọc tại đây:")

    market = st.sidebar.multiselect(
        "Chọn thị trường:",
        options=all_market(),
        default=df["market"].unique()
    )

    year = st.sidebar.multiselect(
        "Chọn năm:",
        options=df["year"].sort_values().unique(),
        default=df["year"].max()
    )

    month = st.sidebar.multiselect(
        "Chọn tháng:",
        options=months,
        default=df.loc[df['year'] == df["year"].max()]["month"].max()
    )
    
    if role == "admin":
        list_mkt = df_marketer_names["employee"].sort_values().values.tolist()
    else:
        list_mkt = [] 
    list_mkt.append(name)

    container = st.sidebar.container()
    all = st.sidebar.checkbox("Chọn tất cả")
    
    if all:
        marketer = container.multiselect("Chọn marketer:",
            list_mkt, list_mkt)
    else:
        marketer =  container.multiselect("Chọn marketer:",
            list_mkt, name)
    
    if selected == "Chi phí ADS":
        # ---- SIDEBAR ----

        channel = st.sidebar.multiselect(
            "Chọn nguồn quảng cáo:",
            options=df["channel"].unique(),
            default=df["channel"].unique()
        )

        if st.session_state['role'] == "admin":
            list_product_list = df_product_names["product_name"].sort_values().unique()
        else:
            list_product_list = df_product_names.loc[df_product_names['marketer'] == name]["product_name"].sort_values().unique()

        list_product_list = list(list_product_list)
        list_product_list.extend(['SP test 1','SP test 2','SP test 3','SP test 4','SP test 5','SP test 6'])

        product_name = st.sidebar.multiselect(
            "Chọn sản phẩm đã chạy:",
            options=list_product_list,
            default=list_product_list,
        )

        df_selection = df.query(
            """channel == @channel & product_name == @product_name & month == @month & year == @year & market == @market & marketer == @marketer"""
        )
        
        # ---- MAINPAGE ----
        st.header(f":bar_chart: Chi tiết chi phí ADS - {name}")
        st.markdown("##")
        # TOP KPI's
        total_fee = int(df_selection["spend"].sum())
        average_rating = round(df_selection["channel"].nunique(), 2)
        count_product = round(df_selection["product_name"].nunique(), 2)

        left_column, middle_column, right_column = st.columns(3)
        with left_column:
            st.caption("**Tổng chi phí:**")
            st.subheader(f"{total_fee:,} vnđ")
        with middle_column:
            st.caption("**Tỉ giá trung bình:**")
            st.subheader(f"vnđ/x: {average_rating:,}")
        with right_column:
            st.caption("**Số sản phẩm chạy:**")
            st.subheader(f"{count_product} sản phẩm")

        st.markdown("""---""")
        st.dataframe(df_selection[['market','marketer','year','month','day','channel','product_name','spend','note']], use_container_width=True, hide_index = True)

        engine_full = create_engine(f'mysql+pymysql://trungpq:1234@103.170.118.214/test'
                    .format(user="trungpq",
                            pw="1234",
                            db="test"))
        with st.form("edit_mkt_spend", clear_on_submit=True):
            with st.expander("Nhập chi phí Marketing?"):
                st.text(""" *Lưu ý: Mỗi lần sửa, hãy chọn một STT bất kì cho mỗi dòng""")
                
                df_to_edit = df_selection[['month','day','channel','product_name', 'spend','note']]
                df_to_edit.index.name='STT'
                edited_df = st.data_editor(df_to_edit
                    , column_config={
                            "day": st.column_config.NumberColumn(
                                "Ngày",
                                help="Ngày chạy quảng cáo",
                                min_value=1,
                                max_value=31
                            ),
                            "month": st.column_config.NumberColumn(
                                "Tháng",
                                help="Tháng chạy quảng cáo",
                                min_value=1,
                                max_value=12
                            ),
                            "channel": st.column_config.SelectboxColumn(
                                "Kênh quảng cáo",
                                help="Chọn kênh quảng cáo",
                                width="medium",
                                options=['Facebook', 'Tiktok'],
                            ),
                            "spend": st.column_config.NumberColumn(
                                "Chi phí",
                                help="Nếu xoá hãy sửa chi phí về 0?",
                                min_value=0,
                                max_value=100000000
                            ),
                            "product_name": st.column_config.SelectboxColumn(
                                "Tên sản phẩm",
                                help="Lựa chọn tên sản phẩm",
                                width="medium",
                                options=list_product_list,
                            ),
                            "note": st.column_config.TextColumn(
                                "Chú thích",
                                help="Nếu là sản phẩm test, hãy nhập đầy đủ cả link và landing page",
                                default="www.linktest.com : tensanphamtest",
                                max_chars=500,
                                validate="^[a-zA-]+\.[a-zA-]+\..+",
                            )
                            }
                    , hide_index = False ,use_container_width=True, num_rows='dynamic', key = "Check").reset_index()
            # st.text(st.session_state['Check'])
            # st.dataframe(edited_df)
            edited_df['marketer'] = name
            edited_df['year'] = 2023
            edited_df = edited_df.replace(r'^\s*$', np.nan , regex=True)
            st.session_state['edited_df'] = edited_df
            submitted = st.form_submit_button("Cập nhật chi phí MKT!")
            if submitted:
                if st.session_state["Check"] != {'edited_cells': {}, 'added_rows': [], 'deleted_rows': []}:
                    st.session_state['edited_df'].to_sql(f'mkt_spend_temp_{str((hash(name) % 10**8))}', con = engine_full, if_exists = 'replace', chunksize = 1000, schema = pos, index=False)
                    engine_full.dispose()
                    run_sql([query_upsert_mkt_spend(pos, str((hash(name) % 10**8))), ], engine_full)
                    st.success("Đã cập nhật, hãy kiểm tra lại dữ liệu!")
        st.markdown("""---""")


    if selected == "Lịch sử hóa đơn":
        type = st.sidebar.multiselect(
            "Chọn thẻ:",
            options=df_hoa_don["type"].unique(),
            default=df_hoa_don["type"].unique()
        )
        st.header(f"Danh sách hóa đơn đã nạp")

        df_selection_hoa_don = df_hoa_don.query(
            """month == @month & year == @year & market == @market & marketer == @marketer & type == @type"""
        )

        df_selection_tong_hoa_don = df_hoa_don.query(
            """marketer == @marketer"""
        )

        st.markdown("##")
        # TOP KPI's
        tong_du_no = int(df_selection_tong_hoa_don["nap"].sum()) - int(df_selection_tong_hoa_don["thanh_toan"].sum())
        thay_doi = int(df_selection_hoa_don["nap"].sum()) - int(df_selection_hoa_don["thanh_toan"].sum())
        nap_trong_ki = int(df_selection_hoa_don["nap"].sum())
        thanh_toan_trong_ki = int(df_selection_hoa_don["thanh_toan"].sum())
        column_1, column_2 = st.columns(2)
        column_3, column_4 = st.columns(2)
        with column_1:
            st.caption("**Tổng dư - nợ:**")
            st.subheader(f"{tong_du_no:,} vnđ")
        with column_2:
            st.caption("**Thay đổi trong kì:**")
            st.subheader(f"{thay_doi:,} vnđ")
        with column_3:
            st.caption("**Tổng nạp trong kì:**")
            st.subheader(f"{nap_trong_ki:,} vnđ")
        with column_4:
            st.caption("**Tổng thanh toán trong kì:**")
            st.subheader(f"{thanh_toan_trong_ki:,} vnđ")
        st.markdown("""---""")

        st.dataframe(df_selection_hoa_don[['market','marketer','date','type','nap', 'thanh_toan','note']], use_container_width=True)

        st.markdown("""---""")
        
        engine_full = create_engine(f'mysql+pymysql://trungpq:1234@103.170.118.214/test'
                    .format(user="trungpq",
                            pw="1234",
                            db="test"))
        
        with st.form("edit_mkt_bill", clear_on_submit=True):
            with st.expander("Nhập hoá đơn Marketing?"):
                st.text(""" *Lưu ý: Mỗi lần sửa, hãy chọn một STT bất kì cho mỗi dòng""")
                
                df_bill_to_edit = df_selection_hoa_don[['month','day','type','nap', 'thanh_toan','note']]

                df_bill_to_edit.index.name='STT'
                edited_df_bill = st.data_editor(df_bill_to_edit, hide_index = False,use_container_width=True, num_rows='dynamic')
            edited_df_bill['marketer'] = name
            edited_df_bill['year'] = 2023
            edited_df_bill = edited_df_bill.replace(r'^\s*$', np.nan , regex=True)
            st.session_state['edited_df_bill'] = edited_df_bill
            submitted = st.form_submit_button("Cập nhật chi phí MKT!")
            if submitted:
                st.session_state['edited_df_bill'].to_sql(f'mkt_bill_temp_{str((hash(name) % 10**8))}', con = engine_full, if_exists = 'replace', chunksize = 1000, schema = pos, index=False)
                run_sql([query_upsert_mkt_bill(pos, str((hash(name) % 10**8))), ], engine_full)
                st.success("Đã cập nhật, hãy kiểm tra lại dữ liệu!")
        # SALES BY PRODUCT LINE [BAR CHART]
        sales_by_product_line = df_selection_hoa_don.groupby(by=["date"]).sum()[["nap"]].sort_values(by="date")
        fig_product_sales = px.bar(
            sales_by_product_line,
            x="nap",
            y=sales_by_product_line.index,
            orientation="h",
            title="<b>Tổng hợp nạp</b>",
            color_discrete_sequence=["#0083B8"] * len(sales_by_product_line),
            template="plotly_white",
        )
        fig_product_sales.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=(dict(showgrid=False))
        )

        # SALES BY HOUR [BAR CHART]
        sales_by_date = df_selection_hoa_don.groupby(by=["date"]).sum()[["thanh_toan"]].sort_values(by="date")
        fig_hourly_sales = px.bar(
            sales_by_date,
            x=sales_by_date.index,
            y="thanh_toan",
            title="<b>Tổng hợp thanh toán</b>",
            color_discrete_sequence=["#0083B8"] * len(sales_by_date),
            template="plotly_white",
        )
        fig_hourly_sales.update_layout(
            xaxis=dict(tickmode="linear"),
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=(dict(showgrid=False)),
        )
        

        left_column, right_column = st.columns(2)
        left_column.plotly_chart(fig_hourly_sales, use_container_width=True)
        right_column.plotly_chart(fig_product_sales, use_container_width=True)

