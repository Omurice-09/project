import hashlib
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

# DB 연결 및 테이블 생성
conn = sqlite3.connect("school_community_v4.db", check_same_thread=False)
c = conn.cursor()

# 게시글 테이블
c.execute(
    """
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    title TEXT,
    author TEXT,
    content TEXT,
    created_at TEXT
)
"""
)

# 댓글 테이블
c.execute(
    """
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER,
    author TEXT,
    comment TEXT,
    created_at TEXT
)
"""
)
conn.commit()

# 관리자 인증 정보 (필요시 아이디/비밀번호 변경)
ADMIN_USERNAME = "asgus0826" #관리자 아이디
ADMIN_PASSWORD_HASH = hashlib.sha256("afpjz11@@".encode()).hexdigest() #관리자 비밀번호

# 세션 상태 초기화 (관리자 로그인 여부만 관리)
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

st.title("🏫 남창고등학교 커뮤니티")

# 사이드바 - 관리자 로그인 영역
st.sidebar.title("🛡️ 관리자 메뉴")

if st.session_state["is_admin"]:
    st.sidebar.success("👑 관리자 권한으로 로그인됨")
    if st.sidebar.button("로그아웃"):
        st.session_state["is_admin"] = False
        st.rerun()
else:
    with st.sidebar.expander("🔑 관리자 로그인"):
        admin_id = st.text_input("관리자 아이디")
        admin_pw = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            hashed_pw = hashlib.sha256(admin_pw.encode()).hexdigest()
            if admin_id == ADMIN_USERNAME and hashed_pw == ADMIN_PASSWORD_HASH:
                st.session_state["is_admin"] = True
                st.sidebar.success("관리자 로그인 성공!")
                st.rerun()
            else:
                st.sidebar.error("아이디 또는 비밀번호가 틀렸습니다.")

# 메인 메뉴
menu = ["글 목록", "글 작성하기"]
choice = st.sidebar.selectbox("메뉴", menu)

if choice == "글 목록":
    st.subheader("📋 게시글 목록")

    category_filter = st.selectbox(
        "카테고리 선택", ["전체", "자유게시판", "Q&A", "동아리/행사"]
    )

    if category_filter == "전체":
        posts = pd.read_sql_query(
            "SELECT id, category, title, author, created_at FROM posts ORDER BY id DESC",
            conn,
        )
    else:
        posts = pd.read_sql_query(
            "SELECT id, category, title, author, created_at FROM posts WHERE category=? ORDER BY id DESC",
            conn,
            params=(category_filter,),
        )

    if posts.empty:
        st.info("등록된 게시글이 없습니다. 첫 번째 글을 작성해 보세요!")
    else:
        st.dataframe(posts, use_container_width=True)

        selected_id = st.number_input(
            "조회할 글 번호(ID) 입력",
            min_value=1,
            step=1,
            value=int(posts["id"].iloc[0]),
        )

        if st.button("글 읽기"):
            st.session_state["read_post_id"] = selected_id

        if "read_post_id" in st.session_state:
            post_id = st.session_state["read_post_id"]
            c.execute(
                "SELECT category, title, author, content, created_at FROM posts WHERE id=?",
                (post_id,),
            )
            post = c.fetchone()

            if post:
                st.markdown("---")
                st.markdown(f"### [{post[0]}] {post[1]}")
                st.caption(f"작성자: **{post[2]}** | 작성일: {post[4]}")
                st.write(post[3])

                # 관리자 전용 권한 영역 (삭제/수정)
                if st.session_state["is_admin"]:
                    st.markdown("---")
                    st.markdown("#### ⚙️ 관리자 전용 메뉴 (게시글 수정 / 삭제)")
                    col1, col2 = st.columns(2)

                    # 관리자 글 삭제
                    with col1:
                        if st.button("🗑️ 글 삭제하기", key=f"del_{post_id}"):
                            c.execute(
                                "DELETE FROM posts WHERE id=?", (post_id,)
                            )
                            c.execute(
                                "DELETE FROM comments WHERE post_id=?",
                                (post_id,),
                            )
                            conn.commit()
                            st.success("게시글이 삭제되었습니다.")
                            del st.session_state["read_post_id"]
                            st.rerun()

                    # 관리자 글 수정
                    with col2:
                        with st.expander("✏️ 글 내용 수정하기"):
                            with st.form(f"edit_form_{post_id}"):
                                new_title = st.text_input(
                                    "수정할 제목", value=post[1]
                                )
                                new_content = st.text_area(
                                    "수정할 내용", value=post[3]
                                )
                                submit_edit = st.form_submit_button("수정 완료")

                                if submit_edit:
                                    c.execute(
                                        "UPDATE posts SET title=?, content=? WHERE id=?",
                                        (new_title, new_content, post_id),
                                    )
                                    conn.commit()
                                    st.success(
                                        "게시글이 성공적으로 수정되었습니다!"
                                    )
                                    st.rerun()

                # 댓글 영역 (비회원 누구나 작성 가능)
                st.markdown("---")
                st.subheader("💬 댓글")
                comments = pd.read_sql_query(
                    "SELECT author, comment, created_at FROM comments WHERE post_id=? ORDER BY id ASC",
                    conn,
                    params=(post_id,),
                )

                for idx, row in comments.iterrows():
                    st.text(
                        f"{row['author']}: {row['comment']} ({row['created_at']})"
                    )

                with st.form("comment_form", clear_on_submit=True):
                    comment_author = st.text_input("닉네임", value="익명")
                    comment_text = st.text_area("댓글 내용")
                    submit_comment = st.form_submit_button("댓글 달기")

                    if submit_comment and comment_text:
                        now = datetime.now().strftime("%Y-%m-%d %H:%M")
                        c.execute(
                            "INSERT INTO comments (post_id, author, comment, created_at) VALUES (?, ?, ?, ?)",
                            (post_id, comment_author, comment_text, now),
                        )
                        conn.commit()
                        st.success("댓글이 등록되었습니다!")
                        st.rerun()
            else:
                st.error("해당 글 번호가 존재하지 않습니다.")

elif choice == "글 작성하기":
    st.subheader("✍️ 새 글 작성")

    # 비회원 누구나 작성 가능
    with st.form("post_form", clear_on_submit=True):
        category = st.selectbox(
            "카테고리", ["자유게시판", "Q&A", "동아리/행사"]
        )
        author = st.text_input("작성자 닉네임", value="익명")
        title = st.text_input("제목")
        content = st.text_area("내용", height=200)
        submitted = st.form_submit_button("게시글 등록")

        if submitted:
            if title and content:
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                c.execute(
                    "INSERT INTO posts (category, title, author, content, created_at) VALUES (?, ?, ?, ?, ?)",
                    (category, title, author, content, now),
                )
                conn.commit()
                st.success("게시글이 성공적으로 등록되었습니다!")
            else:
                st.warning("제목과 내용을 모두 입력해주세요.")