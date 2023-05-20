def query_get_role(username):
    return f"SELECT role FROM web_data.account_web where username = '{username}'"
def query_get_pos(username):
    return f"SELECT pos FROM web_data.account_web where username = '{username}'"

def query_upsert_mkt_spend(database):
    return f"""INSERT INTO {database}.mkt_spent
            (marketer, spend, product_name, channel, `date`, id, note)
            SELECT marketer, spend, product_name, channel, DATE(CONCAT_WS('-', year, month, day)) `date`, COALESCE(id, CONCAT(CONCAT_WS('-', year, month, day), "|","Facebook","|",marketer,"|",product_name)) id, note FROM 
            {database}.mkt_spend_temp temp
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
