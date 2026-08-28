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
                # 날짜 앞뒤의 공백이나 탭 제거
                date_text = row["날짜"].strip()

                current_date = datetime.strptime(
                    date_text,
                    "%Y-%m-%d"
                ).date()

                # 평균기온
                avg_text = row["평균기온"].strip()

                if not avg_text:
                    continue

                avg_temp = float(avg_text)

                # 최저기온
                min_temp = None

                if row["최저기온"].strip():
                    min_temp = float(
                        row["최저기온"].strip()
                    )

                # 최고기온
                max_temp = None

                if row["최고기온"].strip():
                    max_temp = float(
                        row["최고기온"].strip()
                    )

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
                continue

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
        "seoul.csv에서 기온 데이터를 읽지 못했습니다."
    )

    st.stop()


first_date = min(
    item["date"] for item in data
)

last_date = max(
    item["date"] for item in data
)

years = sorted(
    set(item["year"] for item in data)
)


# ==================================================
# 상단
# ==================================================

st.title("🌡️ 서울 기온 랭킹")

st.write(
    f"**{first_date.year}년부터 {last_date.year}년까지**의 "
    "서울 기온 기록과 비교해 보세요."
)

st.caption(
    "원하는 기간을 선택하면 같은 날짜의 역대 평균기온을 비교합니다."
)

st.divider()


# ==================================================
# 날짜 선택
# ==================================================

st.subheader("📅 비교할 기간")

st.caption(
    "시작 날짜와 종료 날짜를 각각 선택할 수 있습니다."
)


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


if start_date.year != end_date.year:

    st.error(
        "⚠️ 시작 날짜와 종료 날짜는 같은 연도여야 합니다."
    )

    st.stop()


selected_year = start_date.year


# ==================================================
# 선택 기간 길이
# ==================================================

selected_days = (
    end_date - start_date
).days + 1


st.caption(
    f"선택한 기간 · 총 {selected_days}일"
)


# ==================================================
# 각 연도의 같은 기간 계산
# ==================================================

yearly_results = []


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

        # 2월 29일처럼 특정 연도에 없는 날짜
        continue


    expected_days = (
        comparison_end - comparison_start
    ).days + 1


    period_data = [
        item
        for item in data
        if comparison_start
        <= item["date"]
        <= comparison_end
    ]


    # 데이터가 하루라도 빠져 있으면
    # 해당 연도는 비교 대상에서 제외
    if len(period_data) != expected_days:
        continue


    # 평균기온 계산
    avg_temperature = sum(
        item["avg"]
        for item in period_data
    ) / len(period_data)


    # 최저기온 계산
    valid_min = [
        item["min"]
        for item in period_data
        if item["min"] is not None
    ]


    if valid_min:

        period_min = min(valid_min)

    else:

        period_min = None


    # 최고기온 계산
    valid_max = [
        item["max"]
        for item in period_data
        if item["max"] is not None
    ]


    if valid_max:

        period_max = max(valid_max)

    else:

        period_max = None


    yearly_results.append({
        "year": year,
        "average": avg_temperature,
        "minimum": period_min,
        "maximum": period_max
    })


# ==================================================
# 높은 평균기온 순으로 정렬
# ==================================================

yearly_results.sort(
    key=lambda x: x["average"],
    reverse=True
)


# ==================================================
# 순위 부여
# ==================================================

for index, result in enumerate(yearly_results):

    result["rank"] = index + 1


# ==================================================
# 선택한 연도 찾기
# ==================================================

selected_result = None


for result in yearly_results:

    if result["year"] == selected_year:

        selected_result = result

        break


# ==================================================
# 데이터가 없을 경우
# ==================================================

