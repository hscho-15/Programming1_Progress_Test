import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Bike Sharing Demand 데이터셋**  
                - 제공처: [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)  
                - 설명: 2011–2012년 캘리포니아 주의 수도인 미국 워싱턴 D.C. 인근 도시에서 시간별 자전거 대여량을 기록한 데이터  
                - 주요 변수:  
                  - `datetime`: 날짜 및 시간  
                  - `season`: 계절  
                  - `holiday`: 공휴일 여부  
                  - `workingday`: 근무일 여부  
                  - `weather`: 날씨 상태  
                  - `temp`, `atemp`: 기온 및 체감온도  
                  - `humidity`, `windspeed`: 습도 및 풍속  
                  - `casual`, `registered`, `count`: 비등록·등록·전체 대여 횟수  
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        # 지역 한글 → 영문 매핑
        region_map = {
            '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
            '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
            '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
            '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
            '제주': 'Jeju', '전국': 'Total'
        }

        st.title("인구 통계 전처리 및 요약 분석")

        # 파일 업로드
        uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type=["csv"])

        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)

            # 전처리
            df['인구'] = pd.to_numeric(df['인구'].astype(str).str.replace(",", ""), errors='coerce')
            df['출생아수(명)'] = pd.to_numeric(df['출생아수(명)'].astype(str).str.replace(",", ""), errors='coerce')
            df['사망자수(명)'] = pd.to_numeric(df['사망자수(명)'].astype(str).str.replace(",", ""), errors='coerce')
            df['Region'] = df['지역'].map(region_map)
            df = df.dropna(subset=['Region'])

            tab1, tab2, tab3, tab4, tab5 = st.tabs(
                ["기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"])

            # 📊 Tab 1: 기초 통계
            with tab1:
                st.subheader("원본 데이터")
                st.dataframe(df.head())

                # ‘세종’ 지역의 행 필터링
                sejong_mask = df['지역'].astype(str).str.contains("세종")
                df.loc[sejong_mask] = df.loc[sejong_mask].replace("-", "0")

                # ‘인구’, ‘출생아수(명)’, ‘사망자수(명)’ 열을 숫자로 변환
                cols_to_numeric = ['인구', '출생아수(명)', '사망자수(명)']
                for col in cols_to_numeric:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors='coerce')
                    else:
                        st.warning(f"'{col}' 열이 데이터프레임에 없습니다.")

                st.subheader("전처리된 데이터")
                st.dataframe(df.head())

                st.subheader("요약 통계 (df.describe())")
                st.dataframe(df.describe())

                st.subheader("데이터프레임 구조 (df.info())")
                # df.info() 결과를 문자열로 받아오기 위해 StringIO 사용
                buffer = io.StringIO()
                df.info(buf=buffer)
                s = buffer.getvalue()
                st.text(s)

            # 📈 Tab 2: 연도별 추이
            with tab2:
                # 전국 데이터 필터링
                nationwide_df = df[df['지역'] == '전국'].sort_values('연도')

                # 인구 추이 시각화
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.plot(nationwide_df['연도'], nationwide_df['인구'], marker='o', label="Actual")

                # 최근 3년 평균 증가량 = 출생 - 사망
                recent = nationwide_df.tail(3)
                recent_births = recent['출생아수(명)'].mean()
                recent_deaths = recent['사망자수(명)'].mean()
                annual_growth = recent_births - recent_deaths

                # 가장 최근 연도와 인구
                last_year = nationwide_df['연도'].iloc[-1]
                last_pop = nationwide_df['인구'].iloc[-1]

                # 2035년까지 연도 수
                years_to_project = 2035 - last_year

                # 인구 예측
                projected_pop = last_pop + years_to_project * annual_growth

                # 그래프에 예측 결과 표시
                ax.plot(2035, projected_pop, 'ro', label="Projected 2035")
                ax.axvline(x=2035, linestyle='--', color='red', alpha=0.5)
                ax.text(2035 + 0.3, projected_pop, f"{int(projected_pop):,}", color='red')

                # 그래프 꾸미기 (영문 라벨만 사용)
                ax.set_title("Population Trends and 2035 Projection")
                ax.set_xlabel("Year")
                ax.set_ylabel("Population")
                ax.legend()
                ax.grid(True)

                st.pyplot(fig)

            # 📉 Tab 3: 지역별 최근 5년 인구 변화량/변화율
            with tab3:
                st.subheader("Regional Change Over Last 5 Years")
                df_local = df[df['Region'] != 'Total']
                latest_years = sorted(df_local['연도'].unique())[-5:]
                df_recent = df_local[df_local['연도'].isin(latest_years)]

                pop_change = df_recent.groupby(['Region', '연도'])['인구'].sum().unstack()
                start_year = latest_years[0]
                end_year = latest_years[-1]
                pop_change['Change (k)'] = (pop_change[end_year] - pop_change[start_year]) / 1000
                pop_change['Change (%)'] = ((pop_change[end_year] - pop_change[start_year]) / pop_change[
                    start_year]) * 100

                st.subheader("Change in Population (k)")
                fig2, ax2 = plt.subplots(figsize=(10, 6))
                pop_change_sorted = pop_change.sort_values("Change (k)", ascending=False)
                sns.barplot(x="Change (k)", y=pop_change_sorted.index, data=pop_change_sorted, ax=ax2,
                            palette="Blues_d")
                for i, val in enumerate(pop_change_sorted["Change (k)"]):
                    ax2.text(val + 2, i, f"{val:.1f}", va='center')
                ax2.set_xlabel("Change (thousands)")
                ax2.set_ylabel("Region")
                st.pyplot(fig2)

                st.subheader("Growth Rate (%)")
                fig3, ax3 = plt.subplots(figsize=(10, 6))
                pop_change_sorted = pop_change.sort_values("Change (%)", ascending=False)
                sns.barplot(x="Change (%)", y=pop_change_sorted.index, data=pop_change_sorted, ax=ax3,
                            palette="Greens_d")
                for i, val in enumerate(pop_change_sorted["Change (%)"]):
                    ax3.text(val + 0.2, i, f"{val:.2f}%", va='center')
                ax3.set_xlabel("Growth Rate (%)")
                ax3.set_ylabel("Region")
                st.pyplot(fig3)

            # 📘 Tab 4: 증감량 분석 테이블
            with tab4:
                st.subheader("Top 100 Largest Population Changes")
                df_diff = df[df['Region'] != 'Total'].sort_values(['Region', '연도'])
                df_diff['Change'] = df_diff.groupby('Region')['인구'].diff()
                df_diff['abs_change'] = df_diff['Change'].abs()
                top100 = df_diff.sort_values('abs_change', ascending=False).head(100)

                display_df = top100[['연도', 'Region', '인구', 'Change']].copy()
                display_df['인구'] = display_df['인구'].map(lambda x: f"{int(x):,}")
                display_df['Change'] = display_df['Change'].map(lambda x: f"{int(x):,}" if pd.notnull(x) else "-")

                def highlight_change(val):
                    if val == "-":
                        return ""
                    val = int(val.replace(",", ""))
                    if val > 0:
                        return "background-color: rgba(0, 100, 255, 0.2)"
                    elif val < 0:
                        return "background-color: rgba(255, 0, 0, 0.2)"
                    return ""

                styled = display_df.style.applymap(highlight_change, subset=['Change'])
                st.dataframe(styled, use_container_width=True)

            # 📊 Tab 5: 누적 영역 시각화
            with tab5:
                st.subheader("Stacked Area Chart by Region")
                pivot_df = df[df['Region'] != 'Total'].pivot_table(index='Region', columns='연도', values='인구',
                                                                   aggfunc='sum')
                pivot_df = pivot_df.sort_index(axis=1)
                fig5, ax5 = plt.subplots(figsize=(12, 6))
                pivot_df_T = pivot_df.transpose()
                pivot_df_T.plot(kind='area', stacked=True, ax=ax5, cmap='tab20')
                ax5.set_title("Population by Region Over Time")
                ax5.set_xlabel("Year")
                ax5.set_ylabel("Population")
                ax5.legend(title="Region", bbox_to_anchor=(1.05, 1), loc='upper left')
                ax5.grid(True)
                st.pyplot(fig5)


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()