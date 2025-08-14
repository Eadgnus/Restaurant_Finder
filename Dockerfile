# Playwright가 공식적으로 지원하는 Python 이미지를 사용합니다.
# requirements.txt의 playwright 버전과 동일한 이미지 버전을 사용하도록 변경합니다.
FROM mcr.microsoft.com/playwright/python:v1.54.0-jammy

# Python의 표준 스트림이 버퍼링되지 않도록 환경 변수를 설정합니다.
ENV PYTHONUNBUFFERED=1

# 애플리케이션 파일들을 저장할 작업 디렉터리를 설정합니다.
WORKDIR /app

# requirements.txt 파일을 복사하고 파이썬 라이브러리들을 설치합니다.
# Playwright는 이미 설치되어 있으므로, 다른 종속성만 설치합니다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션의 나머지 파일들을 작업 디렉터리에 복사합니다.
COPY . .

# 컨테이너가 시작될 때 실행될 명령어를 정의합니다.
# Gunicorn을 사용하여 Flask 앱을 실행하고, Render가 제공하는 PORT 환경 변수를 사용합니다.
CMD gunicorn app:app --bind 0.0.0.0:$PORT
