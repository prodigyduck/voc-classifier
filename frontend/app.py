import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
from i18n import i18n

API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="VOC Classifier",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.markdown("### 🌐 Language")
lang = st.sidebar.selectbox(
    "Select Language",
    i18n.get_available_languages(),
    format_func=lambda x: {"ko": "한국어", "en": "English"}.get(x, x),
    index=i18n.get_available_languages().index(i18n.get_language())
)
i18n.set_language(lang)

st.title(f"📊 {i18n.t('app_title')} - {i18n.t('app_subtitle')}")

st.sidebar.title(i18n.t("menu.dashboard"))
page = st.sidebar.radio(
    i18n.t("menu.dashboard"),
    [
        i18n.t("menu.dashboard"),
        i18n.t("menu.voc_list"),
        i18n.t("menu.classification_model")
    ]
)


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


if page == i18n.t("menu.dashboard"):
    st.header(f"📈 {i18n.t('dashboard.title')}")

    auto_refresh = st.checkbox(i18n.t("common.auto_refresh"), value=False)
    if auto_refresh:
        time.sleep(30)
        st.rerun()

    analytics = get_analytics()
    if analytics:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(i18n.t("dashboard.total_voc"), analytics["total_vocs"])

        with col2:
            st.metric(i18n.t("dashboard.ui_related_voc"), analytics["ui_related_count"])

        with col3:
            st.metric("AI 분류 완료", analytics.get("classified_count", 0))

        st.subheader(i18n.t("dashboard.category_distribution"))
        if analytics["by_category"]:
            category_df = pd.DataFrame(list(analytics["by_category"].items()), columns=["카테고리", "건수"])
            fig_cat = px.bar(category_df, x="카테고리", y="건수", color="건수")
            st.plotly_chart(fig_cat, use_container_width=True)

        if analytics.get("by_ai_category"):
            st.subheader("🤖 AI 분류 결과 분포")
            ai_cat_df = pd.DataFrame(list(analytics["by_ai_category"].items()), columns=["AI 추천 카테고리", "건수"])
            ai_cat_df = ai_cat_df.sort_values("건수", ascending=False)
            fig_ai_cat = px.bar(ai_cat_df, x="AI 추천 카테고리", y="건수", color="건수", color_continuous_scale="Blues")
            st.plotly_chart(fig_ai_cat, use_container_width=True)

        if analytics.get("confidence_distribution"):
            st.subheader("📊 분류 신뢰도 분포")
            conf = analytics["confidence_distribution"]
            conf_df = pd.DataFrame({
                "신뢰도": ["높음 (≥70%)", "중간 (50-70%)", "낮음 (<50%)"],
                "건수": [conf.get("high", 0), conf.get("medium", 0), conf.get("low", 0)]
            })
            fig_conf = px.pie(conf_df, values="건수", names="신뢰도", title="AI 분류 신뢰도 분포", color="신뢰도",
                              color_discrete_map={"높음 (≥70%)": "green", "중간 (50-70%)": "orange", "낮음 (<50%)": "red"})
            st.plotly_chart(fig_conf, use_container_width=True)

        st.subheader("월별 추이")
        if analytics["monthly_trend"]:
            trend_df = pd.DataFrame(analytics["monthly_trend"])
            fig_trend = px.line(trend_df, x="month", y="count", markers=True)
            fig_trend.update_layout(xaxis_title="월", yaxis_title="VOC 건수")
            st.plotly_chart(fig_trend, use_container_width=True)

        if analytics.get("category_trend"):
            st.subheader("카테고리별 트렌드")
            trend_data = []
            for month, categories in analytics["category_trend"].items():
                for category, count in categories.items():
                    trend_data.append({"월": month[:7], "카테고리": category, "건수": count})

            if trend_data:
                trend_df = pd.DataFrame(trend_data)
                fig_category_trend = px.line(
                    trend_df,
                    x="월",
                    y="건수",
                    color="카테고리",
                    markers=True,
                    title="월별 카테고리별 VOC 추이"
                )
                fig_category_trend.update_layout(xaxis_title="월", yaxis_title="VOC 건수")
                st.plotly_chart(fig_category_trend, use_container_width=True)

        if analytics.get("ai_category_trend"):
            st.subheader("🤖 AI 분류 결과 트렌드")
            ai_trend_data = []
            for month, categories in analytics["ai_category_trend"].items():
                for category, count in categories.items():
                    ai_trend_data.append({"월": month[:7], "AI 추천 카테고리": category, "건수": count})

            if ai_trend_data:
                ai_trend_df = pd.DataFrame(ai_trend_data)
                fig_ai_trend = px.line(
                    ai_trend_df,
                    x="월",
                    y="건수",
                    color="AI 추천 카테고리",
                    markers=True,
                    title="월별 AI 분류 결과 추이"
                )
                fig_ai_trend.update_layout(xaxis_title="월", yaxis_title="VOC 건수")
                st.plotly_chart(fig_ai_trend, use_container_width=True)
    else:
        st.error("분석 데이터를 불러오는데 실패했습니다. 백엔드 서버가 실행 중인지 확인해주세요.")


