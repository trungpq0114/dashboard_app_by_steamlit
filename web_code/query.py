def query_get_role(username):
    return f"SELECT role FROM web_data.account_web where username = '{username}'"
def query_get_pos(username):
    return f"SELECT pos FROM web_data.account_web where username = '{username}'"

def query_upsert_mkt_spend(database, name):
    return f"""INSERT INTO {database}.mkt_spent
            (marketer, spend, product_name, channel, `date`, note)
            SELECT marketer, spend, product_name, channel, DATE(CONCAT_WS('-', year, month, day)) `date`, note FROM 
            {database}.mkt_spend_temp_{name} temp
            WHERE COALESCE(marketer,product_name, year, month, day, spend) IS NOT NULL
            AND DATE(CONCAT_WS('-', year, month, day)) is not null
            ON	DUPLICATE KEY UPDATE
            marketer = temp.marketer
            , spend = temp.spend 
            , product_name = temp.product_name 
            , channel = temp.channel 
            , `date` = DATE(CONCAT_WS('-', year, month, day))
            , note = temp.note; 
            """


def query_upsert_mkt_bill(database, name):
    return f"""INSERT INTO {database}.mkt_bill
            (marketer, `type`, `date`, nap, thanh_toan, note)
            SELECT marketer, `type`, DATE(CONCAT_WS('-', year, month, day)) `date`, nap, thanh_toan, note FROM 
            {database}.mkt_bill_temp_{name} temp
            WHERE COALESCE(marketer, type, year, month, day) IS NOT NULL
            AND DATE(CONCAT_WS('-', year, month, day)) is not null
            ON	DUPLICATE KEY UPDATE
                nap = temp.nap
                , thanh_toan = temp.thanh_toan 
                , note = temp.note; 
            """
def all_market():
    all_market = ["hpl_malay","hpl_malay_2","hpl_phil"]
    return all_market

def all_employee():
    query = ""
    for market in all_market():
        query = query + f""" UNION
                            SELECT DISTINCT `user.name` employee, '{market}' market from {market}.employee_temp"""
    return query[6:]


def all_product():
    query = ""
    for market in all_market():
        query = query + f""" UNION
                        SELECT DISTINCT product_name, '{market}' market from {market}.products """
    return query[6:]


def all_bill():
    query = ""
    for market in all_market():
        query = query + f""" UNION
                        SELECT	'{market}' market,	marketer, `date` , type, year(date) year, month(date) month, day(date) day, nap, thanh_toan, note
                                FROM {market}.mkt_bill where nap <> 0 or thanh_toan <> 0 """
    return query[6:]

def all_spend():
    query = ""
    for market in all_market():
        query = query + f""" UNION
                        SELECT marketer, '{market}' market,year(date) year, month(date) month, day(date) day, date, channel, product_name, spend, note FROM {market}.mkt_spent m where spend > 0 """
    return query[6:] + "ORDER BY date DESC"


def all_product_name_mkt():
    query = ""
    for market in all_market():
        query = query + f""" UNION
                        SELECT DISTINCT product_name,marketer  from {market}.vt_mkt """
    return query[6:]