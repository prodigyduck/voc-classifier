import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="VOC Classifier",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 VOC Classifier - 제조시스템 UI 분류 및 분석")

st.sidebar.title("메뉴")
page = st.sidebar.radio("페이지 선택", ["대시보드", "VOC 목록", "VOC 입력", "분류 모델", "UI 개선 추적"])


def get_analytics():
    try:
        response = requests.get(f"{API_BASE_URL}/analytics/overview")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def get_vocs(category_id=None, status=None, priority=None, ui_related=None):
    params = {}
    if category_id:
        params["category_id"] = category_id
    if status:
        params["status"] = status
    if priority:
        params["priority"] = priority
    if ui_related is not None:
        params["ui_related"] = ui_related

    try:
        response = requests.get(f"{API_BASE_URL}/vocs", params=params)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []


def get_categories():
    try:
        response = requests.get(f"{API_BASE_URL}/categories")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []


if page == "대시보드":
    st.header("📈 VOC 분석 대시보드")

    analytics = get_analytics()
    if analytics:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("전체 VOC", analytics["total_vocs"])

        with col2:
            st.metric("UI 관련 VOC", analytics["ui_related_count"])

        with col3:
            pending = analytics["by_status"].get("PENDING", 0)
            st.metric("미분류 VOC", pending)

        with col4:
            analyzed = analytics["by_status"].get("ANALYZED", 0)
            st.metric("분류 완료", analyzed)

        st.subheader("카테고리별 분포")
        if analytics["by_category"]:
            category_df = pd.DataFrame(list(analytics["by_category"].items()), columns=["카테고리", "건수"])
            fig_cat = px.bar(category_df, x="카테고리", y="건수", color="건수")
            st.plotly_chart(fig_cat, use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("상태별 분포")
            if analytics["by_status"]:
                status_df = pd.DataFrame(list(analytics["by_status"].items()), columns=["상태", "건수"])
                fig_status = px.pie(status_df, values="건수", names="상태")
                st.plotly_chart(fig_status, use_container_width=True)

        with col2:
            st.subheader("우선순위별 분포")
            if analytics["by_priority"]:
                priority_df = pd.DataFrame(list(analytics["by_priority"].items()), columns=["우선순위", "건수"])
                priority_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                priority_df["우선순위"] = pd.Categorical(priority_df["우선순위"], categories=priority_order, ordered=True)
                priority_df = priority_df.sort_values("우선순위")
                fig_priority = px.bar(priority_df, x="우선순위", y="건수", color="우선순위")
                st.plotly_chart(fig_priority, use_container_width=True)

        st.subheader("월별 추이")
        if analytics["monthly_trend"]:
            trend_df = pd.DataFrame(analytics["monthly_trend"])
            fig_trend = px.line(trend_df, x="month", y="count", markers=True)
            fig_trend.update_layout(xaxis_title="월", yaxis_title="VOC 건수")
            st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.error("분석 데이터를 불러오는데 실패했습니다. 백엔드 서버가 실행 중인지 확인해주세요.")


elif page == "VOC 목록":
    st.header("📋 VOC 목록")

    categories = get_categories()
    category_options = {c["name"]: c["id"] for c in categories}

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        selected_category = st.selectbox("카테고리", ["전체"] + list(category_options.keys()))
    with col2:
        selected_status = st.selectbox("상태", ["전체", "PENDING", "ANALYZED", "RESOLVED", "REJECTED"])
    with col3:
        selected_priority = st.selectbox("우선순위", ["전체", "LOW", "MEDIUM", "HIGH", "CRITICAL"])
    with col4:
        ui_related_only = st.checkbox("UI 관련만 보기")

    vocs = get_vocs(
        category_id=category_options.get(selected_category) if selected_category != "전체" else None,
        status=selected_status if selected_status != "전체" else None,
        priority=selected_priority if selected_priority != "전체" else None,
        ui_related=ui_related_only if ui_related_only else None
    )

    if vocs:
        df = pd.DataFrame(vocs)
        df_display = df[["id", "title", "status", "priority", "ui_related", "submitted_by", "created_at"]]

        category_name_map = {c["id"]: c["name"] for c in categories}

        def format_row(row):
            return {
                "ID": row["id"],
                "제목": row["title"],
                "상태": row["status"],
                "우선순위": row["priority"],
                "UI 관련": "✅" if row["ui_related"] else "❌",
                "제출자": row["submitted_by"],
                "생성일": pd.to_datetime(row["created_at"]).strftime("%Y-%m-%d %H:%M")
            }

        formatted_df = df.apply(format_row, axis=1, result_type="expand")
        st.dataframe(formatted_df, use_container_width=True)
    else:
        st.info("VOC 데이터가 없습니다.")


elif page == "VOC 입력":
    st.header("➕ 새 VOC 입력")

    categories = get_categories()
    category_options = {c["name"]: c["id"] for c in categories}

    with st.form("voc_form"):
        title = st.text_input("제목", max_length=500)
        content = st.text_area("내용", height=200)

        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("카테고리", list(category_options.keys()))
            priority = st.selectbox("우선순위", ["LOW", "MEDIUM", "HIGH", "CRITICAL"], index=1)

        with col2:
            submitted_by = st.text_input("제출자")
            ui_related = st.checkbox("UI 개선으로 해결 가능", value=False)

        submitted = st.form_submit_button("VOC 등록")

        if submitted:
            if title and content:
                payload = {
                    "title": title,
                    "content": content,
                    "category_id": category_options[category],
                    "priority": priority,
                    "submitted_by": submitted_by or "익명",
                    "ui_related": ui_related
                }

                try:
                    response = requests.post(f"{API_BASE_URL}/vocs", json=payload)
                    if response.status_code == 201:
                        st.success("VOC가 성공적으로 등록되었습니다!")
                        st.balloons()
                    else:
                        st.error(f"등록 실패: {response.text}")
                except Exception as e:
                    st.error(f"등록 중 오류 발생: {str(e)}")
            else:
                st.warning("제목과 내용은 필수 입력 항목입니다.")


elif page == "분류 모델":
    st.header("🤖 VOC 분류 모델 (BERTopic)")

    st.info("BERTopic을 사용하여 VOC를 자동으로 분류합니다.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📚 모델 학습"):
            try:
                response = requests.post(f"{API_BASE_URL}/classification/train")
                if response.status_code == 200:
                    st.success(response.json()["message"])
                else:
                    st.error(f"학습 실패: {response.text}")
            except Exception as e:
                st.error(f"학습 중 오류 발생: {str(e)}")

    with col2:
        if st.button("🔄 일괄 분류 실행"):
            try:
                response = requests.post(f"{API_BASE_URL}/classification/classify-batch", params={"limit": 100})
                if response.status_code == 200:
                    st.success(response.json()["message"])
                else:
                    st.error(f"분류 실패: {response.text}")
            except Exception as e:
                st.error(f"분류 중 오류 발생: {str(e)}")

    st.subheader("토픽 정보")
    try:
        response = requests.get(f"{API_BASE_URL}/classification/topics")
        if response.status_code == 200:
            topics = response.json()
            if topics:
                topics_df = pd.DataFrame(topics)
                st.dataframe(topics_df[["topic_id", "name", "count"]], use_container_width=True)

                for topic in topics:
                    with st.expander(f"토픽 {topic['topic_id']}: {topic['name']} ({topic['count']}건)"):
                        st.write("**키워드:**", ", ".join([kw[0] for kw in topic["keywords"][:10]]))
                        if topic.get("representative_docs"):
                            st.write("**대표 문서:**")
                            for doc in topic["representative_docs"][:3]:
                                st.text(f"• {doc[:200]}...")
            else:
                st.info("아직 학습된 토픽이 없습니다.")
        else:
            st.error("토픽 정보를 불러오는데 실패했습니다.")
    except Exception as e:
        st.error(f"토픽 정보 불러오기 중 오류 발생: {str(e)}")


elif page == "UI 개선 추적":
    st.header("📊 UI 개선 추적")

    st.info("UI 개선 활동으로 인한 VOC 감소율을 추적합니다.")

    st.subheader("UI 개선 활동 등록")

    with st.form("ui_improvement_form"):
        improvement_name = st.text_input("개선 활동명")
        description = st.text_area("설명")
        categories = get_categories()
        category_options = {c["name"]: c["id"] for c in categories}
        selected_categories = st.multiselect("관련 카테고리", list(category_options.keys()))

        submitted = st.form_submit_button("등록")

        if submitted:
            if improvement_name:
                payload = {
                    "name": improvement_name,
                    "description": description,
                    "related_categories": [category_options[c] for c in selected_categories]
                }
                try:
                    response = requests.post(f"{API_BASE_URL}/ui-improvements", json=payload)
                    if response.status_code == 201:
                        st.success("UI 개선 활동이 등록되었습니다!")
                    else:
                        st.error(f"등록 실패: {response.text}")
                except Exception as e:
                    st.error(f"등록 중 오류 발생: {str(e)}")
            else:
                st.warning("개선 활동명은 필수 입력 항목입니다.")


st.sidebar.markdown("---")
st.sidebar.info("""
**시스템 정보:**
- 백엔드: FastAPI (port 8000)
- 프론트엔드: Streamlit (port 8501)
- 분류 모델: BERTopic
""")
