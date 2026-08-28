import streamlit as st
import csv
from datetime import datetime, date


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
                    "year": current_date.year,
                    "avg": avg_temp,
                    "min": min_temp,
                    "max": max_temp
                })

            except (ValueError, KeyError):
                continue

    return records


# ==================================================
# 데이터 준비
# ==================================================

try:
    data = load_data()

except FileNotFoundError:

    st.error(
        "seoul.csv 파일을 찾을 수 없습니다. "
        "app.py와 같은 폴더에 넣어 주세요."
    )

    st.stop()


if not data:

    st.error("seoul.csv에서 데이터를 읽지 못했습니다.")
    st.stop()


first_date = min(
    item["date"] for item in data
)

last_date = max(
    item["date"] for item in data
)


# 날짜 검색을 빠르게 하기 위한 딕셔너리
data_by_date = {
    item["date"]: item
    for item in data
}


# ==================================================
# 상단
# ==================================================

st.title("🌡️ 서울 기온 랭킹")

st.write(
    f"**{first_date.year}년부터 {last_date.year}년까지**의 "
    "서울 기온 기록과 비교해 보세요."
)

st.caption(
    "원하는 기간을 선택하면 같은 계절·기간의 "
    "역대 평균기온 순위를 계산합니다."
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


# ==================================================
# 날짜 검사
# ==================================================

if start_date > end_date:

    st.error(
        "⚠️ 종료 날짜는 시작 날짜보다 뒤여야 합니다."
    )

    st.stop()


# ==================================================
# 기간 정보
# ==================================================

selected_days = (
    end_date - start_date
).days + 1


# 지나치게 긴 기간 방지
if selected_days > 366:

    st.warning(
        "비교 기간은 최대 1년까지 선택해 주세요."
    )

    st.stop()


st.caption(
    f"선택한 기간 · {selected_days}일"
)


# ==================================================
# 선택 기간 평균 계산 함수
# ==================================================

def calculate_period(start, end):

    current = start

    temperatures = []
    min_temperatures = []
    max_temperatures = []

    from datetime import timedelta

    while current <= end:

        if current not in data_by_date:
            return None

        record = data_by_date[current]

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

        current += timedelta(days=1)


    if not temperatures:
        return None


    return {
        "average": sum(temperatures) / len(temperatures),

        "minimum":
            min(min_temperatures)
            if min_temperatures
            else None,

        "maximum":
            max(max_temperatures)
            if max_temperatures
            else None
    }


# ==================================================
# 같은 기간을 과거 연도와 비교
# ==================================================

yearly_results = []


# 선택한 기간이 연도를 넘는지 확인
cross_year = (
    start_date.year != end_date.year
)


# 시작일 기준으로 비교 가능한 모든 연도 확인
for base_year in range(
    first_date.year,
    last_date.year + 1
):

    try:

        comparison_start = date(
            base_year,
            start_date.month,
            start_date.day
        )


        # ------------------------------------------
        # 같은 연도 안의 기간
        # ------------------------------------------

        if not cross_year:

            comparison_end = date(
                base_year,
                end_date.month,
                end_date.day
            )


        # ------------------------------------------
        # 연도를 넘어가는 기간
        # 예:
        # 2025/12/20 → 2026/01/10
        # ------------------------------------------

        else:

            comparison_end = date(
                base_year + 1,
                end_date.month,
                end_date.day
            )


    except ValueError:

        # 2월 29일 등
        continue


    # CSV 범위를 벗어나면 제외
    if comparison_start < first_date:
        continue

    if comparison_end > last_date:
        continue


    result = calculate_period(
        comparison_start,
        comparison_end
    )


    if result is None:
        continue


    yearly_results.append({

        "year": base_year,

        "start": comparison_start,

        "end": comparison_end,

        "average": result["average"],

        "minimum": result["minimum"],

        "maximum": result["maximum"]
    })


# ==================================================
# 순위 정렬
# ==================================================

yearly_results.sort(
    key=lambda x: x["average"],
    reverse=True
)


for index, result in enumerate(yearly_results):

    result["rank"] = index + 1


# ==================================================
# 내가 선택한 기간 찾기
# ==================================================

selected_result = None


for result in yearly_results:

    if (
        result["start"] == start_date
        and
        result["end"] == end_date
    ):

        selected_result = result

        break


if selected_result is None:

    st.error(
        "선택한 기간에 빠진 데이터가 있어 "
        "순위를 계산할 수 없습니다."
    )

    st.stop()


# ==================================================
# 결과
# ==================================================

rank = selected_result["rank"]
total = len(yearly_results)

average = selected_result["average"]

percentile = (
    rank / total
) * 100


# ==================================================
# 평가 문구
# ==================================================

if rank == 1:

    emoji = "🏆"
    message = "역대 가장 더웠던 기간"

    detail = (
        "비교 가능한 모든 기록 중 "
        "평균기온 1위입니다."
    )


elif percentile <= 5:

    emoji = "🔥"
    message = "역대급으로 더웠던 기간"

    detail = (
        f"전체 기록 중 상위 "
        f"{percentile:.1f}%입니다."
    )


elif percentile <= 20:

    emoji = "☀️"
    message = "상당히 더웠던 기간"

    detail = (
        f"전체 기록 중 상위 "
        f"{percentile:.1f}%입니다."
    )


elif percentile <= 50:

    emoji = "🌤️"
    message = "비교적 따뜻했던 기간"

    detail = (
        f"{total}개 기간과 비교했습니다."
    )


else:

    emoji = "🌿"
    message = "비교적 선선했던 기간"

    detail = (
        f"{total}개 기간과 비교했습니다."
    )


# ==================================================
# 선택한 기간
# ==================================================

st.write("")
st.divider()

st.caption("선택한 기간")

st.subheader(
    f"{start_date.strftime('%Y.%m.%d')} "
    f"→ "
    f"{end_date.strftime('%Y.%m.%d')}"
)

st.caption(
    f"총 {selected_days}일"
)


# ==================================================
# 메인 순위
# ==================================================

st.write("")

st.markdown(
    f"### {emoji} {total}개 기간 중 평균기온 순위"
)

st.markdown(
    f"# {rank}위"
)

st.caption(
    "같은 월·일의 기간을 역대 기록과 비교한 결과입니다."
)


# ==================================================
# 기온 정보
# ==================================================

st.write("")

col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "🌡️ 평균기온",
        f"{average:.1f}℃"
    )


