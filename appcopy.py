import streamlit as st

# Barra lateral com expander
with st.sidebar.expander("Escolha uma página"):
    page = st.radio("Selecione", ["Página 1", "Página 2", "Página 3", "Análise de Dados"])

if page == "Página 1":
    st.subheader("Bem-vindo à DataPaws!")
    st.write("Esta é a página inicial. Aqui você pode fornecer uma breve introdução ao sistema.")  

elif page == "Página 2":
    st.subheader("Bem-vindo à DataPaws!")
    st.write("Esta é a página inicial. Aqui você pode fornecer uma breve introdução ao sistema.")
    
elif page == "Página 3":
    st.subheader("Bem-vindo à DataPaws!")
    st.write("Esta é a página de testes.")

elif page == "Análise de Dados":
    st.subheader("Análise de Dados")
    st.write("Este é o lugar para análise detalhada dos dados.")
