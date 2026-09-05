import pandas as pd
import plotly.express as px
df = pd.DataFrame({'A': [1,2,3], 'B': [4,5,6], 'id': [1,2,3]})
try:
    fig = px.scatter(df, x='A', y='B', hover_data=['id'], trendline="ols")
    print("Scatter with OLS works")
except Exception as e:
    print("Error in scatter:", type(e).__name__, e)
