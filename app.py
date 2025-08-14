# run_app.py
# import subprocess
# import os

# print("--- Playwright 브라우저 및 시스템 종속성 설치 시작 ---")
# try:
#     # 'playwright install --with-deps' 명령어를 실행하여 브라우저와 시스템 종속성을 모두 설치합니다.
#     subprocess.run(["playwright", "install", "--with-deps"], check=True)
#     print("--- Playwright 설치 완료 ---")
#
#     # app.py 파일을 실행합니다.
#     print("--- app.py 실행 시작 ---")
#     os.system("python app.py")
#
# except subprocess.CalledProcessError as e:
#     print(f"Playwright 설치 중 오류 발생: {e}")
# except FileNotFoundError:
#     print("오류: 'playwright' 명령어를 찾을 수 없습니다. 'pip install playwright'를 먼저 실행했는지 확인하세요.")
# except Exception as e:
#     print(f"오류 발생: {e}")

import sys
import webbrowser
import requests
from requests.exceptions import RequestException
import random
import re
import math
from bs4 import BeautifulSoup
import json
import os
from dotenv import load_dotenv  # dotenv 라이브러리 추가
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright

# 이 코드를 실행하기 전에 다음 명령어를 터미널에 입력하여 필요한 라이브러리를 설치해주세요:
# pip install Flask requests beautifulsoup4 playwright Flask-Cors python-dotenv

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

# ====================================================================
# 필수: 환경 변수에서 카카오 REST API 키를 불러옵니다.
# ====================================================================
API_KEY = os.getenv('KAKAO_API_KEY')
if not API_KEY:
    raise ValueError("API 키가 환경 변수 'KAKAO_API_KEY'에 설정되지 않았습니다.")

HEADERS_API = {"Authorization": f"KakaoAK {API_KEY}"}

app = Flask(__name__)
CORS(app)  # CORS 허용 설정 추가


# ----------------------
# 함수: 두 지점 간 거리 계산 (하버사인 공식)
# ----------------------
def calculate_distance(lat1, lon1, lat2, lon2):
    """
    두 위도/경도 좌표 사이의 거리를 미터 단위로 계산합니다 (하버사인 공식).
    """
    R = 6371000  # 지구 반지름 (미터)

    lat1_rad = math.radians(float(lat1))
    lon1_rad = math.radians(float(lon1))
    lat2_rad = math.radians(float(lat2))
    lon2_rad = math.radians(float(lon2))

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return int(distance)


# ----------------------
# 함수: Playwright를 사용하여 상세 정보 추출
# ----------------------
def get_restaurant_details_with_playwright(page, url):
    """
    Playwright를 사용하여 주어진 상세 페이지 URL에서 평점과 메뉴 정보를 추출합니다.
    """
    rating, menus = "정보 없음", []
    try:
        page.goto(url, wait_until='domcontentloaded', timeout=1000)

        # 페이지에 동적 콘텐츠가 로드될 때까지 기다립니다.
        page.wait_for_selector('div.star_info, ul.list_menu, div.wrap_menu', timeout=5000)

        soup = BeautifulSoup(page.content(), 'html.parser')

        # 평점 정보 추출
        rating_tag = soup.find('span', class_='num_star')
        if rating_tag:
            try:
                rating_text = rating_tag.text
                rating_value = rating_text.replace("별점", "").strip()
                rating = float(rating_value)
            except (ValueError, AttributeError):
                rating = "정보 없음"

        # 메뉴 정보 추출:
        menu_info_divs = soup.find_all('div', class_='line_info')
        for menu_div in menu_info_divs:
            name_tag = menu_div.select_one('strong.tit_item')
            if name_tag:
                menu_name = name_tag.get_text(strip=True)
                price_div = menu_div.find_next_sibling('div', class_='line_info')
                menu_price = "가격 정보 없음"
                if price_div:
                    price_tag = price_div.select_one('p.desc_item')
                    if price_tag:
                        menu_price = price_tag.get_text(strip=True)
                menus.append({'name': menu_name, 'price': menu_price})

        # 'div.wrap_menu' 내에 있는 텍스트 기반 메뉴 정보 추출
        if not menus:
            menu_items = soup.select('div.wrap_menu li.list_menu_item')
            for item in menu_items:
                menu_data = {}
                name_tag = item.select_one('.loss_word')
                price_tag = item.select_one('.price_menu')
                if name_tag:
                    menu_data['name'] = name_tag.get_text(strip=True)
                if price_tag:
                    menu_data['price'] = price_tag.get_text(strip=True)
                if menu_data:
                    menus.append(menu_data)
    except Exception as e:
        print(f"스크래핑 중 오류 발생: {e}")
        pass
    return rating, menus


