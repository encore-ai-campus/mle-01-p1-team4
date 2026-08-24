"""
출장 여비 계산 로직

역할
- 행정주소를 여비규정상의 지역 등급으로 분류
- 일비 / 식비 / 숙박비 계산
- 최종 예상 여비 계산

주의
- 교통비는 '실비'이므로 1차 구현에서는 총액에 포함하지 않음
- Kakao Map API 관련 코드는 이 파일에 넣지 않음
"""


# ============================================================
# 1. 여비규정 상수
# ============================================================

DAILY_ALLOWANCE = 20000

MEAL_ALLOWANCE = 20000

LODGING_LIMITS = {
    "SEOUL": 70000,
    "MAJOR": 60000,
    "OTHER": 50000
}


# ============================================================
# 2. 지역 판정에 필요한 목록
# ============================================================

MAJOR_CITIES = {
    "부산광역시",
    "대구광역시",
    "인천광역시",
    "광주광역시",
    "대전광역시",
    "울산광역시",
}

# 특별자치시 / 특별자치도 등
SPECIAL_REGIONS = {
    "세종특별자치시",
    "제주특별자치도",
}

# 수도권 판정을 위해 필요한 지역
CAPITAL_REGIONS = {
    "서울특별시",
    "인천광역시",
    "경기도",
}

PROVINCIAL_CAPITAL_CITIES = {
    "수원시",    # 경기도청
    "춘천시",    # 강원특별자치도청
    "청주시",    # 충청북도청
    "홍성군",    # 충청남도청
    "전주시",    # 전북특별자치도청
    "무안군",    # 전라남도청
    "안동시",    # 경상북도청
    "창원시",    # 경상남도청
}


# ============================================================
# 3. 지역 분류
# ============================================================

def classify_region(address: str) -> str:
    """
    행정주소를 여비규정상의 숙박비 지역 등급으로 분류한다.

    Returns
    -------
    str
        "SEOUL"
        "MAJOR"
        "OTHER"
    """

    if address is None:
        raise ValueError("주소가 올바르지 않습니다.")

    address = address.strip()

    if not address:
        raise ValueError("주소가 올바르지 않습니다.")

    # 서울: 70,000원
    if "서울특별시" in address:
        return "SEOUL"

    # 광역시: 60,000원
    for city in MAJOR_CITIES:
        if city in address:
            return "MAJOR"

    # 특별자치시 / 특별자치도: 60,000원
    for region in SPECIAL_REGIONS:
        if region in address:
            return "MAJOR"

    # 도청 소재지: 60,000원
    for city in PROVINCIAL_CAPITAL_CITIES:
        if city in address:
            return "MAJOR"

    # 수도권 해당 지역: 60,000원
    for region in CAPITAL_REGIONS:
        if region in address:
            return "MAJOR"

    # 그 외 지역: 50,000원
    return "OTHER"


# ============================================================
# 4. 지역별 1박 숙박비 상한
# ============================================================

def get_lodging_limit(address: str) -> int:
    """
    주소를 기준으로 1박 숙박비 상한액을 반환한다.

    Parameters
    ----------
    address : str

    Returns
    -------
    int
        1박당 숙박비 상한액
    """

    # classify_region()을 호출하여 지역 등급을 얻는다.
    region_grade = classify_region(address)

    # LODGING_LIMITS에서 해당 등급의 금액을 찾는다.
    limit = LODGING_LIMITS[region_grade]

    # 숙박비 상한액을 반환한다.
    return limit


# ============================================================
# 5. 일비 계산
# ============================================================

def calculate_daily_allowance(days: int) -> int:
    """
    출장 일수에 따른 일비를 계산한다.
    """

    # days가 정수인지 또는 계산 가능한 값인지 검증한다.
    if not isinstance(days, int):
        raise ValueError("출장 일수는 정수여야 합니다.")

    # days가 0보다 작은 경우 예외 처리한다.
    if days < 0:
        raise ValueError("출장 일수는 0 이상이어야 합니다.")


    # DAILY_ALLOWANCE * days를 계산한다.
    return DAILY_ALLOWANCE * days


# ============================================================
# 6. 식비 계산
# ============================================================

