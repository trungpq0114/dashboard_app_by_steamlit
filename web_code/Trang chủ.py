from urllib.parse import quote  
import pickle
from pathlib import Path

import calendar 
from datetime import datetime 
import json
import pandas as pd
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
account_df = pd.read_sql('SELECT * FROM web_data.account_web', engine)
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
    # @st.cache_data(ttl=15)    
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
                            pw="123",
                            db="test"))
        if role == 'admin':
            df = pd.read_sql(f"""SELECT id, marketer, 'hpl_malay' market, year(date) year, month(date) month, day(date) day, date, channel, product_name, spend, note FROM hpl_malay.mkt_spent m where spend > 0
                            UNION
                            SELECT id, marketer, 'hpl_phil' market,year(date) year, month(date) month, day(date) day, date, channel, product_name, spend, note FROM hpl_phil.mkt_spent m where spend > 0
                            ORDER BY date DESC""", engine_full)
        else:
            df = pd.read_sql(f"""SELECT id, marketer, '{pos}' market, year(date) year, month(date) month, day(date) day, date, channel, product_name, spend, note FROM {pos}.mkt_spent m where marketer = '{name}' and spend > 0
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
            df = pd.read_sql(f"""SELECT	'hpl_malay' market,	marketer, `date` , type, year(date) year, month(date) month, 
                                    case when LEFT(type,3) = "Nạp" then value
                                        when LEFT(type,3) = "Hóa" then value *-1
                                    end thay_doi, note
                                FROM hpl_malay.mkt_bill
                                UNION ALL
                                SELECT	'hpl_phil' market,	marketer, `date` , type, year(date) year, month(date) month, 
                                    case when LEFT(type,3) = "Nạp" then value
                                        when LEFT(type,3) = "Hóa" then value *-1
                                    end thay_doi, note
                                FROM hpl_phil.mkt_bill""", engine_full)
        else:
            df = pd.read_sql(f"""SELECT	'{pos}' market,	marketer, `date` , type, year(date) year, month(date) month, 
                                    case when LEFT(type,3) = "Nạp" then value
                                        when LEFT(type,3) = "Hóa" then value *-1
                                    end thay_doi, note
                                FROM {pos}.mkt_bill WHERE  marketer = '{name}' """, engine_full)            
        engine_full.dispose()
        return df

    # @st.cache_data(ttl=15)
    def get_product_names():
        engine_full = create_engine('mysql+pymysql://trungpq:1234@103.170.118.214/test'
                    .format(user="trungpq",
                            pw="1234",
                            db="test"))
        df = pd.read_sql(f"""SELECT DISTINCT product_name, 'hpl_malay' market from hpl_malay.products
                        UNION
                        SELECT DISTINCT product_name, 'hpl_phil' market from hpl_phil.products""", engine_full)
        engine_full.dispose()
        return df
    
    # @st.cache_data(ttl=15)
    def get_marketer_names():
        engine_full = create_engine('mysql+pymysql://trungpq:1234@103.170.118.214/test'
                    .format(user="trungpq",
                            pw="1234",
                            db="test"))
        df = pd.read_sql(f"""SELECT DISTINCT marketer from hpl_malay.dm_mkt
                        UNION
                        SELECT DISTINCT marketer from hpl_phil.dm_mkt""", engine_full)
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

    df = get_data_mkt_spend(name, st.session_state.role)
    if df.shape[0] == 0:
        df.loc[len(df.index)] = ['', name, 'hpl_malay', 1945 ,1 , 1, '', '', '', 0, 'Sản phẩm A: abcshop.com'] 
    df_hoa_don = get_data_mkt_bill(name, st.session_state.role)
    df_product_names = get_product_names()
    df_marketer_names = get_marketer_names()
    selected = streamlit_menu()
    if username == 'tester01':
        st.dataframe(df)
        st.header(df.shape[0])
    authenticator.logout("Logout", "sidebar")
    st.sidebar.title(f"Xin chào {name}")
    st.sidebar.header("Bộ lọc tại đây:")

    market = st.sidebar.multiselect(
        "Chọn thị trường:",
        options=["hpl_malay", "hpl_phil"],
        default=df["market"].unique()
    )

    year = st.sidebar.multiselect(
        "Chọn năm:",
        options=df["year"].unique(),
        default=df["year"].max()
    )

    month = st.sidebar.multiselect(
        "Chọn tháng:",
        options=months,
        default=df.loc[df['year'] == df["year"].max()]["month"].max()
    )
    
    if role == "admin":
        list_mkt = df_marketer_names["marketer"].sort_values().values.tolist()
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
        if st.session_state.role == "admin":
            list_product_list = df["product_name"].sort_values().unique()
        else:
            list_product_list = df.loc[df['marketer'] == name]["product_name"].sort_values().unique()
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

        st.dataframe(df_selection[['market','marketer','year','month','day','channel','product_name','spend','note']], use_container_width=True)

        
        engine_full = create_engine(f'mysql+pymysql://trungpq:1234@103.170.118.214/test'
                    .format(user="trungpq",
                            pw="123",
                            db="test"))
        with st.form("edit_mkt_spend", clear_on_submit=False):
            with st.expander("Nhập chi phí Marketing?"):
                st.text(""" Vui lòng nhập cột đầu tiên trước cột ID!!!""")
                edited_df = st.experimental_data_editor(df_selection[['id', 'month','day','channel','product_name', 'spend','note']], use_container_width=True, num_rows='dynamic')
                edited_df['marketer'] = name
                edited_df['year'] = 2023
                st.session_state.edited_df = edited_df
            submitted = st.form_submit_button("Cập nhật chi phí MKT!")
            if submitted:
                st.session_state.edited_df.to_sql('mkt_spend_temp', con = engine_full, if_exists = 'replace', chunksize = 1000, schema = pos, index=False)
                engine_full.dispose()
                c = engine_full.raw_connection()
                cursor = c.cursor()
                result = cursor.execute(query_upsert_mkt_spend(pos))
                c.commit()
                c.close()
                engine_full.dispose()
                st.success("Đã cập nhật, hãy kiểm tra lại dữ liệu!")
        st.markdown("""---""")

        # SALES BY PRODUCT LINE [BAR CHART]
        sales_by_product_line = (
            df_selection.groupby(by=["product_name"]).sum()[["spend"]].sort_values(by="spend")
        )
        fig_product_sales = px.bar(
            sales_by_product_line,
            x="spend",
            y=sales_by_product_line.index,
            orientation="h",
            title="<b>Chi phí QC theo các sản phẩm</b>",
            color_discrete_sequence=["#0083B8"] * len(sales_by_product_line),
            template="plotly_white",
            text_auto=True
        )
        fig_product_sales.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=(dict(showgrid=False))
        )

        # SALES BY HOUR [BAR CHART]
        sales_by_hour = df_selection.groupby(by=["date"]).sum()[["spend"]].sort_values(by="spend")
        fig_hourly_sales = px.bar(
            sales_by_hour,
            x=sales_by_hour.index,
            y="spend",
            title="<b>Chi phí QC theo ngày</b>",
            color_discrete_sequence=["#0083B8"] * len(sales_by_hour),
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


        # SALES BY HOUR [BAR CHART]
        sales_by_hour = df_selection.groupby(by=["marketer"]).sum()[["spend"]].sort_values(by="spend")
        fig_marketer_mktfee = px.bar(
            sales_by_hour,
            x=sales_by_hour.index,
            y="spend",
            title="<b>Chi phí theo Marketer</b>",
            color_discrete_sequence=["#0083B8"] * len(sales_by_hour),
            template="plotly_white",
            text_auto=True
        )
        fig_marketer_mktfee.update_layout(
            xaxis=dict(tickmode="linear"),
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=(dict(showgrid=False)),
        )

        st.plotly_chart(fig_marketer_mktfee, use_container_width=True)
        # ---- HIDE STREAMLIT STYLE ----
        hide_st_style = """
                    <style>
                    #MainMenu {visibility: hidden;}
                    footer {visibility: hidden;}
                    header {visibility: hidden;}
                    </style>
                    """
        st.markdown(hide_st_style, unsafe_allow_html=True)
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
        tong_du_no = int(df_selection_tong_hoa_don["thay_doi"].sum())
        thay_doi = int(df_selection_hoa_don["thay_doi"].sum())
        hoa_don_facebook = int(df_selection_hoa_don.loc[df_selection_hoa_don['type'] == "Hóa đơn facebook"]["thay_doi"].sum())
        hoa_don_tiktok = int(df_selection_hoa_don.loc[df_selection_hoa_don['type'] == "Hóa đơn tiktok"]["thay_doi"].sum())
        nap_tiktok = int(df_selection_hoa_don.loc[df_selection_hoa_don['type'] == "Nạp tiktok"]["thay_doi"].sum())
        nap_facebook = int(df_selection_hoa_don.loc[df_selection_hoa_don['type'] == "Nạp facebook"]["thay_doi"].sum())

        column_1, column_2, column_3 = st.columns(3)
        column_4, column_5, column_6, = st.columns(3)
        with column_1:
            st.caption("**Tổng dư - nợ:**")
            st.subheader(f"{tong_du_no:,} vnđ")
        with column_2:
            st.caption("**Thanh toán facebook:**")
            st.subheader(f"{hoa_don_facebook:,} vnđ")
        with column_3:
            st.caption("**Thanh toán tiktok:**")
            st.subheader(f"{hoa_don_tiktok:,} vnđ")
        with column_4:
            st.caption("**Thay đổi:**")
            st.subheader(f"{thay_doi:,} vnđ")
        with column_5:
            st.caption("**Tiền nạp facebook:**")
            st.subheader(f"{nap_facebook:,} vnđ")
        with column_6:
            st.caption("**Tiền nạp tiktok:**")
            st.subheader(f"{nap_tiktok:,} vnđ")

        st.markdown("""---""")

        st.dataframe(df_selection_hoa_don[['market','marketer','date','type','thay_doi','note']], use_container_width=True)

        st.markdown("""---""")

        # SALES BY PRODUCT LINE [BAR CHART]
        sales_by_product_line = (
            df_selection_hoa_don.groupby(by=["date"]).sum()[["thay_doi"]].sort_values(by="date")
        )
        fig_product_sales = px.bar(
            sales_by_product_line,
            x="thay_doi",
            y=sales_by_product_line.index,
            orientation="h",
            title="<b>Hóa đơn theo ngày</b>",
            color_discrete_sequence=["#0083B8"] * len(sales_by_product_line),
            template="plotly_white",
        )
        fig_product_sales.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=(dict(showgrid=False))
        )

        # SALES BY HOUR [BAR CHART]
        sales_by_hour = df_selection_hoa_don.groupby(by=["type"]).sum()[["thay_doi"]].sort_values(by="type")
        fig_hourly_sales = px.bar(
            sales_by_hour,
            x=sales_by_hour.index,
            y="thay_doi",
            title="<b>Hóa đơn theo loại</b>",
            color_discrete_sequence=["#0083B8"] * len(sales_by_hour),
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



    if selected == "Check campain":
        st.header(f"You have selected {selected}")
    