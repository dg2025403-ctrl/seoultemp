import streamlit as st
import csv
from datetime import datetime, date, timedelta


# =========================================================
# 페이지 설정
# =========================================================

st.set_page_config(
    page_title="서울 기온 분석",
    page_icon="🌡️",
    layout="wide"
)


# =========================================================
# CSV 데이터 불러오기
# =========================================================

@st.cache_data
def load_data():

    records = []

    with open("seoul.csv", "r", encoding="utf-8-sig") as file:

        reader = csv.DictReader(file)

        for row in reader:

            try:

                date_text = row["날짜"].strip()

                current_date = datetime.strptime(
                    date_text,
                    "%Y-%m-%d"
                ).date()

                avg_text = row["평균기온"].strip()

                if not avg_text:
                    continue

                avg_temp = float(avg_text)

                min_temp = None
                max_temp = None

                if row["최저기온"].strip():
                    min_temp = float(
                        row["최저기온"].strip()
                    )

                if row["최고기온"].strip():
                    max_temp = float(
                        row["최고기온"].strip()
                    )

                records.append({
                    "date": current_date,
                    "avg": avg_temp,
                    "min": min_temp,
                    "max": max_temp
                })

            except (ValueError, KeyError):
                continue

    records.sort(
        key=lambda x: x["date"]
    )

    return records


# =========================================================
# 데이터 준비
# =========================================================

try:
    data = load_data()

except FileNotFoundError:

    st.error(
        "seoul.csv 파일을 찾을 수 없습니다.\n\n"
        "app.py와 seoul.csv를 같은 폴더에 넣어 주세요."
    )

    st.stop()


if not data:

    st.error(
        "seoul.csv에서 기온 데이터를 읽지 못했습니다."
    )

    st.stop()


first_date = data[0]["date"]
last_date = data[-1]["date"]


# 날짜로 바로 검색하기 위한 딕셔너리
data_by_date = {
    item["date"]: item
    for item in data
}


# =========================================================
# 기간 분석 함수
# =========================================================