with col2:

    if selected_result["maximum"] is not None:

        st.metric(
            "🔺 최고기온",
            f"{selected_result['maximum']:.1f}℃"
        )

    else:

        st.metric(
            "🔺 최고기온",
            "-"
        )


with col3:

    if selected_result["minimum"] is not None:

        st.metric(
            "🔻 최저기온",
            f"{selected_result['minimum']:.1f}℃"
        )

    else:

        st.metric(
            "🔻 최저기온",
            "-"
        )


# ==================================================
# 평가
# ==================================================

st.write("")


if rank == 1:

    st.success(
        f"🏆 **{message}**\n\n{detail}"
    )

elif percentile <= 20:

    st.warning(
        f"{emoji} **{message}**\n\n{detail}"
    )

else:

    st.info(
        f"{emoji} **{message}**\n\n{detail}"
    )


# ==================================================
# TOP 5
# ==================================================

st.write("")
st.divider()

st.subheader("🏅 역대 TOP 5")

st.caption(
    "같은 월·일 구간의 평균기온 비교"
)


for result in yearly_results[:5]:

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

        if (
            result["start"] == start_date
            and
            result["end"] == end_date
        ):

            st.markdown(
                f"**{result['start'].year}년** ← 선택"
            )

        else:

            if result["start"].year == result["end"].year:

                st.markdown(
                    f"**{result['start'].year}년**"
                )

            else:

                st.markdown(
                    f"**{result['start'].year}"
                    f"~{result['end'].year}년**"
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
            f"**{start_date.year}"
            f"~{end_date.year}년** ← 선택"
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

st.subheader("📊 역대 TOP 10")


chart_data = {}


for result in yearly_results[:10]:

    if result["start"].year == result["end"].year:

        label = str(
            result["start"].year
        )

    else:

        label = (
            f"{result['start'].year}"
            f"~{str(result['end'].year)[-2:]}"
        )


    chart_data[label] = (
        result["average"]
    )


st.bar_chart(
    chart_data,
    y_label="평균기온 (℃)"
)


# ==================================================
# 하단
# ==================================================

st.write("")
st.divider()

st.caption(
    f"서울 기온 데이터 · "
    f"{first_date.strftime('%Y.%m.%d')} ~ "
    f"{last_date.strftime('%Y.%m.%d')}"
)
