import pandas as pd
df = pd.DataFrame(columns=['A', 'B', 'C'])
def calc(row): return 0
try:
    df['CT'] = df.apply(calc, axis=1)
    print("Empty apply works:", df['CT'].shape)
except Exception as e:
    print("Error:", e)

grade_info = pd.Series([], dtype=object)
try:
    res = grade_info.apply(lambda x: x[0])
    print("Empty series apply works:", res.shape)
except Exception as e:
    print("Error:", e)
