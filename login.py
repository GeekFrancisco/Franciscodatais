import streamlit as st

def verificar_login(username, password):
    return username == "admin" and password == "senha123"

def tela_login():
    st.markdown('<div class="login">', unsafe_allow_html=True)
    st.markdown('<h1>Login</h1>', unsafe_allow_html=True)

    with st.form(key='login_form', clear_on_submit=True):
        username = st.text_input("Usuário", placeholder="Username")
        password = st.text_input("Senha", type="password", placeholder="Password")
        submit_button = st.form_submit_button("Entrar")

    st.markdown('</div>', unsafe_allow_html=True)

    if submit_button:
        if verificar_login(username, password):
            st.session_state.login = True
            st.success("Login realizado com sucesso!")
        else:
            st.error("Usuário ou senha incorretos.")
