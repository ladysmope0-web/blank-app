#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

#######################
# Page configuration
st.set_page_config(
    page_title="US Population Dashboard",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("default")

#######################
# CSS styling
st.markdown("""
<style>

[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}

[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

/* ======== Metric 카드 스타일 ======== */
[data-testid="stMetric"] {
    background-color: white;   /* 배경 흰색 */
    color: black;              /* 텍스트 검정 */
    text-align: center;
    padding: 15px 0;
    border-radius: 10px;
    border: 1px solid #ddd;    /* 테두리 */
}

[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: bold;
  color: #333;
}

[data-testid="stMetricValue"] {
  color: black;
}

[data-testid="stMetricDelta"] {
  color: black !important;
}


</style>
""", unsafe_allow_html=True)


#######################
# Load data
df_reshaped = pd.read_csv('titanic.csv') ## 분석 데이터 넣기


#######################
# Sidebar
#######################
# Sidebar
with st.sidebar:
    st.title("🚢 Titanic Survival Dashboard")

    # 탑승 클래스 선택
    pclass_filter = st.selectbox(
        "Select Passenger Class (Pclass)",
        options=sorted(df_reshaped['Pclass'].unique()),
        index=0
    )

    # 성별 선택
    sex_filter = st.radio(
        "Select Gender",
        options=df_reshaped['Sex'].unique()
    )

    # 연령대 필터링 (슬라이더)
    age_min = int(df_reshaped['Age'].min())
    age_max = int(df_reshaped['Age'].max())
    age_range = st.slider(
        "Select Age Range",
        min_value=age_min,
        max_value=age_max,
        value=(age_min, age_max)
    )

    # 출발 항구 선택
    embarked_filter = st.multiselect(
        "Select Embarkation Port",
        options=df_reshaped['Embarked'].dropna().unique(),
        default=list(df_reshaped['Embarked'].dropna().unique())
    )

    # 필터 적용 데이터셋
    df_filtered = df_reshaped[
        (df_reshaped['Pclass'] == pclass_filter) &
        (df_reshaped['Sex'] == sex_filter) &
        (df_reshaped['Age'].between(age_range[0], age_range[1])) &
        (df_reshaped['Embarked'].isin(embarked_filter))
    ]



#######################
# Plots



#######################
# Dashboard Main Panel
col = st.columns((1.5, 4.5, 2), gap='medium')

with col[0]:
    st.markdown("### 📊 Survival Summary")

    # 전체 승객 수
    total_passengers = len(df_filtered)
    survived = df_filtered['Survived'].sum()
    not_survived = total_passengers - survived
    survival_rate = (survived / total_passengers * 100) if total_passengers > 0 else 0

    # 메트릭 카드 표시
    st.metric("Total Passengers", total_passengers)
    st.metric("Survived", survived)
    st.metric("Not Survived", not_survived)
    st.metric("Survival Rate (%)", f"{survival_rate:.1f}%")

    st.markdown("---")

    # 성별 생존률 도넛 차트
    st.markdown("#### Survival Rate by Gender")
    gender_survival = df_filtered.groupby("Sex")["Survived"].mean().reset_index()
    gender_survival["Survived"] = gender_survival["Survived"] * 100

    fig_gender = px.pie(
        gender_survival,
        names="Sex",
        values="Survived",
        hole=0.4,
        color="Sex",
        color_discrete_map={"male": "lightblue", "female": "pink"}
    )
    st.plotly_chart(fig_gender, use_container_width=True)

    # 클래스별 생존률 도넛 차트
    st.markdown("#### Survival Rate by Class")
    class_survival = df_filtered.groupby("Pclass")["Survived"].mean().reset_index()
    class_survival["Survived"] = class_survival["Survived"] * 100

    fig_class = px.pie(
        class_survival,
        names="Pclass",
        values="Survived",
        hole=0.4,
        color="Pclass"
    )
    st.plotly_chart(fig_class, use_container_width=True)



with col[1]:
    st.markdown("### 🗺️ Core Visualizations")

    # ----- 공통 전처리 -----
    df_viz = df_filtered.copy()

    # 연령대 구간 생성 (0~80, 10살 단위) + 결측치 처리
    bins = list(range(0, 91, 10))
    labels = [f"{bins[i]}–{bins[i+1]-1}" for i in range(len(bins)-1)]
    df_viz["AgeGroup"] = pd.cut(df_viz["Age"], bins=bins, labels=labels, right=False)
    df_viz["AgeGroup"] = df_viz["AgeGroup"].cat.add_categories(["Unknown"]).fillna("Unknown")

    # 생존 라벨
    df_viz["SurvivedLabel"] = df_viz["Survived"].map({0: "Not Survived", 1: "Survived"})

    # =========================================
    # 1) 연령대 × 생존 여부 히트맵 (생존률 %)
    # =========================================
    st.markdown("#### Heatmap: Survival Rate by Age Group")
    age_survival_rate = (
        df_viz.dropna(subset=["AgeGroup"])
        .groupby(["AgeGroup", "SurvivedLabel"])
        .size()
        .reset_index(name="count")
    )

    # 각 연령대별 총합으로 나눠 생존률 계산
    totals = age_survival_rate.groupby("AgeGroup")["count"].transform("sum")
    age_survival_rate["rate"] = (age_survival_rate["count"] / totals * 100).round(1)

    heat_age = (
        alt.Chart(age_survival_rate)
        .mark_rect()
        .encode(
            x=alt.X("AgeGroup:N", title="Age Group"),
            y=alt.Y("SurvivedLabel:N", title="Survival"),
            color=alt.Color("rate:Q", title="Rate (%)"),
            tooltip=[
                alt.Tooltip("AgeGroup:N", title="Age Group"),
                alt.Tooltip("SurvivedLabel:N", title="Status"),
                alt.Tooltip("rate:Q", title="Rate (%)"),
                alt.Tooltip("count:Q", title="Count"),
            ],
        )
        .properties(height=240)
    )
    st.altair_chart(heat_age, use_container_width=True)

    st.markdown("---")

    # =========================================
    # 2) Pclass × 성별 히트맵 (생존률 %)
    # =========================================
    st.markdown("#### Heatmap: Survival Rate by Class × Gender")
    class_sex_rate = (
        df_viz.groupby(["Pclass", "Sex"])["Survived"]
        .mean()
        .reset_index(name="rate")
    )
    class_sex_rate["rate"] = (class_sex_rate["rate"] * 100).round(1)

    heat_cls_sex = (
        alt.Chart(class_sex_rate)
        .mark_rect()
        .encode(
            x=alt.X("Pclass:O", title="Passenger Class"),
            y=alt.Y("Sex:N", title="Gender"),
            color=alt.Color("rate:Q", title="Survival Rate (%)"),
            tooltip=[
                alt.Tooltip("Pclass:O", title="Class"),
                alt.Tooltip("Sex:N", title="Gender"),
                alt.Tooltip("rate:Q", title="Rate (%)"),
            ],
        )
        .properties(height=200)
    )
    st.altair_chart(heat_cls_sex, use_container_width=True)

    st.markdown("---")

    # =========================================
    # 3) 연령 분포 히스토그램 (생존/비생존 비교)
    # =========================================
    st.markdown("#### Age Distribution by Survival")
    hist_age = px.histogram(
        df_viz.dropna(subset=["Age"]),
        x="Age",
        color="SurvivedLabel",
        nbins=30,
        barmode="overlay",
        opacity=0.6,
        labels={"Age": "Age", "SurvivedLabel": "Status"},
    )
    st.plotly_chart(hist_age, use_container_width=True)



# with col[2]:
with col[2]:
    st.markdown("### 🔎 Detailed Analysis")

    # =========================================
    # 1) 그룹별 생존률 Top 분석
    # (성별 × 클래스 조합)
    # =========================================
    st.markdown("#### Top Survival Groups")
    group_rate = (
        df_filtered.groupby(["Pclass", "Sex"])["Survived"]
        .mean()
        .reset_index(name="rate")
    )
    group_rate["rate"] = (group_rate["rate"] * 100).round(1)
    group_rate["Group"] = (
        "Class " + group_rate["Pclass"].astype(str) + " - " + group_rate["Sex"]
    )

    top_groups = group_rate.sort_values("rate", ascending=False).head(5)

    fig_top_groups = px.bar(
        top_groups,
        x="rate",
        y="Group",
        orientation="h",
        text="rate",
        labels={"rate": "Survival Rate (%)", "Group": "Group"},
    )
    st.plotly_chart(fig_top_groups, use_container_width=True)

    st.markdown("---")

    # =========================================
    # 2) 연령대별 생존률 Top 5
    # =========================================
    st.markdown("#### Top 5 Survival by Age Group")
    bins = list(range(0, 91, 10))
    labels = [f"{bins[i]}–{bins[i+1]-1}" for i in range(len(bins) - 1)]
    df_filtered["AgeGroup"] = pd.cut(
        df_filtered["Age"], bins=bins, labels=labels, right=False
    )
    age_rate = (
        df_filtered.groupby("AgeGroup")["Survived"]
        .mean()
        .reset_index(name="rate")
    )
    age_rate["rate"] = (age_rate["rate"] * 100).round(1)
    age_rate = age_rate.dropna().sort_values("rate", ascending=False).head(5)

    fig_age_top = px.bar(
        age_rate,
        x="AgeGroup",
        y="rate",
        text="rate",
        labels={"AgeGroup": "Age Group", "rate": "Survival Rate (%)"},
    )
    st.plotly_chart(fig_age_top, use_container_width=True)

    st.markdown("---")

    # =========================================
    # 3) 데이터 설명 / 출처
    # =========================================
    st.markdown("#### ℹ️ About the Data")
    st.write("""
    - **Dataset**: Titanic passenger data (sample dataset, Kaggle/Seaborn)  
    - **Key Fields**:  
        - Pclass: Passenger Class (1 = 1st, 2 = 2nd, 3 = 3rd)  
        - Sex: Gender  
        - Age: Age of Passenger  
        - Survived: 0 = No, 1 = Yes  
        - Embarked: Port of Embarkation (C = Cherbourg, Q = Queenstown, S = Southampton)  

    This dashboard analyzes survival patterns by passenger class, gender, and age.
    """)