def analyze_period(start, end):

    current = start

    records = []

    expected_days = (
        end - start
    ).days + 1


    while current <= end:

        if current in data_by_date:
            records.append(
                data_by_date[current]
            )

        current += timedelta(days=1)


    if not records:
        return None


    # -----------------------------------------------------
    # 데이터 완성도
    # -----------------------------------------------------

    actual_days = len(records)

    completeness = (
        actual_days / expected_days
    ) * 100


    # -----------------------------------------------------
    # 평균기온
    # -----------------------------------------------------

    avg_values = [
        r["avg"]
        for r in records
    ]

    average = (
        sum(avg_values)
        / len(avg_values)
    )


    # -----------------------------------------------------
    # 최저기온
    # -----------------------------------------------------

    min_values = [
        r["min"]
        for r in records
        if r["min"] is not None
    ]


    # -----------------------------------------------------
    # 최고기온
    # -----------------------------------------------------

    max_values = [
        r["max"]
        for r in records
        if r["max"] is not None
    ]


    # -----------------------------------------------------
    # 평균 최저기온
    # -----------------------------------------------------

    average_min = None

    if min_values:

        average_min = (
            sum(min_values)
            / len(min_values)
        )


    # -----------------------------------------------------
    # 평균 최고기온
    # -----------------------------------------------------

    average_max = None

    if max_values:

        average_max = (
            sum(max_values)
            / len(max_values)
        )


    # -----------------------------------------------------
    # 기간 전체 최저기온
    # -----------------------------------------------------

    absolute_min = None
    coldest_day = None

    if min_values:

        valid_records = [
            r
            for r in records
            if r["min"] is not None
        ]

        coldest_record = min(
            valid_records,
            key=lambda x: x["min"]
        )

        absolute_min = coldest_record["min"]
        coldest_day = coldest_record["date"]


    # -----------------------------------------------------
    # 기간 전체 최고기온
    # -----------------------------------------------------

    absolute_max = None
    hottest_day = None

    if max_values:

        valid_records = [
            r
            for r in records
            if r["max"] is not None
        ]

        hottest_record = max(
            valid_records,
            key=lambda x: x["max"]
        )

        absolute_max = hottest_record["max"]
        hottest_day = hottest_record["date"]


    # -----------------------------------------------------
    # 가장 평균기온이 높았던 날
    # -----------------------------------------------------

    warmest_avg_record = max(
        records,
        key=lambda x: x["avg"]
    )


    # -----------------------------------------------------
    # 가장 평균기온이 낮았던 날
    # -----------------------------------------------------

    coldest_avg_record = min(
        records,
        key=lambda x: x["avg"]
    )


    # -----------------------------------------------------
    # 30도 이상 일수
    # -----------------------------------------------------

    days_over_30 = sum(
        1
        for r in records
        if r["max"] is not None
        and r["max"] >= 30
    )


    # -----------------------------------------------------
    # 35도 이상 일수
    # -----------------------------------------------------

    days_over_35 = sum(
        1
        for r in records
        if r["max"] is not None
        and r["max"] >= 35
    )


    # -----------------------------------------------------
    # 영하 일수
    # =====================================================

    days_below_zero = sum(
        1
        for r in records
        if r["min"] is not None
        and r["min"] < 0
    )


    # -----------------------------------------------------
    # 일교차 평균
    # -----------------------------------------------------

    daily_ranges = [
        r["max"] - r["min"]
        for r in records
        if r["max"] is not None
        and r["min"] is not None
    ]


    average_range = None

    if daily_ranges:

        average_range = (
            sum(daily_ranges)
            / len(daily_ranges)
        )


    return {

        "start": start,
        "end": end,

        "expected_days": expected_days,
        "actual_days": actual_days,
        "completeness": completeness,

        "average": average,

        "average_min": average_min,
        "average_max": average_max,

        "absolute_min": absolute_min,
        "absolute_max": absolute_max,

        "coldest_day": coldest_day,
        "hottest_day": hottest_day,

        "warmest_avg_day":
            warmest_avg_record["date"],

        "warmest_avg":
            warmest_avg_record["avg"],

        "coldest_avg_day":
            coldest_avg_record["date"],

        "coldest_avg":
            coldest_avg_record["avg"],

        "days_over_30": days_over_30,
        "days_over_35": days_over_35,
        "days_below_zero": days_below_zero,

        "average_range": average_range,

        "records": records
    }


# =========================================================
# 제목
# =========================================================

st.title("🌡️ 서울 기온 분석")

st.write(
    f"서울의 **{first_date.strftime('%Y.%m.%d')}부터 "
    f"{last_date.strftime('%Y.%m.%d')}까지** 기온 데이터를 "
    "원하는 기간으로 분석합니다."
)

st.caption(
    "평균기온뿐 아니라 역대 순위, 최고·최저기온, "
    "이상고온·한파일수와 장기 변화를 함께 확인할 수 있습니다."
)

st.divider()


# =========================================================
# 날짜 선택
# =========================================================

st.subheader("📅 분석 기간")

col1, col2 = st.columns(2)


with col1:

    start_date = st.date_input(
        "시작 날짜",
        value=last_date,
        min_value=first_date,
        max_value=last_date,
        format="YYYY/MM/DD",
        key="start"
    )


with col2:

    end_date = st.date_input(
        "종료 날짜",
        value=last_date,
        min_value=first_date,
        max_value=last_date,
        format="YYYY/MM/DD",
        key="end"
    )


if start_date > end_date:

    st.error(
        "종료 날짜는 시작 날짜보다 뒤여야 합니다."
    )

    st.stop()


period_days = (
    end_date - start_date
).days + 1


st.write(
    f"선택한 기간: **{period_days:,}일**"
)