def calculate_meal_allowance(days: int) -> int:
    """
    출장 일수에 따른 식비를 계산한다.
    """

    # days가 정수인지 또는 계산 가능한 값인지 검증한다.
    if not isinstance(days, int):
        raise ValueError("출장 일수는 정수여야 합니다.")

    # days가 0보다 작은 경우 예외 처리한다.
    if days < 0:
        raise ValueError("출장 일수는 0 이상이어야 합니다.")

    return MEAL_ALLOWANCE * days


# ============================================================
# 7. 숙박비 계산
# ============================================================

def calculate_lodging(address: str, nights: int) -> int:
    """
    출장지와 숙박 일수를 기준으로 숙박비 상한 총액을 계산한다.
    """

    if not isinstance(nights, int):
        raise ValueError("숙박 일수는 정수여야 합니다.")

    # nights가 0보다 작은 경우 예외 처리한다.
    if nights < 0:
        raise ValueError("숙박 일수는 0 이상이어야 합니다.")

    # 1박당 숙박비 상한액을 얻는다
    lodging_limit = get_lodging_limit(address)
    total_lodging = lodging_limit * nights

    return total_lodging



# ============================================================
# 8. 출장 입력값 검증
# ============================================================

def validate_travel_input(days: int, nights: int) -> None:
    """
    출장 일수와 숙박 일수의 관계가 정상적인지 검증한다.
    """

    # 입력값 타입 검증
    if not isinstance(days, int):
        raise ValueError("출장 일수는 정수여야 합니다.")

    if not isinstance(nights, int):
        raise ValueError("숙박 일수는 정수여야 합니다.")

    # 출장 일수는 최소 1일
    if days < 1:
        raise ValueError("출장 일수는 1 이상이어야 합니다.")

    # 숙박 일수는 0 이상
    if nights < 0:
        raise ValueError("숙박 일수는 0 이상이어야 합니다.")

    # 숙박 일수는 최대 출장 일수 - 1
    if nights > days - 1:
        raise ValueError(
            "숙박 일수는 출장 일수보다 적어야 합니다."
        )



# ============================================================
# 9. 최종 예상 여비 계산
# ============================================================

def calculate_travel_expense(
    address: str,
    days: int,
    nights: int,
) -> dict:
    """
    출장지, 출장일수, 숙박일수를 기준으로 예상 여비를 계산한다.

    교통비는 실비이므로 계산 결과에는 포함하지 않는다.

    Returns
    -------
    dict
        Streamlit 화면에서 사용하기 쉬운 형태의 계산 결과
    """

    # 출장 일수와 숙박 일수 검증
    validate_travel_input(days, nights)


    # 지역 등급
    region_type = classify_region(address)

    # 1박 숙박비 상한
    lodging_limit_per_night = get_lodging_limit(address)

    # 일비
    daily_allowance = calculate_daily_allowance(days)

    # 식비
    meal_allowance = calculate_meal_allowance(days)

    # 숙박비 총액
    lodging = calculate_lodging(address, nights)

    # 교통비를 제외한 예상 여비 합계
    subtotal = daily_allowance + meal_allowance + lodging

    # Streamlit에서 사용하기 쉬운 dictionary 형태로 반환
    return {
        "address": address,
        "region_type": region_type,
        "days": days,
        "nights": nights,
        "lodging_limit_per_night": lodging_limit_per_night,
        "daily_allowance": daily_allowance,
        "meal_allowance": meal_allowance,
        "lodging": lodging,
        "subtotal": subtotal,
        "transportation": "실비 별도",
    }


# ============================================================
# 10. 간단한 직접 테스트
# ============================================================

if __name__ == "__main__":

    # API 연결 전에 직접 주소를 넣어 함수가 정상 동작하는지 확인한다.
    test_addresses = [
        "서울특별시 강남구",
        "부산광역시 해운대구",
        "경기도 성남시",
        "경상북도 포항시",
    ]

    for address in test_addresses:
        try:
            result = calculate_travel_expense(
                address=address,
                days=3,
                nights=2,
            )

            print("=" * 50)
            print(f"주소: {result['address']}")
            print(f"지역 등급: {result['region_type']}")
            print(f"1박 숙박비 상한: {result['lodging_limit_per_night']:,}원")
            print(f"일비: {result['daily_allowance']:,}원")
            print(f"식비: {result['meal_allowance']:,}원")
            print(f"숙박비: {result['lodging']:,}원")
            print(f"예상 여비 합계: {result['subtotal']:,}원")
            print(f"교통비: {result['transportation']}")

        except ValueError as e:
            print(f"{address} 테스트 실패: {e}")