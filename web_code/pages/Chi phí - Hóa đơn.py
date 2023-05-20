import pickle
from pathlib import Path

import calendar 
from datetime import datetime 

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_option_menu import option_menu
from sqlalchemy import create_engine

# --- PREPARE ---
years = [datetime.today().year, datetime.today().year - 1]
months = list(range(1,13))
days = list(range(1,32))


def html_warning(txt):
    htmlstr1=f"""<p style='background-color:#FA8072;
                                            color:white;
                                            font-size:18px;
                                            border-radius:3px;
                                            line-height:50px;
                                            padding-left:17px;
                                            opacity:1'>
                                            {txt}</style>
                                            <br></p>""" 
    return htmlstr1

credentials = {"usernames":{}}
authenticator = stauth.Authenticate(credentials, "homepage", "random_key", cookie_expiry_days=10)
name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:

    @st.cache_data(ttl=200)
    def get_data(name):
        engine_full = create_engine(f'mysql+pymysql://trungpq:123@103.170.118.214/test'
                    .format(user="trungpq",
                            pw="123",
                            db="test"))
        df = pd.read_sql(f"""SELECT 'Malay' market, year(date) year, month(date) month, m.* FROM hpl.mkt m where marketer = '{name}' and mkt_fee > 0
                        UNION
                        SELECT 'Phil' market,year(date) year, month(date) month, m.* FROM hpl_phil.mkt m where marketer = '{name}' and mkt_fee > 0""", engine_full)
        engine_full.dispose()
        return df
    
    @st.cache_data(ttl=30)
    def get_product_names():
        engine_full = create_engine('mysql+pymysql://trungpq:123@103.170.118.214/test'
                    .format(user="trungpq",
                            pw="123",
                            db="test"))
        df = pd.read_sql(f"""SELECT	DISTINCT San_pham product_name,	'Malay' market from	hpl.vt_mkt
                            UNION ALL
                            SELECT	DISTINCT San_pham product_name,	'Phil' market from hpl_phil.vt_mkt""", engine_full)
        engine_full.dispose()
        return df
    df = get_data(name)
    df_product_names = get_product_names()
    # @st.cache_data()
    def streamlit_menu():
        selected = option_menu(
            menu_title=None,  # required
            options=["Nhập dữ liệu", "Nhập hóa đơn"],  # required
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


    selected = streamlit_menu()

    if selected == "Nhập dữ liệu":
        st.header(f"Nhập chi phí chạy quảng cáo")

        with st.form("entry_form", clear_on_submit=False):
            col1, col2, col3 = st.columns(3)
            day_index = days.index(datetime.today().day)
            month_index = months.index(datetime.today().month)
            col1.selectbox("Chọn ngày:", days, index=day_index , key="day")
            col2.selectbox("Chọn tháng:", months, index=month_index, key="month")
            col3.selectbox("Chọn năm:", years, key="year")

            "---"
            
            col_market, col_source = st.columns(2)
            market = col_market.selectbox("Chọn thị trường:", ["Malay", "Phil"], key="market")

            product_names = df_product_names['product_name'].sort_values().values.tolist()
            product_names = list(set(product_names))
            product_names.insert(0, '')
            
            # product_names.in
            col_source.selectbox("Chọn nền tảng chạy quảng cáo:", ["Facebook", "Tiktok", "Instagram", "Shoppe"], key="source")
            st.selectbox("Chọn sản phẩm:", product_names, key="product_name")
            st.number_input("Tiền chạy:", min_value=0, format="%i", step=10000, key="mkt_fee")
            with st.expander("Tên sản phẩm test nếu có"):
                comment = st.text_area("", placeholder="""Nhập chi tiết tên sản phẩm và link bán hàng: (VD: Quần sịp: linkbanhang.com)""")

            "---"

            submitted = st.form_submit_button("Lưu lại")
            if submitted:
                date = str(st.session_state["year"]) + "-" + str(st.session_state["month"]) + "-" + str(st.session_state["day"])
                source = st.session_state["source"]
                product_name = st.session_state["product_name"]
                mkt_fee = st.session_state["mkt_fee"]
                
                if st.session_state["market"] == "Malay":
                    database_choose = 'hpl'
                else:
                    database_choose = 'hpl_phil'

                upsert_query = f""" 
                
                INSERT INTO {database_choose}.mkt (marketer, `date`, source, product_name, mkt_fee, curency_ratio, budget,comment)
                VALUES('{name}', '{date}', '{source}', '{product_name}', {mkt_fee}, 0, 0, '{comment}')
                ON DUPLICATE KEY UPDATE 
                    mkt_fee = {mkt_fee}
                    , comment = '{comment}';

                
                """
                if product_name == '':
                    st.markdown(html_warning("Vui lòng chọn sản phẩm!"),unsafe_allow_html=True) 
                elif product_name[0:13] != 'SẢN PHẨM TEST':
                    engine_full = create_engine(f'mysql+pymysql://trungpq:123@103.170.118.214/test'
                                                .format(user="trungpq",
                                                        pw="123",
                                                        db="test"))
                    c = engine_full.raw_connection()
                    cursor = c.cursor()
                    result = cursor.execute(upsert_query)
                    c.commit()
                    c.close()
                    st.success("Đã cập nhật dữ liệu!")
                elif len(comment) < 15 or "." not in  comment:
                    st.markdown(html_warning("Vui lòng nhập chi tiết sản phẩm test đúng quy tắc!"),unsafe_allow_html=True) 
                else:
                    engine_full = create_engine(f'mysql+pymysql://trungpq:123@103.170.118.214/test'
                                                .format(user="trungpq",
                                                        pw="123",
                                                        db="test"))
                    c = engine_full.raw_connection()
                    cursor = c.cursor()
                    result = cursor.execute(upsert_query)
                    c.commit()
                    c.close()
                    st.success("Đã cập nhật dữ liệu!")
                    
    if selected == "Nhập hóa đơn":
        st.header("Nhập nạp tài khoản và thanh toán hóa đơn")

        with st.form("entry_form"):
            col1, col2, col3 = st.columns(3)
            day_index = days.index(datetime.today().day)
            month_index = months.index(datetime.today().month)
            col1.selectbox("Chọn ngày:", days, index=day_index , key="day")
            col2.selectbox("Chọn tháng:", months, index=month_index, key="month")
            col3.selectbox("Chọn năm:", years, key="year")
            "---"
            col_market, col_source = st.columns(2)
            market = col_market.selectbox("Chọn thị trường:", ["Malay", "Phil"], key="market")
            col_source.selectbox("Chọn loại thanh toán:", ["Hóa đơn facebook", "Hóa đơn tiktok", "Nạp facebook", "Nạp tiktok"], key="type")
            st.number_input("Tổng tiền:", min_value=0, format="%i", step=10000, key="value")
            with st.expander("Nhập chú thích nếu có:"):
                note = st.text_area("", placeholder="Nhập: '=A1+A2+A3' để tự tính hộ tổng hoá đơn ...")
            "---"
            submitted = st.form_submit_button("Lưu lại")
            if submitted:
                date = str(st.session_state["year"]) + "-" + str(st.session_state["month"]) + "-" + str(st.session_state["day"])
                type = st.session_state["type"]
                value = st.session_state["value"]
                if len(note) >= 1:
                    if note[0] == '=':
                        details = note[1:].split("+",)
                        details_int = [int(x) for x in details]
                        value = sum(details_int)

                if st.session_state["market"] == "Malay":
                    database_choose = 'hpl'
                else:
                    database_choose = 'hpl_phil'

                upsert_query = f""" 
                
                INSERT INTO {database_choose}.bill (marketer, `date`, `type`, value, note) VALUES
                ('{name}', '{date}', '{type}', {value}, '{note}')
                ON DUPLICATE KEY UPDATE 
                value = {value}
                , note = '{note}';
                
                """
                engine_full = create_engine(f'mysql+pymysql://trungpq:123@103.170.118.214/test'
                                            .format(user="trungpq",
                                                    pw="123",
                                                    db="test"))
                c = engine_full.raw_connection()
                cursor = c.cursor()
                result = cursor.execute(upsert_query)
                c.commit()
                c.close()
                st.success("Đã cập nhật dữ liệu!")