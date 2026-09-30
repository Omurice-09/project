import streamlit as st
import hashlib

# 비밀번호 안전 암호화 (SHA-256 해싱)
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

# 회원가입 및 로그인 화면 기능
def show_login_page():
    st.title("보안 로그인 시스템")

    menu = ["로그인", "회원가입"]
    choice = st.sidebar.selectbox("메뉴 선택", menu)

    # 임시 사용자 데이터 저장 (실제 실행 시 메모리에 유지)
    if 'user_db' not in st.session_state:
        st.session_state['user_db'] = {}

    if choice == "로그인":
        st.subheader("로그인 영역")

        username = st.text_input("아이디")
        password = st.text_input("비밀번호", type='password')

        if st.button("로그인"):
            hashed_pswd = make_hashes(password)
            
            # 사용자 검증 (보안: 아이디/비밀번호 오답 메시지 모호화)
            if username in st.session_state['user_db'] and check_hashes(password, st.session_state['user_db'][username]):
                st.success(f"{username}님, 환영합니다!")
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
            else:
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

    elif choice == "회원가입":
        st.subheader("새 계정 만들기")
        new_user = st.text_input("사용할 아이디")
        new_password = st.text_input("사용할 비밀번호", type='password')

        if st.button("회원가입"):
            if new_user in st.session_state['user_db']:
                st.warning("이미 존재하는 아이디입니다.")
            elif new_user == "" or new_password == "":
                st.warning("아이디와 비밀번호를 모두 입력해 주세요.")
            else:
                # 비밀번호 평문 저장 방지 (해싱 후 저장)
                st.session_state['user_db'][new_user] = make_hashes(new_password)
                st.success("회원가입이 완료되었습니다! 로그인 메뉴로 이동해 주세요.")
