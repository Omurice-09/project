import streamlit as st

# 상단 탭 배치 (상단 메뉴 바처럼 동작)
tab1, tab2, tab3 = st.tabs(["🗣️ 자유게시판", "📢 공지사항", "👤 사용자 정보"])

with tab1:
    st.write("메인 페이지 내용입니다.")

with tab2:
    st.write("자유게시판 내용입니다.")

with tab3:
    st.write("공지사항 내용입니다.")