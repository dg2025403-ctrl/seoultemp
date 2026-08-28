import streamlit as st
import csv
from datetime import datetime, timedelta


# ==================================================
# 페이지 설정
# ==================================================

st.set_page_config(
    page_title="서울 기온 랭킹",
    page_icon="🌡️",
    layout="centered"
)


# ==================================================
# CSV 불러오기
# ==================================================

@st.cache_data
def load_data():

    records = []

    # 파일 이름은 반드시 seoul.csv
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


    # 날짜 순 정렬
    records.sort(
        key=lambda x: x["date"]
    )

    return records


# ==================================================
# 데이터 준비
# ==================================================

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
        "seoul.csv에서 데이터를 읽지 못했습니다."
    )

    st.stop()


first_date = data[0]["date"]
last_date = data[-1]["date"]


# 날짜 → 데이터
data_by_date = {
    item["date"]: item
    for item in data
}


# ==================================================
# 제목
# ==================================================

st.title("🌡️ 서울 기온 랭킹")

st.write(
    f"**{first_date.year}년부터 {last_date.year}년까지**의 "
    "서울 기온 기록을 비교합니다."
)

st.caption(
    "원하는 시작일과 종료일을 선택하면 "
    "같은 길이의 과거 기간과 평균기온을 비교합니다."
)

st.divider()


# ==================================================
# 날짜 선택
# ==================================================

st.subheader("📅 비교할 기간")

col1, col2 = st.columns(2)


with col1:

    start_date = st.date_input(
        "시작 날짜",
        value=last_date,
        min_value=first_date,
        max_value=last_date,
        format="YYYY/MM/DD",
        key="start_date"
    )


with col2:

    end_date = st.date_input(
        "종료 날짜",
        value=last_date,
        min_value=first_date,
        max_value=last_date,
        format="YYYY/MM/DD",
        key="end_date"
    )


# ==================================================
# 날짜 검사
# ==================================================

if start_date > end_date:

    st.error(
        "⚠️ 종료 날짜는 시작 날짜보다 뒤여야 합니다."
    )

    st.stop()


# ==================================================
# 기간 길이
# ==================================================

period_days = (
    end_date - start_date
).days + 1


st.caption(
    f"선택한 기간 · **{period_days:,}일**"
)


# ==================================================
# 기간 계산 함수
# ==================================================

def calculate_period(start, days):

    temperatures = []
    min_temperatures = []
    max_temperatures = []


    for i in range(days):

        current_date = (
            start + timedelta(days=i)
        )


        # 하루라도 데이터가 없으면
        # 비교 대상에서 제외
        if current_date not in data_by_date:

            return None


        record = data_by_date[current_date]


        temperatures.append(
            record["avg"]
        )


        if record["min"] is not None:

            min_temperatures.append(
                record["min"]
            )


        if record["max"] is not None:

            max_temperatures.append(
                record["max"]
            )


    if not temperatures:

        return None


    average = (
        sum(temperatures)
        / len(temperatures)
    )


    minimum = (
        min(min_temperatures)
        if min_temperatures
        else None
    )


    maximum = (
        max(max_temperatures)
        if max_temperatures
        else None
    )


    return {
        "average": average,
        "minimum": minimum,
        "maximum": maximum
    }


# ==================================================
# 선택 기간 계산
# ==================================================

selected_result = calculate_period(
    start_date,
    period_days
)


if selected_result is None:

    st.error(
        "선택한 기간에 누락된 기온 데이터가 있어 "
        "평균기온을 계산할 수 없습니다."
    )

    st.stop()


# ==================================================
# 모든 동일 길이 기간 비교
#
# 너무 비슷한 기간이 매일 겹치는 것을 방지하기 위해
# 비교 기간의 시작점을 1년 단위로 이동
#
# 예:
# 선택 2010.01.01 ~ 2020.12.31
#
# 비교
# 1908.01.01 ~ 1918.12.31
# 1909.01.01 ~ 1919.12.31
# 1910.01.01 ~ 1920.12.31
# ...
# ==================================================

results = []


for year in range(
    first_date.year,
    last_date.year + 1
):

    try:

        comparison_start = start_date.replace(
            year=year
        )

    except ValueError:

        # 2월 29일 → 2월 28일
        comparison_start = start_date.replace(
            year=year,
            day=28
        )


    comparison_end = (
        comparison_start
        + timedelta(days=period_days - 1)
    )


    # 데이터 범위를 벗어나면 제외
    if comparison_start < first_date:
        continue


    if comparison_end > last_date:
        continue


    result = calculate_period(
        comparison_start,
        period_days
    )


    if result is None:
        continue


    results.append({
        "start": comparison_start,
        "end": comparison_end,
        "average": result["average"],
        "minimum": result["minimum"],
        "maximum": result["maximum"]
    })


# ==================================================
# 선택한 기간이 목록에 없는 경우 추가
# ==================================================

selected_exists = False


for result in results:

    if (
        result["start"] == start_date
        and
        result["end"] == end_date
    ):

        selected_exists = True
        break


if not selected_exists:

    results.append({
        "start": start_date,
        "end": end_date,
        "average": selected_result["average"],
        "minimum": selected_result["minimum"],
        "maximum": selected_result["maximum"]
    })


# ==================================================
# 평균기온 순 정렬
# ==================================================

results.sort(
    key=lambda x: x["average"],
    reverse=True
)


# ==================================================
# 순위 부여
# ==================================================

for index, result in enumerate(results):

    result["rank"] = index + 1


# ==================================================
# 선택한 기간 순위 찾기
# ==================================================

selected_rank_result = None


for result in results:

    if (
        result["start"] == start_date
        and
        result["end"] == end_date
    ):

        selected_rank_result = result
        break