# ----------------------
# 웹 애플리케이션 라우팅
# ----------------------
@app.route('/')
def index():
    """메인 페이지를 렌더링합니다."""
    return render_template('index.html')


@app.route('/api/search_address', methods=['POST'])
def search_address():
    """
    주소 검색 API 엔드포인트
    """
    data = request.get_json()
    address = data.get('address')
    if not address:
        return jsonify({"success": False, "message": "주소를 입력해주세요."}), 400

    print(f"주소 검색 요청: {address}")
    try:
        url = f"https://dapi.kakao.com/v2/local/search/address.json?query={address}"
        response = requests.get(url, headers=HEADERS_API, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data['documents']:
            doc = data['documents'][0]
            lat = doc['y']
            lng = doc['x']
            print(f"주소 '{address}' 검색 성공: lat={lat}, lng={lng}")
            return jsonify({
                "success": True,
                "message": f"'{address}'의 위치가 설정되었습니다.",
                "lat": lat,
                "lng": lng
            }), 200
        else:
            print(f"주소 '{address}' 검색 결과 없음")
            return jsonify({"success": False, "message": "주소를 찾을 수 없습니다."}), 404

    except RequestException as e:
        print(f"주소 검색 중 오류 발생: {e}")
        return jsonify({"success": False, "message": f"주소 검색 중 오류 발생: {e}"}), 500


@app.route('/api/search_restaurants', methods=['POST'])
def search_restaurants():
    """
    맛집 검색 및 상세 정보 스크래핑 API 엔드포인트
    """
    data = request.get_json()
    lat = data.get('lat')
    lng = data.get('lng')
    food_query = data.get('food_query', '').strip()

    print(f"맛집 검색 요청: lat={lat}, lng={lng}, query='{food_query}'")
    if not lat or not lng:
        return jsonify({"success": False, "message": "위치 정보가 필요합니다."}), 400

    categories = ["한식", "중식", "일식", "양식", "분식", "패스트푸드", "카페"]
    query = food_query if food_query else random.choice(categories)
    random_flag = not food_query

    url = f"https://dapi.kakao.com/v2/local/search/keyword.json?query={query}&y={lat}&x={lng}&radius=500&size=15"
    try:
        response = requests.get(url, headers=HEADERS_API, timeout=5)
        response.raise_for_status()
        kakao_data = response.json()

        if 'documents' not in kakao_data or not kakao_data['documents']:
            print(f"카카오 API 검색 결과 없음: query='{query}'")
            return jsonify({"success": False, "message": "검색 결과가 없습니다."}), 404

        restaurants_with_details = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            count = 0
            docs = kakao_data['documents']
            for restaurant in docs:
                try:
                    count += 1
                    rating, menus = get_restaurant_details_with_playwright(page, restaurant['place_url'])
                    restaurant['rating'] = rating
                    restaurant['menus'] = menus
                    restaurant['distance'] = calculate_distance(lat, lng, restaurant['y'], restaurant['x'])
                    restaurants_with_details.append(restaurant)
                    if count == 3 and random_flag:
                        break
                except Exception as e:
                    print(f"스크래핑 오류 발생: {restaurant.get('place_name')} - {e}")
                    continue

            browser.close()

        restaurants_with_details.sort(
            key=lambda x: x.get('rating') if isinstance(x.get('rating'), (int, float)) else -1, reverse=True
        )
        print(f"최종 검색 결과 {len(restaurants_with_details)}개 반환")
        return jsonify({"success": True, "restaurants": restaurants_with_details}), 200

    except RequestException as e:
        print(f"API 요청 중 오류 발생: {e}")
        return jsonify({"success": False, "message": f"API 요청 중 오류 발생: {e}"}), 500
    except Exception as e:
        print(f"스크래핑 또는 기타 오류 발생: {e}")
        return jsonify({"success": False, "message": f"스크래핑 또는 기타 오류 발생: {e}"}), 500


if __name__ == '__main__':
    # Render 환경 변수에서 포트 번호를 가져오거나, 없다면 기본값 5000을 사용합니다.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
