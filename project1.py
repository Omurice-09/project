import streamlit as st

# 페이지 기본 설정 (넓은 화면 레이아웃)
st.set_page_config(page_title="커뮤니티 게시판", layout="wide")

# 1. 사이드바 카테고리 메뉴 구성
st.sidebar.title("📌 게시판 카테고리")
category = st.sidebar.radio(
    "이동할 게시판을 선택하세요",
    ["🏠 전체 홈", "💬 자유게시판", "❓ 질문게시판", "💡 정보공유게시판", "📢 공지사항"]
)

# 2. 카테고리별 화면 전환 처리
if category == "🏠 전체 홈":
    st.title("🏠 커뮤니티 메인 홈")
    st.write("원하는 게시판을 왼쪽 사이드바에서 선택해 보세요!")
    
    # 홈 화면에 최신글 요약 등을 보여주는 구역
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔥 인기 게시글")
        
    with col2:
        st.subheader("📢 최근 공지")
        

elif category == "💬 자유게시판":
    st.title("💬 자유게시판")
    st.caption("자유롭게 이야기를 나누는 공간입니다.")
    st.divider()
    
    # 글 작성 버튼 예시
    if st.button("✏️ 글쓰기"):
        st.info("글 작성 폼 들어갈 자리")

    # 게시글 목록 영역
    st.subheader("📄 게시글 목록")

elif category == "❓ 질문게시판":
    st.title("❓ 질문게시판")
    st.caption("궁금한 점을 서로 묻고 답하는 공간입니다.")
    st.divider()

    if st.button("✏️ 글쓰기"):
        st.info("글 작성 폼 들어갈 자리")
    
    st.subheader("📄 게시글 목록")

elif category == "💡 정보공유게시판":
    st.title("💡 정보공유게시판")
    st.caption("유용한 정보를 공유하는 공간입니다.")
    st.divider()

    if st.button("✏️ 글쓰기"):
            st.info("글 작성 폼 들어갈 자리")
    
    st.subheader("📄 게시글 목록")

elif category == "📢 공지사항":
    st.title("📢 공지사항")
    st.divider()