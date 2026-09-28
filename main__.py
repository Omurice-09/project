import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path
from uuid import uuid4
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
    created_at TEXT,
    author_password_hash TEXT
)
"""
)

# 기존 DB에도 사진 경로 컬럼을 추가
c.execute("PRAGMA table_info(posts)")
post_columns = {row[1] for row in c.fetchall()}
if "image_path" not in post_columns:
    c.execute("ALTER TABLE posts ADD COLUMN image_path TEXT")
if "author_password_hash" not in post_columns:
    c.execute("ALTER TABLE posts ADD COLUMN author_password_hash TEXT")

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

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

# 1. 멘토 신청 및 프로필 테이블
c.execute(
    """
CREATE TABLE IF NOT EXISTS mentors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    subject TEXT,
    introduction TEXT,
    status TEXT DEFAULT '대기', -- '대기', '승인', '거절'
    created_at TEXT
)
"""
)

# 2. 멘토-멘티 매칭 및 방 관리 테이블
c.execute(
    """
CREATE TABLE IF NOT EXISTS matchings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mentor_id INTEGER,
    mentee_name TEXT,
    created_at TEXT
)
"""
)

# 3. 스터디룸 채팅 및 사진 공유 테이블
c.execute(
    """
CREATE TABLE IF NOT EXISTS study_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matching_id INTEGER,
    sender TEXT,
    message TEXT,
    image_path TEXT,
    created_at TEXT
)
"""
)
conn.commit()

# 관리자 인증 정보 (필요시 아이디/비밀번호 변경)
ADMIN_USERNAME = "asgus0826" #관리자 아이디
ADMIN_PASSWORD_HASH = hashlib.sha256("afpjz11@@".encode()).hexdigest() #관리자 비밀번호


def hash_post_password(password):
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"{salt.hex()}:{password_hash.hex()}"


def verify_post_password(password, stored_hash):
    try:
        salt_hex, password_hash_hex = stored_hash.split(":", maxsplit=1)
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(password_hash_hex)
    except (AttributeError, ValueError):
        return False

    actual_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return hmac.compare_digest(actual_hash, expected_hash)

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
menu = ["글 목록", "글 작성하기", "🤝 멘토링 신청", "🏫 멘토링 매칭", "📖 나의 스터디룸"]
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
                "SELECT category, title, author, content, created_at, image_path, author_password_hash FROM posts WHERE id=?",
                (post_id,),
            )
            post = c.fetchone()

            if post:
                st.markdown("---")
                st.markdown(f"### [{post[0]}] {post[1]}")
                st.caption(f"작성자: **{post[2]}** | 작성일: {post[4]}")
                st.write(post[3])
                if post[5]:
                    image_file = Path(post[5])
                    if image_file.exists():
                        st.image(str(image_file), caption="첨부 사진", use_container_width=True)

                # 작성자는 게시글 비밀번호로, 관리자는 관리자 권한으로 관리합니다.
                is_admin = st.session_state["is_admin"]
                if is_admin or post[6]:
                    st.markdown("---")
                    st.markdown("#### 게시글 수정 / 삭제")

                    with st.expander("✏️ 글 내용 수정하기"):
                        with st.form(f"edit_form_{post_id}"):
                            edit_password = ""
                            if not is_admin:
                                edit_password = st.text_input(
                                    "글 작성 시 설정한 비밀번호", type="password"
                                )
                            new_title = st.text_input("수정할 제목", value=post[1])
                            new_content = st.text_area("수정할 내용", value=post[3])
                            submit_edit = st.form_submit_button("수정 완료")

                            if submit_edit:
                                if is_admin or verify_post_password(edit_password, post[6]):
                                    c.execute(
                                        "UPDATE posts SET title=?, content=? WHERE id=?",
                                        (new_title, new_content, post_id),
                                    )
                                    conn.commit()
                                    st.success("게시글이 성공적으로 수정되었습니다!")
                                    st.rerun()
                                else:
                                    st.error("비밀번호가 올바르지 않습니다.")

                    with st.form(f"delete_form_{post_id}"):
                        delete_password = ""
                        if not is_admin:
                            delete_password = st.text_input(
                                "삭제하려면 글 작성 시 설정한 비밀번호를 입력하세요",
                                type="password",
                            )
                        submit_delete = st.form_submit_button("🗑️ 글 삭제하기")

                        if submit_delete:
                            if is_admin or verify_post_password(delete_password, post[6]):
                                if post[5]:
                                    image_file = Path(post[5])
                                    if image_file.exists():
                                        image_file.unlink()
                                c.execute("DELETE FROM posts WHERE id=?", (post_id,))
                                c.execute("DELETE FROM comments WHERE post_id=?", (post_id,))
                                conn.commit()
                                st.success("게시글이 삭제되었습니다.")
                                del st.session_state["read_post_id"]
                                st.rerun()
                            else:
                                st.error("비밀번호가 올바르지 않습니다.")

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
        post_password = st.text_input(
            "수정·삭제 비밀번호", type="password", help="이 글을 수정하거나 삭제할 때 필요합니다."
        )
        title = st.text_input("제목")
        content = st.text_area("내용", height=200)
        uploaded_image = st.file_uploader(
            "사진 첨부 (선택)",
            type=["jpg", "jpeg", "png", "gif", "webp"],
            help="최대 5MB까지 업로드할 수 있습니다.",
        )
        submitted = st.form_submit_button("게시글 등록")

        if submitted:
            if title and content and len(post_password) >= 8:
                image_path = None
                if uploaded_image:
                    image_data = uploaded_image.getvalue()
                    if len(image_data) > 5 * 1024 * 1024:
                        st.error("사진은 5MB 이하만 업로드할 수 있습니다.")
                        st.stop()

                    safe_filename = Path(uploaded_image.name).name
                    image_path = str(UPLOAD_DIR / f"{uuid4().hex}_{safe_filename}")
                    Path(image_path).write_bytes(image_data)

                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                c.execute(
                    "INSERT INTO posts (category, title, author, content, created_at, image_path, author_password_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (category, title, author, content, now, image_path, hash_post_password(post_password)),
                )
                conn.commit()
                st.success("게시글이 성공적으로 등록되었습니다!")
            elif len(post_password) < 8:
                st.warning("수정·삭제 비밀번호는 8자 이상 입력해주세요.")
            else:
                st.warning("수정·삭제 비밀번호, 제목, 내용을 모두 입력해주세요.")

# [메뉴 추가 1] 🤝 멘토링 신청
# ====================================================================
elif choice == "🤝 멘토링 신청":
    st.subheader("🤝 멘토 신청하기")
    st.info("자신의 특기 과목을 살려 친구들을 도와줄 멘토를 모집합니다!")

    with st.form("mentor_apply_form", clear_on_submit=True):
        mentor_name = st.text_input("이름 (또는 닉네임)")
        mentor_subject = st.selectbox("자신 있는 과목", ["국어", "수학", "영어", "과학", "사회", "코딩/IT"])
        mentor_intro = st.text_area("한 줄 소개 및 각오", placeholder="예: 수학 모르는 부분 시원하게 긁어드립니다!")
        submit_mentor = st.form_submit_button("멘토 신청서 제출")

        if submit_mentor:
            if mentor_name and mentor_intro:
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                c.execute(
                    "INSERT INTO mentors (name, subject, introduction, created_at) VALUES (?, ?, ?, ?)",
                    (mentor_name, mentor_subject, mentor_intro, now)
                )
                conn.commit()
                st.success("멘토 신청이 완료되었습니다! 관리자 승인 후 매칭 목록에 표시됩니다.")
            else:
                st.warning("이름과 소개를 모두 입력해 주세요.")

    # 👑 관리자 권한일 때만 보이는 멘토 승인 창
    if st.session_state["is_admin"]:
        st.markdown("---")
        st.subheader("👑 [관리자 전용] 멘토 신청 승인 관리")
        
        pending_mentors = pd.read_sql_query("SELECT * FROM mentors WHERE status='대기'", conn)
        if pending_mentors.empty:
            st.write("대기 중인 멘토 신청이 없습니다.")
        else:
            st.dataframe(pending_mentors, use_container_width=True)
            mentor_to_approve = st.number_input("승인/거절할 멘토 ID 입력", min_value=1, step=1)
            
            col_app, col_rej = st.columns(2)
            with col_app:
                if st.button("✅ 선택한 멘토 승인"):
                    c.execute("UPDATE mentors SET status='승인' WHERE id=?", (mentor_to_approve,))
                    conn.commit()
                    st.success(f"{mentor_to_approve}번 멘토가 승인되었습니다.")
                    st.rerun()
            with col_rej:
                if st.button("❌ 선택한 멘토 거절"):
                    c.execute("UPDATE mentors SET status='거절' WHERE id=?", (mentor_to_approve,))
                    conn.commit()
                    st.warning(f"{mentor_to_approve}번 멘토 신청이 거절되었습니다.")
                    st.rerun()


# ====================================================================
# [수정] 🏫 멘토링 매칭 (방 비밀번호 자동 생성 추가)
# ====================================================================
elif choice == "🏫 멘토링 매칭":
    st.subheader("🏫 대기 중인 멘토 목록")
    st.write("같이 공부하고 싶은 멘토를 선택하여 스터디룸을 개설해 보세요!")

    approved_mentors = pd.read_sql_query("SELECT id, name, subject, introduction FROM mentors WHERE status='승인'", conn)
    
    if approved_mentors.empty:
        st.info("현재 매칭 가능한 멘토가 없습니다. 먼저 멘토 신청 및 승인이 필요합니다.")
    else:
        st.dataframe(approved_mentors, use_container_width=True)
        
        st.markdown("---")
        st.subheader("🎯 멘토링 매칭 신청")
        with st.form("matching_form"):
            selected_mentor_id = st.number_input("함께할 멘토의 ID 번호 입력", min_value=1, step=1)
            mentee_username = st.text_input("신청자(멘티) 이름 또는 닉네임")
            
            # 방 비밀번호 설정 기능 추가 (기본값으로 임의의 4자리 설정 가능)
            import random
            suggested_code = str(random.randint(1000, 9999))
            room_password = st.text_input("이 방의 비밀번호 설정 (4자리 숫자 추천)", value=suggested_code, max_chars=10)
            
            submit_match = st.form_submit_button("이 멘토와 매칭하기")
            
            if submit_match:
                if mentee_username and room_password:
                    # DB에 room_code 컬럼이 없을 경우를 대비해 자동 추가 체크
                    try:
                        c.execute("ALTER TABLE matchings ADD COLUMN room_code TEXT")
                        conn.commit()
                    except sqlite3.OperationalError:
                        pass # 이미 컬럼이 존재하면 넘어감

                    # 멘토 존재 여부 확인
                    c.execute("SELECT name FROM mentors WHERE id=? AND status='승인'", (selected_mentor_id,))
                    mentor_check = c.fetchone()
                    
                    if mentor_check:
                        now = datetime.now().strftime("%Y-%m-%d %H:%M")
                        c.execute(
                            "INSERT INTO matchings (mentor_id, mentee_name, room_code, created_at) VALUES (?, ?, ?, ?)",
                            (selected_mentor_id, mentee_username, room_password, now)
                        )
                        conn.commit()
                        st.success(f"🎉 {mentor_check[0]} 멘토와 성공적으로 매칭되었습니다!")
                        st.info(f"🔑 **이 방의 비밀번호는 [{room_password}] 입니다.** 멘토와 멘티만 공유하세요!")
                    else:
                        st.error("올바른 승인 완료 멘토 ID를 입력해 주세요.")
                else:
                    st.warning("멘티 이름과 방 비밀번호를 모두 입력해 주세요.")



# ====================================================================
# [수정] 📖 나의 스터디룸 (비밀번호 인증 기능 추가)
# ====================================================================
elif choice == "📖 나의 스터디룸":
    st.subheader("📖 우리들의 스터디룸 인증 입장")
    
    # 닉네임과 함께 방 비밀번호를 받음
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        my_name = st.text_input("본인의 닉네임(멘토 또는 멘티명) 입력")
    with col_input2:
        input_code = st.text_input("방 비밀번호 입력", type="password")
    
    if my_name and input_code:
        # DB 구조 업데이트 확인 (기본 방 코드 조회용)
        try:
            c.execute("ALTER TABLE matchings ADD COLUMN room_code TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        # 이름과 비밀번호가 모두 매칭되는 방만 조회
        query = """
        SELECT m.id, men.name AS mentor_name, men.subject, m.mentee_name, m.room_code
        FROM matchings m
        JOIN mentors men ON m.mentor_id = men.id
        WHERE (men.name = ? OR m.mentee_name = ?) AND m.room_code = ?
        """
        my_rooms = pd.read_sql_query(query, conn, params=(my_name, my_name, input_code))
        
        if my_rooms.empty:
            st.error("❌ 일치하는 스터디룸이 없거나 비밀번호가 틀렸습니다.")
        else:
            # 일치하는 방이 있으면 안전하게 입장 선택창 띄우기
            room_options = {f"[{row['subject']}] {row['mentor_name']}(멘토) X {row['mentee_name']}(멘티) 방": row['id'] for idx, row in my_rooms.iterrows()}
            selected_room_text = st.selectbox("입장할 스터디룸 선택", list(room_options.keys()))
            room_id = room_options[selected_room_text]
            
            st.success("✅ 인증 성공! 스터디룸에 정상 접속되었습니다.")
            st.markdown(f"### 🚪 {selected_room_text}")
            
            # --------------------------------------------------------
            # 기존 채팅 및 사진첩 렌더링 코드 (동일하게 유지)
            # --------------------------------------------------------
            chat_col, gallery_col = st.columns([1.2, 1.0])
            
            # 1. 왼쪽: 채팅방
            with chat_col:
                st.write("💬 **스터디룸 채팅**")
                messages = pd.read_sql_query(
                    "SELECT sender, message, image_path, created_at FROM study_messages WHERE matching_id=? ORDER BY id ASC", 
                    conn, params=(room_id,)
                )
                
                chat_box = st.container(height=300)
                with chat_box:
                    for idx, msg in messages.iterrows():
                        if msg['message']:
                            st.markdown(f"**{msg['sender']}**: {msg['message']} <span style='font-size:11px; color:gray;'>({msg['created_at']})</span>", unsafe_allow_html=True)
                        if msg['image_path']:
                            img_path = Path(msg['image_path'])
                            if img_path.exists():
                                st.image(str(img_path), width=150, caption=f"{msg['sender']}의 업로드")

                with st.form("send_msg_form", clear_on_submit=True):
                    msg_text = st.text_input("메시지 입력")
                    msg_img = st.file_uploader("사진 공유 (선택)", type=["jpg", "png", "jpeg"], key="msg_img")
                    submit_msg = st.form_submit_button("전송")
                    
                    if submit_msg:
                        saved_img_path = ""
                        if msg_img:
                            saved_img_path = str(UPLOAD_DIR / f"{uuid4().hex}_{msg_img.name}")
                            Path(saved_img_path).write_bytes(msg_img.getvalue())
                        
                        if msg_text or saved_img_path:
                            now = datetime.now().strftime("%H:%M")
                            c.execute(
                                "INSERT INTO study_messages (matching_id, sender, message, image_path, created_at) VALUES (?, ?, ?, ?, ?)",
                                (room_id, my_name, msg_text, saved_img_path, now)
                            )
                            conn.commit()
                            st.rerun()

            # 2. 오른쪽: 갤러리
            with gallery_col:
                st.write("📸 **공부 인증 / 질문 사진첩**")
                img_messages = messages[messages['image_path'] != ""]
                
                if img_messages.empty:
                    st.caption("아직 공유된 사진이 없습니다.")
                else:
                    g_cols = st.columns(2)
                    for i, (_, msg) in enumerate(img_messages.iterrows()):
                        img_path = Path(msg['image_path'])
                        if img_path.exists():
                            with g_cols[i % 2]:
                                st.image(str(img_path), caption=f"by {msg['sender']} ({msg['created_at']})", use_container_width=True)

