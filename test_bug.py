import pandas as pd
import numpy as np
df = pd.DataFrame({'A': [1.5, 2.5], 'B': ['Max', 'Min'], 'C': [np.nan, 3.0]})
res = df.iloc[0].astype(str).str.lower().values
print("Values:", res)
print("Types:", [type(x) for x in res])
