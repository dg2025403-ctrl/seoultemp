import streamlit as st
import csv
from datetime import datetime, date

# --------------------------------------------------
# 페이지 설정
# --------------------------------------------------
st.set_page_config(
    page_title="서울 기온 랭킹",
    page_icon="🌡️",
    layout="centered"
)

# --------------------------------------------------
# 디자인
# --------------------------------------------------
st.markdown("""
<style>
    .block-container {
        max-width: 850px;
        padding-top: 3rem;
        padding-bottom: 4rem;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .title {
        font-size: 42px;
        font-weight: 800;
        letter-spacing: -2px;
        margin-bottom: 5px;
    }

    .subtitle {
        color: #777;
        font-size: 16px;
        margin-bottom: 32px;
    }

    .result-card {
        border: 1px solid rgba(128,128,128,0.22);
        border-radius: 24px;
        padding: 30px;
        margin-top: 25px;
        text-align: center;
        box-shadow: 0 8px 30px rgba(0,0,0,0.05);
    }

    .rank-label {
        font-size: 15px;
        color: #888;
        margin-bottom: 5px;
    }

    .rank {
        font-size: 65px;
        font-weight: 900;
        line-height: 1.1;
        letter-spacing: -3px;
    }

    .temperature {
        font-size: 25px;
        font-weight: 700;
        margin-top: 15px;
    }

    .description {
        color: #777;
        margin-top: 8px;
        font-size: 14px;
    }

    .small-card {
        border: 1px solid rgba(128,128,128,0.18);
        border-radius: 16px;
        padding: 18px;
        text-align: center;
    }

    div[data-testid="stDateInput"] {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# CSV 불러오기
# --------------------------------------------------
@st.cache_data
def load_data():
    records = []

    # 파일 이름은 반드시 seoul.csv
    with open("seoul.csv", "r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for row in reader:
            try:
                # 데이터 날짜 앞에 탭이 들어가 있어서 strip() 처리
                date_text = row["날짜"].strip()
                current_date = datetime.strptime(
                    date_text,
                    "%Y-%m-%d"
                ).date()

                avg_temp = float(row["평균기온"])

                min_temp = None
                max_temp = None

                if row["최저기온"].strip():
                    min_temp = float(row["최저기온"])

                if row["최고기온"].strip():
                    max_temp = float(row["최고기온"])

                records.append({
                    "date": current_date,
                    "year": current_date.year,
                    "month": current_date.month,
                    "day": current_date.day,
                    "avg": avg_temp,
                    "min": min_temp,
                    "max": max_temp
                })

            except (ValueError, KeyError):
                # 결측값이나 이상한 행은 건너뜀
                continue

    return records


data = load_data()

if not data:
    st.error("seoul.csv에서 데이터를 읽지 못했습니다.")
    st.stop()


# --------------------------------------------------
# 데이터 기본 정보
# --------------------------------------------------
first_date = min(item["date"] for item in data)
last_date = max(item["date"] for item in data)

available_dates = {item["date"] for item in data}


# --------------------------------------------------
# 제목
# --------------------------------------------------
st.markdown(
    '<div class="title">서울 기온 랭킹 🌡️</div>',
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="subtitle">
        {first_date.year}년부터 {last_date.year}년까지의 서울 기온 기록에서<br>
        내가 선택한 기간은 얼마나 더웠을까요?
    </div>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# 날짜 선택
# --------------------------------------------------
st.markdown("### 📅 비교할 기간")

selected_dates = st.date_input(
    "시작일과 종료일을 선택하세요",
    value=(last_date, last_date),
    min_value=first_date,
    max_value=last_date
)


# 두 날짜가 모두 선택되었을 때
if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:

    start_date = selected_dates[0]
    end_date = selected_dates[1]

    if start_date > end_date:
        st.warning("시작일은 종료일보다 앞이어야 합니다.")
        st.stop()

    # 연도를 넘어가는 기간은 제외
    if start_date.year != end_date.year:
        st.warning("현재 버전에서는 같은 연도 안의 기간을 선택해 주세요.")
        st.stop()

    selected_year = start_date.year

    # --------------------------------------------------
    # 각 연도의 같은 기간 평균 계산
    # --------------------------------------------------
    yearly_results = []

    years = sorted(set(item["year"] for item in data))

    for year in years:

        try:
            comparison_start = date(
                year,
                start_date.month,
                start_date.day
            )

            comparison_end = date(
                year,
                end_date.month,
                end_date.day
            )

        except ValueError:
            # 윤년 2월 29일 등 존재하지 않는 날짜
            continue

        period_data = [
            item for item in data
            if comparison_start <= item["date"] <= comparison_end
        ]

        expected_days = (
            comparison_end - comparison_start
        ).days + 1

        # 기간 전체의 데이터가 있는 연도만 비교
        if len(period_data) != expected_days:
            continue

        avg_temperature = sum(
            item["avg"] for item in period_data
        ) / len(period_data)

        valid_min = [
            item["min"]
            for item in period_data
            if item["min"] is not None
        ]

        valid_max = [
            item["max"]
            for item in period_data
            if item["max"] is not None
        ]

        period_min = min(valid_min) if valid_min else None
        period_max = max(valid_max) if valid_max else None

        yearly_results.append({
            "year": year,
            "average": avg_temperature,
            "minimum": period_min,
            "maximum": period_max
        })


    # --------------------------------------------------
    # 평균기온 높은 순 정렬
    # --------------------------------------------------
    yearly_results.sort(
        key=lambda x: x["average"],
        reverse=True
    )

    selected_result = None

    for index, result in enumerate(yearly_results):
        result["rank"] = index + 1

        if result["year"] == selected_year:
            selected_result = result


    # --------------------------------------------------
    # 결과 출력
    # --------------------------------------------------
    if selected_result is None:

        st.error(
            "선택한 기간의 데이터가 부족하여 순위를 계산할 수 없습니다."
        )

    else:

        rank = selected_result["rank"]
        total = len(yearly_results)
        average = selected_result["average"]

        percentile = (rank / total) * 100

        # 순위에 따른 문구
        if rank == 1:
            message = "🔥 기록상 가장 더웠던 기간입니다."
        elif percentile <= 5:
            message = "🔥 역대급으로 더웠던 기간입니다."
        elif percentile <= 20:
            message = "☀️ 상당히 더웠던 기간입니다."
        elif percentile <= 50:
            message = "🌤️ 비교적 따뜻한 편이었습니다."
        else:
            message = "❄️ 역대 기록과 비교하면 선선한 편이었습니다."

        st.markdown(
            f"""
            <div class="result-card">
                <div class="rank-label">
                    {total}개 연도 중 평균기온 순위
                </div>

                <div class="rank">
                    {rank}위
                </div>

                <div class="temperature">
                    평균 {average:.1f}℃
                </div>

                <div class="description">
                    {selected_year}년
                    {start_date.month}월 {start_date.day}일
                    ~
                    {end_date.month}월 {end_date.day}일
                </div>

                <div style="
                    margin-top:20px;
                    font-size:18px;
                    font-weight:700;
                ">
                    {message}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


        # --------------------------------------------------
        # 추가 정보
        # --------------------------------------------------
        st.write("")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "기간 평균",
                f"{average:.1f}℃"
            )

        with col2:
            if selected_result["maximum"] is not None:
                st.metric(
                    "가장 높은 기온",
                    f"{selected_result['maximum']:.1f}℃"
                )
            else:
                st.metric("가장 높은 기온", "-")

        with col3:
            if selected_result["minimum"] is not None:
                st.metric(
                    "가장 낮은 기온",
                    f"{selected_result['minimum']:.1f}℃"
                )
            else:
                st.metric("가장 낮은 기온", "-")


        # --------------------------------------------------
        # TOP 5
        # --------------------------------------------------
        st.write("")
        st.markdown("### 🏆 같은 기간 역대 TOP 5")

        top5 = yearly_results[:5]

        for result in top5:

            medal = ""

            if result["rank"] == 1:
                medal = "🥇"
            elif result["rank"] == 2:
                medal = "🥈"
            elif result["rank"] == 3:
                medal = "🥉"
            else:
                medal = "　"

            if result["year"] == selected_year:
                marker = " ← 선택한 연도"
            else:
                marker = ""

            st.markdown(
                f"""
                **{medal} {result['rank']}위 · {result['year']}년**
                &nbsp;&nbsp; {result['average']:.1f}℃ {marker}
                """
            )


        # --------------------------------------------------
        # 간단한 막대 그래프
        # Streamlit 기본 기능만 사용
        # --------------------------------------------------
        st.write("")
        st.markdown("### 📊 TOP 10 기온")

        chart_data = {}

        for result in yearly_results[:10]:
            chart_data[str(result["year"])] = result["average"]

        st.bar_chart(chart_data)


else:
    st.info("달력에서 시작일과 종료일을 모두 선택해 주세요.")