if selected_result is None:

    st.error(
        "선택한 기간의 데이터가 부족하여 "
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
# 평가
# ==================================================

if rank == 1:

    emoji = "🏆"

    message = "역대 가장 더웠던 기간"

    detail = (
        "서울 기온 기록 중 "
        "가장 높은 평균기온을 기록했습니다."
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
        f"{total}개 연도의 같은 기간과 "
        "비교한 결과입니다."
    )


else:

    emoji = "🌿"

    message = "비교적 선선했던 기간"

    detail = (
        f"{total}개 연도의 같은 기간과 "
        "비교한 결과입니다."
    )


# ==================================================
# 선택 기간 표시
# ==================================================

st.write("")

st.divider()

st.caption("선택한 기간")


if start_date == end_date:

    st.subheader(
        f"{selected_year}년 "
        f"{start_date.month}월 "
        f"{start_date.day}일"
    )

else:

    st.subheader(
        f"{selected_year}년 "
        f"{start_date.month}월 "
        f"{start_date.day}일"
        f"  →  "
        f"{end_date.month}월 "
        f"{end_date.day}일"
    )


st.caption(
    f"총 {selected_days}일간의 평균기온"
)


# ==================================================
# 메인 랭킹
# ==================================================

st.write("")

st.markdown(
    f"### {emoji} {total}개 연도 중"
)

st.markdown(
    f"# {rank}위"
)

st.caption(
    "같은 날짜·기간의 평균기온을 "
    "높은 순서로 비교한 결과"
)


# ==================================================
# 주요 기온
# ==================================================

st.write("")

col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        label="🌡️ 평균기온",
        value=f"{average:.1f}℃"
    )


with col2:

    if selected_result["maximum"] is not None:

        st.metric(
            label="🔺 최고기온",
            value=(
                f"{selected_result['maximum']:.1f}℃"
            )
        )

    else:

        st.metric(
            label="🔺 최고기온",
            value="-"
        )


with col3:

    if selected_result["minimum"] is not None:

        st.metric(
            label="🔻 최저기온",
            value=(
                f"{selected_result['minimum']:.1f}℃"
            )
        )

    else:

        st.metric(
            label="🔻 최저기온",
            value="-"
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

st.subheader("🏅 같은 기간 역대 TOP 5")


if start_date == end_date:

    st.caption(
        f"매년 {start_date.month}월 "
        f"{start_date.day}일의 평균기온"
    )

else:

    st.caption(
        f"매년 {start_date.month}월 "
        f"{start_date.day}일 ~ "
        f"{end_date.month}월 "
        f"{end_date.day}일의 평균기온"
    )


top5 = yearly_results[:5]


for result in top5:

    if result["rank"] == 1:

        medal = "🥇"


    elif result["rank"] == 2:

        medal = "🥈"


    elif result["rank"] == 3:

        medal = "🥉"


    else:

        medal = f"{result['rank']}위"


    col_rank, col_year, col_temp = st.columns(
        [1, 3, 2]
    )


    with col_rank:

        st.markdown(
            f"### {medal}"
        )


    with col_year:

        if result["year"] == selected_year:

            st.markdown(
                f"**{result['year']}년** ← 선택"
            )

        else:

            st.markdown(
                f"**{result['year']}년**"
            )


    with col_temp:

        st.markdown(
            f"### {result['average']:.1f}℃"
        )


# ==================================================
# 선택한 연도가 TOP 5 밖일 경우
# ==================================================

if rank > 5:

    st.write("")

    st.caption("내가 선택한 연도")

    col_rank, col_year, col_temp = st.columns(
        [1, 3, 2]
    )


    with col_rank:

        st.markdown(
            f"### {rank}위"
        )


    with col_year:

        st.markdown(
            f"**{selected_year}년** ← 선택"
        )


    with col_temp:

        st.markdown(
            f"### {average:.1f}℃"
        )


# ==================================================
# TOP 10 그래프
# ==================================================

st.write("")

st.divider()

st.subheader("📊 역대 TOP 10")

st.caption(
    "같은 기간의 평균기온이 "
    "가장 높았던 연도"
)


chart_data = {}


for result in yearly_results[:10]:

    chart_data[
        str(result["year"])
    ] = result["average"]


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