# =========================================================
# 선택 기간 분석
# =========================================================

selected = analyze_period(
    start_date,
    end_date
)


if selected is None:

    st.error(
        "선택한 기간의 데이터를 분석할 수 없습니다."
    )

    st.stop()


# =========================================================
# 데이터 완성도 확인
# =========================================================

if selected["completeness"] < 100:

    st.warning(
        f"선택한 {selected['expected_days']:,}일 중 "
        f"{selected['actual_days']:,}일의 데이터만 존재합니다. "
        f"데이터 완성도는 {selected['completeness']:.1f}%입니다."
    )


# =========================================================
# 기본 분석
# =========================================================

st.divider()

st.subheader("📊 기간 기온 요약")


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "🌡️ 평균기온",
        f"{selected['average']:.1f}℃"
    )


with col2:

    if selected["average_max"] is not None:

        st.metric(
            "☀️ 평균 최고기온",
            f"{selected['average_max']:.1f}℃"
        )


with col3:

    if selected["average_min"] is not None:

        st.metric(
            "❄️ 평균 최저기온",
            f"{selected['average_min']:.1f}℃"
        )


col1, col2, col3 = st.columns(3)


with col1:

    if selected["absolute_max"] is not None:

        st.metric(
            "🔥 기간 최고기온",
            f"{selected['absolute_max']:.1f}℃"
        )


with col2:

    if selected["absolute_min"] is not None:

        st.metric(
            "🧊 기간 최저기온",
            f"{selected['absolute_min']:.1f}℃"
        )


with col3:

    if selected["average_range"] is not None:

        st.metric(
            "↕️ 평균 일교차",
            f"{selected['average_range']:.1f}℃"
        )


# =========================================================
# 역대 동일 계절 기간 비교
# =========================================================

st.divider()

st.subheader("🏆 역대 기온 순위")

st.caption(
    "선택한 기간과 같은 월·일에서 시작하는 "
    "동일한 길이의 과거 기간을 비교합니다."
)


historical_results = []


for year in range(
    first_date.year,
    last_date.year + 1
):

    try:

        comparison_start = date(
            year,
            start_date.month,
            start_date.day
        )

    except ValueError:

        # 2월 29일이면 해당 연도의 2월 28일 사용
        comparison_start = date(
            year,
            2,
            28
        )


    comparison_end = (
        comparison_start
        + timedelta(days=period_days - 1)
    )


    if comparison_start < first_date:
        continue

    if comparison_end > last_date:
        continue


    result = analyze_period(
        comparison_start,
        comparison_end
    )


    if result is None:
        continue


    # 데이터가 95% 이상 있는 기간만 순위에 사용
    if result["completeness"] < 95:
        continue


    historical_results.append(
        result
    )


# 선택 기간이 기존 비교에 없다면 추가
selected_exists = any(

    r["start"] == start_date
    and r["end"] == end_date

    for r in historical_results
)


if not selected_exists:

    historical_results.append(
        selected
    )


# =========================================================
# 평균기온 순위
# =========================================================

average_ranking = sorted(
    historical_results,
    key=lambda x: x["average"],
    reverse=True
)


selected_average_rank = None


for index, result in enumerate(
    average_ranking,
    start=1
):

    if (
        result["start"] == start_date
        and
        result["end"] == end_date
    ):

        selected_average_rank = index
        break


total_periods = len(
    average_ranking
)


# =========================================================
# 평균 최고기온 순위
# =========================================================

max_ranking = [
    r
    for r in historical_results
    if r["average_max"] is not None
]


max_ranking.sort(
    key=lambda x: x["average_max"],
    reverse=True
)


selected_max_rank = None


for index, result in enumerate(
    max_ranking,
    start=1
):

    if (
        result["start"] == start_date
        and
        result["end"] == end_date
    ):

        selected_max_rank = index
        break


# =========================================================
# 평균 최저기온 순위
# =========================================================

