"""
Kakao Map 관련 기능

역할
- Streamlit 화면에 Kakao Map 표시
- LX 본사 위치 표시
- 사용자가 지도에서 선택한 위치 획득
- 선택 좌표를 행정주소로 변환

주의
- 여비 계산 로직은 이 파일에 작성하지 않는다.
- 여비 계산은 travel_expense.py가 담당한다.
"""

import os

import requests
import streamlit as st
from dotenv import load_dotenv


# ============================================================
# 0. 기본 설정
# ============================================================

load_dotenv()


# LX 한국국토정보공사 본사
# 전북특별자치도 전주시 덕진구 기지로 120
LX_HEADQUARTERS_LAT = 35.8379644978844
LX_HEADQUARTERS_LNG = 127.065375044325


# ============================================================
# 1. Kakao API 설정
# ============================================================

def _get_streamlit_secret(key: str):
    """
    Streamlit Secrets에서 값을 안전하게 가져온다.
    """
    try:
        return st.secrets.get(key)
    except (FileNotFoundError, KeyError, AttributeError):
        return None


def get_kakao_api_key() -> str:
    """
    Kakao REST API Key를 가져온다.

    우선순위
    1. Streamlit Secrets
    2. 환경변수(.env)
    """

    api_key = (
        _get_streamlit_secret("KAKAO_REST_API_KEY")
        or os.getenv("KAKAO_REST_API_KEY")
    )

    if not api_key:
        raise ValueError(
            "KAKAO_REST_API_KEY가 설정되어 있지 않습니다."
        )

    return api_key


def get_kakao_javascript_key() -> str:
    """
    Kakao Map 출력에 사용할 JavaScript Key를 가져온다.

    우선순위
    1. Streamlit Secrets
    2. 환경변수(.env)
    """

    javascript_key = (
        _get_streamlit_secret("KAKAO_JAVASCRIPT_KEY")
        or os.getenv("KAKAO_JAVASCRIPT_KEY")
    )

    if not javascript_key:
        raise ValueError(
            "KAKAO_JAVASCRIPT_KEY가 설정되어 있지 않습니다."
        )

    return javascript_key


# ============================================================
# 2. 좌표 -> 주소 변환
# ============================================================

def coordinates_to_address(
    latitude: float,
    longitude: float,
) -> str:
    """
    위도/경도를 Kakao Local API를 이용해 행정주소로 변환한다.

    Parameters
    ----------
    latitude : float
        위도

    longitude : float
        경도

    Returns
    -------
    str
        예:
        "전북특별자치도 전주시 덕진구 혁신동"
    """

    if latitude is None or longitude is None:
        raise ValueError("위도와 경도가 필요합니다.")

    try:
        latitude = float(latitude)
        longitude = float(longitude)

    except (TypeError, ValueError) as e:
        raise ValueError(
            "위도와 경도는 숫자여야 합니다."
        ) from e

    if not -90 <= latitude <= 90:
        raise ValueError(
            "올바른 위도 범위가 아닙니다."
        )

    if not -180 <= longitude <= 180:
        raise ValueError(
            "올바른 경도 범위가 아닙니다."
        )

    api_key = get_kakao_api_key()

    url = (
        "https://dapi.kakao.com/"
        "v2/local/geo/coord2regioncode.json"
    )

    headers = {
        "Authorization": f"KakaoAK {api_key}"
    }

    # Kakao API는
    # x = 경도(longitude)
    # y = 위도(latitude)
    params = {
        "x": longitude,
        "y": latitude,
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=5,
        )

        response.raise_for_status()

    except requests.Timeout as e:
        raise RuntimeError(
            "Kakao API 요청 시간이 초과되었습니다."
        ) from e

    except requests.RequestException as e:
        raise RuntimeError(
            f"Kakao API 요청에 실패했습니다: {e}"
        ) from e

    data = response.json()

    documents = data.get(
        "documents",
        [],
    )

    # 바다 등 행정주소를 얻을 수 없는 위치
    if not documents:
        raise ValueError(
            "선택한 위치의 행정주소를 찾을 수 없습니다."
        )

    # H = 행정동
    administrative_region = next(
        (
            document
            for document in documents
            if document.get("region_type") == "H"
        ),
        None,
    )

    # 행정동이 없다면 첫 번째 결과 사용
    if administrative_region is None:
        administrative_region = documents[0]

    address = administrative_region.get(
        "address_name"
    )

    if not address:
        raise ValueError(
            "선택한 위치의 주소 정보를 찾을 수 없습니다."
        )

    return address


# ============================================================
# 3. Kakao Map Component
# ============================================================

KAKAO_MAP_HTML = """
<div class="kakao-map-wrapper">
    <div id="kakao-map"></div>
    <div id="map-message"></div>
</div>
"""


KAKAO_MAP_CSS = """
.kakao-map-wrapper {
    width: 100%;
    font-family: var(--st-font);
}

#kakao-map {
    width: 100%;
    height: 430px;
    border-radius: 12px;
    overflow: hidden;
}

#map-message {
    display: none;
    margin-top: 10px;
    padding: 10px 12px;
    border-radius: 8px;
    background: rgba(128, 128, 128, 0.08);
    font-size: 14px;
}
"""


