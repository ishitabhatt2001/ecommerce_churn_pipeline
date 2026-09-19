import streamlit as st

conn = st.connection("postgresql", type="sql")
df = conn.query("SELECT now() AS server_time;", ttl=0)
st.write("Connected!")
st.dataframe(df)