min_ranking = [
    r
    for r in historical_results
    if r["average_min"] is not None
]


min_ranking.sort(
    key=lambda x: x["average_min"],
    reverse=True
)


selected_min_rank = None


for index, result in enumerate(
    min_ranking,
    start=1
):

    if (
        result["start"] == start_date
        and
        result["end"] == end_date
    ):

        selected_min_rank = index
        break


# =========================================================
# 순위 출력
# =========================================================

col1, col2, col3 = st.columns(3)


with col1:

    if selected_average_rank is not None:

        st.metric(
            "🌡️ 평균기온 순위",
            f"{selected_average_rank}위",
            f"{total_periods}개 기간"
        )


with col2:

    if selected_max_rank is not None:

        st.metric(
            "☀️ 평균 최고기온 순위",
            f"{selected_max_rank}위",
            f"{len(max_ranking)}개 기간"
        )


with col3:

    if selected_min_rank is not None:

        st.metric(
            "🌙 평균 최저기온 순위",
            f"{selected_min_rank}위",
            f"{len(min_ranking)}개 기간"
        )


# =========================================================
# 상위 비율
# =========================================================

if selected_average_rank is not None:

    top_percent = (
        selected_average_rank
        / total_periods
    ) * 100


    if selected_average_rank == 1:

        st.success(
            "🏆 같은 계절·기간의 기록 중 "
            "**평균기온이 가장 높습니다.**"
        )


    elif top_percent <= 5:

        st.warning(
            f"🔥 평균기온 기준 "
            f"**상위 {top_percent:.1f}%**에 해당하는 "
            "매우 더운 기간입니다."
        )


    elif top_percent <= 20:

        st.warning(
            f"☀️ 평균기온 기준 "
            f"**상위 {top_percent:.1f}%**에 해당합니다."
        )


    elif top_percent <= 50:

        st.info(
            "🌤️ 역대 같은 기간과 비교하면 "
            "평균보다 따뜻한 편입니다."
        )


    else:

        st.info(
            "🌿 역대 같은 기간과 비교하면 "
            "상대적으로 선선한 편입니다."
        )


# =========================================================
# 역사적 평균
# =========================================================

historical_average = (
    sum(
        r["average"]
        for r in historical_results
    )
    / len(historical_results)
)


difference = (
    selected["average"]
    - historical_average
)


st.write("")

col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "역대 같은 기간 평균",
        f"{historical_average:.1f}℃"
    )


with col2:

    st.metric(
        "선택 기간",
        f"{selected['average']:.1f}℃",
        f"{difference:+.1f}℃"
    )


with col3:

    if difference > 0:

        comparison_text = "더 높음"

    elif difference < 0:

        comparison_text = "더 낮음"

    else:

        comparison_text = "같음"


    st.metric(
        "역대 평균과 비교",
        comparison_text
    )


# =========================================================
# 극한 기온 분석
# =========================================================

st.divider()

st.subheader("🔥❄️ 극한 기온")


col1, col2 = st.columns(2)


with col1:

    st.markdown("#### 🔥 가장 더웠던 날")

    if selected["hottest_day"]:

        st.metric(
            selected["hottest_day"].strftime(
                "%Y.%m.%d"
            ),
            f"{selected['absolute_max']:.1f}℃"
        )


with col2:

    st.markdown("#### ❄️ 가장 추웠던 날")

    if selected["coldest_day"]:

        st.metric(
            selected["coldest_day"].strftime(
                "%Y.%m.%d"
            ),
            f"{selected['absolute_min']:.1f}℃"
        )


# =========================================================
# 기온 특징
# =========================================================

st.divider()

st.subheader("🔎 기간 특징")


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "☀️ 30℃ 이상",
        f"{selected['days_over_30']:,}일"
    )


with col2:

    st.metric(
        "🔥 35℃ 이상",
        f"{selected['days_over_35']:,}일"
    )


