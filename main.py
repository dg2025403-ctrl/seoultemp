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

    # 반드시 seoul.csv 사용
    with open("seoul.csv", "r", encoding="utf-8-sig") as file:

        reader = csv.DictReader(file)

        for row in reader:

            try:
                # 날짜 앞뒤 공백/탭 제거
                date_text = row["날짜"].strip()

                current_date = datetime.strptime(
                    date_text,
                    "%Y-%m-%d"
                ).date()

                # 평균기온이 없는 행은 제외
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
                # 잘못된 데이터는 건너뜀
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
    st.error("seoul.csv에서 기온 데이터를 읽지 못했습니다.")
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
    "서울 기온 기록을 비교합니다."
)

st.caption(
    "날짜를 선택하면 같은 기간의 역대 평균기온 순위를 알려드려요."
)

st.divider()


# ==================================================
# 날짜 선택
# ==================================================

st.subheader("📅 기간 선택")

selected_dates = st.date_input(
    "시작일과 종료일을 선택하세요",
    value=(last_date, last_date),
    min_value=first_date,
    max_value=last_date,
    format="YYYY/MM/DD"
)


# 날짜를 하나만 선택했을 경우
if not isinstance(selected_dates, (tuple, list)):
    st.info("시작일과 종료일을 선택해 주세요.")
    st.stop()


if len(selected_dates) != 2:
    st.info("달력에서 종료일까지 선택해 주세요.")
    st.stop()


start_date = selected_dates[0]
end_date = selected_dates[1]


# ==================================================
# 날짜 검사
# ==================================================

if start_date > end_date:
    st.warning("시작일은 종료일보다 앞이어야 합니다.")
    st.stop()


# 현재 버전은 같은 연도 안에서 비교
if start_date.year != end_date.year:
    st.warning(
        "현재는 같은 연도 안의 기간만 비교할 수 있습니다.\n\n"
        "예: 2026/08/01 ~ 2026/08/07"
    )
    st.stop()


selected_year = start_date.year


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
        # 2월 29일처럼 해당 연도에 없는 날짜
        continue


    # 비교해야 하는 전체 날짜 수
    expected_days = (
        comparison_end - comparison_start
    ).days + 1


    # 해당 연도의 기간 데이터
    period_data = [
        item
        for item in data
        if comparison_start
        <= item["date"]
        <= comparison_end
    ]


    # 하루라도 데이터가 빠진 연도는 제외
    if len(period_data) != expected_days:
        continue


    # ------------------------------
    # 평균기온
    # ------------------------------

    avg_temperature = sum(
        item["avg"]
        for item in period_data
    ) / len(period_data)


    # ------------------------------
    # 최저기온
    # ------------------------------

    valid_min = [
        item["min"]
        for item in period_data
        if item["min"] is not None
    ]

    if valid_min:
        period_min = min(valid_min)
    else:
        period_min = None


    # ------------------------------
    # 최고기온
    # ------------------------------

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


# 순위 부여
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
# 결과가 없을 경우
# ==================================================

if selected_result is None:

    st.error(
        "선택한 기간의 데이터가 부족하여 "
        "순위를 계산할 수 없습니다."
    )

    st.stop()


# ==================================================
# 결과 계산
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
    detail = "서울 기온 기록 중 1위입니다."

elif percentile <= 5:

    emoji = "🔥"
    message = "역대급으로 더웠던 기간"
    detail = (
        f"전체 기록 중 상위 "
        f"{percentile:.1f}%에 해당합니다."
    )

elif percentile <= 20:

    emoji = "☀️"
    message = "상당히 더웠던 기간"
    detail = (
        f"전체 기록 중 상위 "
        f"{percentile:.1f}%에 해당합니다."
    )

elif percentile <= 50:

    emoji = "🌤️"
    message = "비교적 따뜻했던 기간"
    detail = (
        f"{total}개 연도의 같은 기간과 비교했습니다."
    )

else:

    emoji = "🌿"
    message = "비교적 선선했던 기간"
    detail = (
        f"{total}개 연도의 같은 기간과 비교했습니다."
    )


# ==================================================
# 선택 기간 표시
# ==================================================

st.write("")
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


st.divider()


# ==================================================
# 메인 랭킹
# ==================================================

st.markdown(
    f"### {emoji} {total}개 연도 중 평균기온 순위"
)

st.markdown(
    f"# {rank}위"
)

st.caption(
    "같은 날짜·기간의 평균기온을 "
    "높은 순서로 비교했습니다."
)

st.write("")


# ==================================================
# 평균 / 최고 / 최저
# ==================================================

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
# 한줄 평가
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

st.caption(
    f"매년 {start_date.month}월 {start_date.day}일"
    f" ~ "
    f"{end_date.month}월 {end_date.day}일의 "
    "평균기온을 비교했습니다."
)


top5 = yearly_results[:5]


for result in top5:

    # 메달
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
                f"**{result['year']}년**  ← 선택"
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
# 선택 연도가 TOP 5 밖에 있을 경우
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
    "같은 기간의 평균기온이 높았던 연도입니다."
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
# 하단 정보
# ==================================================

st.write("")
st.divider()

st.caption(
    f"서울 기온 데이터 · "
    f"{first_date.strftime('%Y.%m.%d')} ~ "
    f"{last_date.strftime('%Y.%m.%d')}"
)
