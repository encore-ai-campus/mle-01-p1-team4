from src.config import RAW_DIR
import streamlit as st

from src.services.kakao_map import (
    render_kakao_map,
    coordinates_to_address,
)

from src.services.travel_expense import (
    calculate_travel_expense,
)


# =========================================================
# 자주 찾는 업무
# =========================================================


def get_frequent_tasks():
    return [
        {"icon": "🏖️", "label": "휴가 · 연차", "question": "연차휴가 사용 기준을 알려줘"},
        {"icon": "💰", "label": "급여 · 수당", "question": "급여와 수당 지급 기준을 알려줘"},
        {"icon": "✈️", "label": "출장 · 출장비", "question": "국내 출장 여비 지급 기준을 알려줘"},
        {"icon": "📈", "label": "승진 · 인사", "question": "승진 관련 기준을 알려줘"},
        {"icon": "🏠", "label": "휴직 · 복직", "question": "휴직과 복직 기준을 알려줘"},
        {"icon": "🔐", "label": "보안 · 자료", "question": "사내 보안 관련 규정을 알려줘"},
    ]


# =========================================================
# 추천 질문
# =========================================================


def get_recommended_questions():
    """
    홈 화면에 표시할 추천 질문을 반환합니다.
    """

    questions = [
    '점심시간은 몇 시부터 몇 시까지인가요?',
    '휴직 중에도 직무급을 받을 수 있나요?',
    '1급 이하 직원의 국내 출장 식비는 얼마인가요?',
    '시간단위 연차 사용 기준은 어떻게 되나요?',
    '숙박비 지역별 상한액은 얼마인가요?'
    ]

    return questions


# =========================================================
# 담당 부서
# =========================================================


def get_department_info():
    """
    업무별 담당 부서 정보를 반환합니다.
    """

    departments = [
        {
            "업무 분야": "급여, 퇴직금, 원천세, 연말정산",
            "지사/부서": "운영지원처",
            "연락처": "053-714-7834",
        },
        {
            "업무 분야": "인사·복무·인권",
            "지사/부서": "운영지원처",
            "연락처": "051-794-5031",
        },
        {
            "업무 분야": "인사처 업무총괄",
            "지사/부서": "인사처",
            "연락처": "063-713-1590",
        },
        {
            "업무 분야": "여비·근태·건강검진",
            "지사/부서": "운영지원처",
            "연락처": "062-714-6803",
        },
        {
            "업무 분야": "정보보안운영처 업무총괄",
            "지사/부서": "정보보안운영처",
            "연락처": "063-710-0441",
        },
    ]

    return departments


# =========================================================
# PDF 원문
# =========================================================


def get_regulation_pdfs():
    """
    data/raw 폴더에 존재하는 PDF 파일의
    문서명과 경로를 반환합니다.
    """

    pdfs = []

    # data/raw 폴더가 없으면 빈 리스트 반환
    if not RAW_DIR.exists():
        return pdfs

    for pdf_path in sorted(
        RAW_DIR.glob("*.pdf")
    ):
        pdfs.append(
            {
                "document_name": pdf_path.stem,
                "path": pdf_path,
            }
        )

    return pdfs

# ============================================================
# 출장 여비 계산 UI
# ============================================================

def render_travel_expense():
    """
    홈 화면 하단에 출장 여비 계산 UI를 표시한다.
    """

    st.markdown("---")

    st.subheader("🗺️ 출장 여비 간편 계산")

    st.caption(
        "지도에서 출장지를 선택하고 출장 일수와 숙박 일수를 입력하면 "
        "예상 여비를 계산합니다."
    )

    # --------------------------------------------------------
    # 1. Kakao Map
    # --------------------------------------------------------

    selected = render_kakao_map()

    # --------------------------------------------------------
    # 2. 출장 일수 / 숙박 일수
    # --------------------------------------------------------

    col_days, col_nights = st.columns(2)

    with col_days:
        days = st.number_input(
            "출장 일수",
            min_value=1,
            value=1,
            step=1,
            key="travel_days",
        )

    with col_nights:
        nights = st.number_input(
            "숙박 일수",
            min_value=0,
            value=0,
            step=1,
            key="travel_nights",
        )

    # --------------------------------------------------------
    # 3. 출장지를 아직 선택하지 않은 경우
    # --------------------------------------------------------

    if not selected:
        st.info(
            "지도에서 출장지를 클릭하면 "
            "예상 여비를 확인할 수 있습니다."
        )
        return

    # --------------------------------------------------------
    # 4. 선택된 출장지 계산
    # --------------------------------------------------------

    try:
        latitude = selected["latitude"]
        longitude = selected["longitude"]

        address = coordinates_to_address(
            latitude,
            longitude,
        )

        result = calculate_travel_expense(
            address=address,
            days=int(days),
            nights=int(nights),
        )

        # ----------------------------------------------------
        # 선택 위치
        # ----------------------------------------------------

        st.success(f"📍 선택한 출장지: {address}")

        # ----------------------------------------------------
        # 출장 정보
        # ----------------------------------------------------

        st.markdown("#### 출장 정보")

        info_col1, info_col2, info_col3 = st.columns(3)

        info_col1.metric(
            "지역 등급",
            result["region_type"],
        )

        info_col2.metric(
            "출장 일수",
            f"{result['days']}일",
        )

        info_col3.metric(
            "숙박 일수",
            f"{result['nights']}박",
        )

        # ----------------------------------------------------
        # 예상 여비
        # ----------------------------------------------------

        st.markdown("#### 예상 여비")

        cost_col1, cost_col2, cost_col3 = st.columns(3)

        cost_col1.metric(
            "일비",
            f"{result['daily_allowance']:,}원",
        )

        cost_col2.metric(
            "식비",
            f"{result['meal_allowance']:,}원",
        )

        cost_col3.metric(
            "숙박비",
            f"{result['lodging']:,}원",
        )

        st.caption(
            f"1박 숙박비 상한: "
            f"{result['lodging_limit_per_night']:,}원"
        )

        # ----------------------------------------------------
        # 합계
        # ----------------------------------------------------

        st.markdown("---")

        total_col1, total_col2 = st.columns([2, 1])

        with total_col1:
            st.markdown("### 💰 총 예상 여비")

        with total_col2:
            st.markdown(
                f"### {result['subtotal']:,}원"
            )

        st.info(
            f"🚆 교통비: {result['transportation']} "
            "(예상 여비 합계에는 포함되지 않습니다.)"
        )

    except ValueError as e:
        st.warning(str(e))

    except RuntimeError as e:
        st.error(str(e))

    except Exception as e:
        st.error(
            "출장 여비를 계산하는 중 오류가 발생했습니다."
        )
        print(f"[travel expense error] {e}")
