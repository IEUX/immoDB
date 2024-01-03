import numpy as np
import pandas as pd
import sqlite3

database = "transaction.sqlite"
conn = sqlite3.connect(database)

arrays = dict(np.load("transactions.npz"))
data = {k: [s.decode("utf-8") for s in v.tobytes().split(b"\x00")] if v.dtype == np.uint8 else v for k, v in arrays.items()}
df = pd.DataFrame.from_dict(data)
df.to_sql(name="transactions", con=conn, if_exists='replace')
conn.close()