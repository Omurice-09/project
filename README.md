📁내-프로젝트-폴더/
 ├── 📄app.py
 └── 📄post_form.py   <-- 같은 위치

📄 `app.py` (메인 파일)

python
import streamlit as st

# post_form.py 파일에서 render_post_form 함수를 가져옵니다.
from post_form import render_post_form

## 💡 요약 규칙

1. `from [폴더명].[파일명] import [함수명]` 형태
2. 폴더가 없고 같은 위치라면 `from [파일명] import [함수명]`만 
3. 불러올 파일 이름 뒤에 `.py` 확장자는 적지 X