if selected_rank_result is None:

    st.error(
        "순위를 계산하지 못했습니다."
    )

    st.stop()


# ==================================================
# 결과값
# ==================================================

rank = selected_rank_result["rank"]

total = len(results)

average = selected_rank_result["average"]

percentile = (
    rank / total
) * 100


# ==================================================
# 평가 문구
# ==================================================

if rank == 1:

    emoji = "🏆"

    message = "가장 더웠던 기간"

    detail = (
        "비교 가능한 같은 길이의 기간 중 "
        "평균기온이 가장 높습니다."
    )


elif percentile <= 5:

    emoji = "🔥"

    message = "역대급으로 더웠던 기간"

    detail = (
        f"전체 비교 기간 중 "
        f"상위 {percentile:.1f}%입니다."
    )


elif percentile <= 20:

    emoji = "☀️"

    message = "상당히 더웠던 기간"

    detail = (
        f"전체 비교 기간 중 "
        f"상위 {percentile:.1f}%입니다."
    )


elif percentile <= 50:

    emoji = "🌤️"

    message = "비교적 따뜻했던 기간"

    detail = (
        f"총 {total}개 기간과 비교했습니다."
    )


else:

    emoji = "🌿"

    message = "비교적 선선했던 기간"

    detail = (
        f"총 {total}개 기간과 비교했습니다."
    )


# ==================================================
# 결과 화면
# ==================================================

st.write("")
st.divider()


# --------------------------------------------------
# 선택 기간
# --------------------------------------------------

st.caption("선택한 기간")

st.subheader(
    f"{start_date.strftime('%Y.%m.%d')} "
    f"→ "
    f"{end_date.strftime('%Y.%m.%d')}"
)

st.caption(
    f"총 {period_days:,}일"
)


# --------------------------------------------------
# 순위
# --------------------------------------------------

st.write("")

st.markdown(
    f"### {emoji} {total}개 기간 중 평균기온 순위"
)

st.markdown(
    f"# {rank}위"
)

st.caption(
    "같은 시작 월·일에서 시작하는 "
    "동일한 길이의 기간과 비교했습니다."
)


# --------------------------------------------------
# 기온
# --------------------------------------------------

st.write("")

col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "🌡️ 평균기온",
        f"{average:.1f}℃"
    )


with col2:

    if selected_rank_result["maximum"] is not None:

        st.metric(
            "🔺 최고기온",
            f"{selected_rank_result['maximum']:.1f}℃"
        )

    else:

        st.metric(
            "🔺 최고기온",
            "-"
        )


with col3:

    if selected_rank_result["minimum"] is not None:

        st.metric(
            "🔻 최저기온",
            f"{selected_rank_result['minimum']:.1f}℃"
        )

    else:

        st.metric(
            "🔻 최저기온",
            "-"
        )


# ==================================================
# 평가 메시지
# ==================================================

st.write("")


if rank == 1:

    st.success(
        f"🏆 **{message}**\n\n"
        f"{detail}"
    )


elif percentile <= 20:

    st.warning(
        f"{emoji} **{message}**\n\n"
        f"{detail}"
    )


else:

    st.info(
        f"{emoji} **{message}**\n\n"
        f"{detail}"
    )


# ==================================================
# TOP 5
# ==================================================

st.write("")
st.divider()

st.subheader("🏅 동일 기간 길이 TOP 5")

st.caption(
    f"{period_days:,}일 동안의 평균기온 비교"
)


for result in results[:5]:

    # 순위 표시
    if result["rank"] == 1:

        medal = "🥇"

    elif result["rank"] == 2:

        medal = "🥈"

    elif result["rank"] == 3:

        medal = "🥉"

    else:

        medal = f"{result['rank']}위"


    col_rank, col_period, col_temp = st.columns(
        [1, 4, 2]
    )


    with col_rank:

        st.markdown(
            f"### {medal}"
        )


    with col_period:

        period_text = (
            f"{result['start'].strftime('%Y.%m.%d')}"
            f" ~ "
            f"{result['end'].strftime('%Y.%m.%d')}"
        )


        if (
            result["start"] == start_date
            and
            result["end"] == end_date
        ):

            st.markdown(
                f"**{period_text}**  ← 선택"
            )

        else:

            st.markdown(
                f"**{period_text}**"
            )


    with col_temp:

        st.markdown(
            f"### {result['average']:.1f}℃"
        )


# ==================================================
# 선택 기간이 TOP 5 밖일 경우
# ==================================================

if rank > 5:

    st.write("")

    st.caption("내가 선택한 기간")


    col1, col2, col3 = st.columns(
        [1, 4, 2]
    )


    with col1:

        st.markdown(
            f"### {rank}위"
        )


    with col2:

        st.markdown(
            f"**{start_date.strftime('%Y.%m.%d')}"
            f" ~ "
            f"{end_date.strftime('%Y.%m.%d')}**"
        )


    with col3:

        st.markdown(
            f"### {average:.1f}℃"
        )


# ==================================================
# TOP 10 그래프
# ==================================================

st.write("")
st.divider()

st.subheader("📊 평균기온 TOP 10")


chart_data = {}


for result in results[:10]:

    label = str(
        result["start"].year
    )

    chart_data[label] = (
        result["average"]
    )


st.bar_chart(
    chart_data,
    y_label="평균기온 (℃)"
)


# ==================================================
# 데이터 정보
# ==================================================

st.write("")
st.divider()

st.caption(
    f"서울 기온 데이터 · "
    f"{first_date.strftime('%Y.%m.%d')} ~ "
    f"{last_date.strftime('%Y.%m.%d')}"
)