with col3:

    st.metric(
        "❄️ 영하",
        f"{selected['days_below_zero']:,}일"
    )


# =========================================================
# TOP 5
# =========================================================

st.divider()

st.subheader("🏅 평균기온 TOP 5")


for index, result in enumerate(
    average_ranking[:5],
    start=1
):

    if index == 1:
        medal = "🥇"

    elif index == 2:
        medal = "🥈"

    elif index == 3:
        medal = "🥉"

    else:
        medal = f"{index}위"


    col1, col2, col3 = st.columns(
        [1, 4, 2]
    )


    with col1:

        st.markdown(
            f"### {medal}"
        )


    with col2:

        period_text = (
            f"{result['start'].strftime('%Y.%m.%d')}"
            f" ~ "
            f"{result['end'].strftime('%Y.%m.%d')}"
        )


        if (
            result["start"] == start_date
            and result["end"] == end_date
        ):

            st.markdown(
                f"**{period_text}** ← 선택"
            )

        else:

            st.markdown(
                f"**{period_text}**"
            )


    with col3:

        st.markdown(
            f"### {result['average']:.1f}℃"
        )


# =========================================================
# 선택 기간이 TOP 5 밖이면 표시
# =========================================================

if (
    selected_average_rank is not None
    and selected_average_rank > 5
):

    st.write("")

    st.caption("내가 선택한 기간")

    col1, col2, col3 = st.columns(
        [1, 4, 2]
    )


    with col1:

        st.markdown(
            f"### {selected_average_rank}위"
        )


    with col2:

        st.markdown(
            f"**{start_date.strftime('%Y.%m.%d')} "
            f"~ {end_date.strftime('%Y.%m.%d')}**"
        )


    with col3:

        st.markdown(
            f"### {selected['average']:.1f}℃"
        )


# =========================================================
# 연도별 비교 그래프
# =========================================================

st.divider()

st.subheader("📈 장기 기온 변화")

st.caption(
    "선택한 기간과 같은 계절·길이의 평균기온이 "
    "시간이 지나면서 어떻게 변했는지 보여줍니다."
)


trend_data = {}


for result in sorted(
    historical_results,
    key=lambda x: x["start"]
):

    trend_data[
        str(result["start"].year)
    ] = result["average"]


st.line_chart(
    trend_data,
    y_label="평균기온 (℃)"
)


# =========================================================
# TOP 10 그래프
# =========================================================

st.divider()

st.subheader("📊 가장 더웠던 기간 TOP 10")


top10_data = {}


for result in average_ranking[:10]:

    label = str(
        result["start"].year
    )

    top10_data[label] = (
        result["average"]
    )


st.bar_chart(
    top10_data,
    y_label="평균기온 (℃)"
)


# =========================================================
# 분석 설명
# =========================================================

st.divider()

st.subheader("ℹ️ 분석 기준")

st.write(
    """
- **평균기온**: 선택한 기간의 일평균기온 평균
- **평균 최고기온**: 매일의 최고기온을 기간 전체에서 평균
- **평균 최저기온**: 매일의 최저기온을 기간 전체에서 평균
- **기간 최고기온**: 선택 기간 중 가장 높은 기온
- **기간 최저기온**: 선택 기간 중 가장 낮은 기온
- **역대 순위**: 같은 월·일에서 시작하는 동일 길이의 기간끼리 비교
- **30℃ 이상**: 일 최고기온이 30℃ 이상인 날
- **35℃ 이상**: 일 최고기온이 35℃ 이상인 날
- **영하**: 일 최저기온이 0℃ 미만인 날
"""
)


# =========================================================
# 데이터 정보
# =========================================================

st.divider()

st.caption(
    f"서울 기온 데이터 · "
    f"{first_date.strftime('%Y.%m.%d')} ~ "
    f"{last_date.strftime('%Y.%m.%d')} · "
    f"총 {len(data):,}일 기록"
)