elif page == "VOC 목록":
    st.header("📋 VOC 목록")

    categories = get_categories()
    category_options = {c["name"]: c["id"] for c in categories}

    col1, col2 = st.columns(2)
    with col1:
        selected_category = st.selectbox("카테고리", ["전체"] + list(category_options.keys()))
    with col2:
        ui_related_only = st.checkbox("UI 관련만 보기")

    vocs = get_vocs(
        category_id=category_options.get(selected_category) if selected_category != "전체" else None,
        ui_related=ui_related_only if ui_related_only else None
    )

    if vocs:
        df = pd.DataFrame(vocs)

        category_name_map = {c["id"]: c["name"] for c in categories}

        def format_row(row):
            return {
                "ID": row["id"],
                "제목": row["title"],
                "카테고리": category_name_map.get(row.get("category_id"), "-"),
                "UI 관련": "✅" if row.get("ui_related") else "❌",
                "제출자": row.get("submitted_by", "-"),
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
        title = st.text_input(i18n.t("voc.title"))
        content = st.text_area(i18n.t("voc.content"), height=200)

        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox(i18n.t("voc.category"), list(category_options.keys()))
            priority = st.selectbox(i18n.t("voc.priority"), ["LOW", "MEDIUM", "HIGH", "CRITICAL"], index=1)

        with col2:
            submitted_by = st.text_input(i18n.t("voc.submitted_by"))
            ui_related = st.checkbox(i18n.t("voc.improvement_action"), value=False)

        submitted = st.form_submit_button(i18n.t("voc.register_voc"))

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
                        st.success(i18n.t("common.registration_success"))
                        st.balloons()
                    else:
                        st.error(f"{i18n.t('common.registration_failed')}: {response.text}")
                except Exception as e:
                    st.error(f"{i18n.t('common.loading_failed')}: {str(e)}")
            else:
                st.warning(i18n.t("common.required_field"))


elif page == i18n.t("menu.classification_model"):
    st.header(f"🤖 {i18n.t('classification.title')}")

    st.info(i18n.t("classification.info"))

    col1, col2 = st.columns(2)

    with col1:
        if st.button(f"📚 {i18n.t('classification.train_model')}"):
            try:
                response = requests.post(f"{API_BASE_URL}/classification/train")
                if response.status_code == 200:
                    st.success(response.json()["message"])
                else:
                    st.error(f"{i18n.t('classification.train_model')}: {response.text}")
            except Exception as e:
                st.error(f"{i18n.t('classification.train_model')}: {str(e)}")

    with col2:
        if st.button(f"🔄 {i18n.t('classification.batch_classify')}"):
            try:
                response = requests.post(f"{API_BASE_URL}/classification/classify-batch", params={"limit": 100})
                if response.status_code == 200:
                    st.success(response.json()["message"])
                else:
                    st.error(f"{i18n.t('classification.batch_classify')}: {response.text}")
            except Exception as e:
                st.error(f"{i18n.t('classification.batch_classify')}: {str(e)}")

    st.subheader(i18n.t("classification.topic_info"))
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
                st.info(i18n.t("classification.no_topic"))
        else:
            st.error(i18n.t("common.loading_failed"))
    except Exception as e:
        st.error(f"{i18n.t('common.loading_failed')}: {str(e)}")


elif page == i18n.t("menu.ui_improvement_tracking"):
    st.header(f"📊 {i18n.t('ui_improvement.title')}")

    st.info(i18n.t("ui_improvement.info"))

    col1, col2, col3 = st.columns(3)
    with col1:
        total_imps = st.metric(i18n.t("ui_improvement.total_improvements"), "0")
    with col2:
        completed_imps = st.metric(i18n.t("ui_improvement.completed_improvements"), "0")
    with col3:
        avg_reduction = st.metric(i18n.t("ui_improvement.avg_reduction_rate"), "0%")

    try:
        response = requests.get(f"{API_BASE_URL}/ui-improvements/analytics/overview")
        if response.status_code == 200:
            analytics = response.json()

            total_imps.metric(i18n.t("ui_improvement.total_improvements"), str(analytics["total_improvements"]))
            completed_imps.metric(i18n.t("ui_improvement.completed_improvements"), str(analytics["completed_improvements"]))
            avg_reduction.metric(i18n.t("ui_improvement.avg_reduction_rate"), f"{analytics['average_reduction_rate'] * 100:.1f}%")

            if analytics["reductions"]:
                st.subheader(i18n.t("ui_improvement.reduction_by_improvement"))
                reduction_df = pd.DataFrame(analytics["reductions"])

                col1, col2 = st.columns(2)

                with col1:
                    fig_reduction = px.bar(
                        reduction_df,
                        x="improvement_name",
                        y="reduction_percentage",
                        title="개선 활동별 감소율 (%)",
                        color="reduction_percentage",
                        color_continuous_scale="RdYlGn_r"
                    )
                    fig_reduction.update_layout(xaxis_title="개선 활동", yaxis_title="감소율 (%)")
                    st.plotly_chart(fig_reduction, use_container_width=True)

                with col2:
                    fig_comparison = px.scatter(
                        reduction_df,
                        x="before_count",
                        y="after_count",
                        title="개선 전후 VOC 수 비교",
                        size="reduction_percentage",
                        hover_data=["improvement_name", "reduction_percentage"],
                        labels={"before_count": "개선 전", "after_count": "개선 후"}
                    )
                    fig_comparison.add_trace(
                        go.Scatter(
                            x=[0, max(reduction_df["before_count"].max(), reduction_df["after_count"].max()) * 1.1],
                            y=[0, max(reduction_df["before_count"].max(), reduction_df["after_count"].max()) * 1.1],
                            mode="lines",
                            name="기준선",
                            line=dict(dash="dash", color="gray")
                        )
                    )
                    st.plotly_chart(fig_comparison, use_container_width=True)

                if analytics["by_category"]:
                    st.subheader(i18n.t("ui_improvement.avg_reduction_by_category"))
                    category_df = pd.DataFrame(list(analytics["by_category"].items()), columns=["카테고리", "평균 감소율"])
                    category_df["평균 감소율 (%)"] = category_df["평균 감소율"] * 100
                    fig_category = px.bar(
                        category_df,
                        x="카테고리",
                        y="평균 감소율 (%)",
                        color="평균 감소율 (%)",
                        color_continuous_scale="RdYlGn_r"
                    )
                    st.plotly_chart(fig_category, use_container_width=True)

            else:
                st.info(i18n.t("ui_improvement.no_data"))
        else:
            st.error(i18n.t("common.loading_failed"))
    except Exception as e:
        st.error(f"{i18n.t('common.loading_failed')}: {str(e)}")

    st.markdown("---")

    st.subheader(i18n.t("ui_improvement.register_improvement"))

    with st.form("ui_improvement_form"):
        improvement_name = st.text_input(i18n.t("ui_improvement.improvement_name"))
        description = st.text_area(i18n.t("ui_improvement.description"))
        categories = get_categories()
        category_options = {c["name"]: c["id"] for c in categories}
        selected_categories = st.multiselect(i18n.t("ui_improvement.related_categories"), list(category_options.keys()))

        submitted = st.form_submit_button(i18n.t("ui_improvement.register"))

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
                        st.success(i18n.t("common.registration_success"))
                    else:
                        st.error(f"{i18n.t('common.registration_failed')}: {response.text}")
                except Exception as e:
                    st.error(f"{i18n.t('common.loading_failed')}: {str(e)}")
            else:
                st.warning(i18n.t("common.required_field"))


st.sidebar.markdown("---")
st.sidebar.info(f"""
**{i18n.t('system_info.title')}:**
- {i18n.t('system_info.backend')}: FastAPI (port 8000)
- {i18n.t('system_info.frontend')}: Streamlit (port 8501)
- {i18n.t('system_info.classification_model')}: BERTopic
""")