KAKAO_MAP_JS = """
export default function(component) {

    const {
        parentElement,
        data,
        setStateValue
    } = component;

    const mapContainer =
        parentElement.querySelector("#kakao-map");

    const message =
        parentElement.querySelector("#map-message");

    const javascriptKey =
        data.javascriptKey;


    // --------------------------------------------
    // 오류 메시지 표시 함수
    // --------------------------------------------

    function showErrorMessage(text) {

        message.style.display = "block";
        message.innerText = text;
    }


    if (!javascriptKey) {

        showErrorMessage(
            "Kakao JavaScript Key가 없습니다."
        );

        return;
    }


    function initializeMap() {

        const headquartersLat =
            data.headquartersLat;

        const headquartersLng =
            data.headquartersLng;

        const center =
            new kakao.maps.LatLng(
                headquartersLat,
                headquartersLng
            );


        // rerun 시 기존 내용 제거
        mapContainer.innerHTML = "";


        const map =
            new kakao.maps.Map(
                mapContainer,
                {
                    center: center,
                    level: 6
                }
            );


        // --------------------------------------------
        // LX 본사 Marker
        // --------------------------------------------

        const headquartersPosition =
            new kakao.maps.LatLng(
                headquartersLat,
                headquartersLng
            );


        const headquartersMarker =
            new kakao.maps.Marker({
                position: headquartersPosition,
                map: map
            });


        // --------------------------------------------
        // LX 본사 InfoWindow
        // --------------------------------------------

        const headquartersInfo =
            new kakao.maps.InfoWindow({
                content:
                    '<div style="' +
                    'padding:7px 10px;' +
                    'font-size:13px;' +
                    'white-space:nowrap;' +
                    '">' +
                    '<strong>' +
                    'LX 한국국토정보공사 본사' +
                    '</strong>' +
                    '</div>'
            });


        headquartersInfo.open(
            map,
            headquartersMarker
        );


        // --------------------------------------------
        // 사용자 선택 Marker
        // --------------------------------------------

        let selectedMarker = null;


        // 이전에 선택한 좌표가 존재하면 Marker 복원
        if (data.selected) {

            const previousPosition =
                new kakao.maps.LatLng(
                    data.selected.latitude,
                    data.selected.longitude
                );


            selectedMarker =
                new kakao.maps.Marker({
                    position: previousPosition,
                    map: map
                });
        }


        // --------------------------------------------
        // 지도 클릭 이벤트
        // --------------------------------------------

        kakao.maps.event.addListener(
            map,
            "click",
            function(mouseEvent) {

                const latLng =
                    mouseEvent.latLng;


                const latitude =
                    latLng.getLat();


                const longitude =
                    latLng.getLng();


                // 기존 선택 Marker 제거
                if (selectedMarker) {

                    selectedMarker.setMap(null);
                }


                // 새로운 선택 Marker 생성
                selectedMarker =
                    new kakao.maps.Marker({
                        position: latLng,
                        map: map
                    });


                /*
                좌표는 화면에 출력하지 않는다.

                다만 아래 setStateValue를 통해
                Python으로 좌표 자체는 계속 전달한다.
                */


                // Streamlit Python으로 좌표 전달
                setStateValue(
                    "selection",
                    {
                        latitude: latitude,
                        longitude: longitude
                    }
                );
            }
        );
    }


    // --------------------------------------------
    // Kakao Maps SDK Load
    // --------------------------------------------

    if (
        window.kakao
        && window.kakao.maps
    ) {

        kakao.maps.load(
            initializeMap
        );

        return;
    }


    const existingScript =
        document.querySelector(
            'script[data-lx-kakao-map="true"]'
        );


    if (existingScript) {

        existingScript.addEventListener(
            "load",
            function() {

                kakao.maps.load(
                    initializeMap
                );
            }
        );

        return;
    }


    const script =
        document.createElement("script");


    script.src =
        "https://dapi.kakao.com/v2/maps/sdk.js"
        + "?autoload=false"
        + "&appkey="
        + encodeURIComponent(javascriptKey);


    script.async = true;

    script.dataset.lxKakaoMap = "true";


    script.onload = function() {

        kakao.maps.load(
            initializeMap
        );
    };


    script.onerror = function() {

        showErrorMessage(
            "Kakao Map SDK를 불러오지 못했습니다. "
            + "API Key와 등록 도메인을 확인하세요."
        );
    };


    document.head.appendChild(
        script
    );
}
"""


_KAKAO_MAP_COMPONENT = st.components.v2.component(
    name="lx_kakao_map",
    html=KAKAO_MAP_HTML,
    css=KAKAO_MAP_CSS,
    js=KAKAO_MAP_JS,
)


# ============================================================
# 4. Kakao Map 출력
# ============================================================

def render_kakao_map():
    """
    Streamlit 화면에 Kakao Map을 출력하고,
    마지막으로 선택한 좌표를 반환한다.
    """

    javascript_key = (
        get_kakao_javascript_key()
    )

    component_key = (
        "lx_kakao_map_instance"
    )

    selection_key = (
        "kakao_selected_location"
    )


    # 이전에 선택한 좌표 복원
    saved_selection = (
        st.session_state.get(
            selection_key
        )
    )


    result = _KAKAO_MAP_COMPONENT(
        data={
            "javascriptKey": javascript_key,
            "headquartersLat": LX_HEADQUARTERS_LAT,
            "headquartersLng": LX_HEADQUARTERS_LNG,
            "selected": saved_selection,
        },
        default={
            "selection": saved_selection
        },
        key=component_key,
        on_selection_change=lambda: None,
    )


    # Component에서 새 좌표가 전달됐는지 확인
    new_selection = getattr(
        result,
        "selection",
        None,
    )


    # 새 좌표가 있으면 session_state에 저장
    if new_selection:

        st.session_state[
            selection_key
        ] = {
            "latitude": new_selection["latitude"],
            "longitude": new_selection["longitude"],
        }


    # 항상 마지막 선택 위치 반환
    return st.session_state.get(
        selection_key
    )