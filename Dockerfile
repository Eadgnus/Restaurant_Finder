# 공식 파이썬 3.13 이미지를 사용합니다.
FROM python:3.13

# Python의 표준 스트림이 버퍼링되지 않도록 환경 변수를 설정합니다.
ENV PYTHONUNBUFFERED=1

# 애플리케이션 파일들을 저장할 작업 디렉터리를 설정합니다.
WORKDIR /app

# Playwright 실행에 필요한 시스템 종속성을 설치합니다.
# 패키지 이름 오류를 수정했습니다.
RUN apt-get update && apt-get install -y \
    libgtk-4-1 \
    libgraphene-1.0-0 \
    libgstreamer-plugins-bad1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    libgstreamer1.0-0 \
    libgstreamer-gl1.0-0 \
    libenchant-2-2 \
    libsecret-1-0 \
    libmanette-0.2-0 \
    libgles2-mesa

# requirements.txt 파일을 복사하고 파이썬 라이브러리들을 설치합니다.
# --no-cache-dir 옵션은 빌드 속도를 높입니다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright가 사용할 브라우저 실행 파일들을 설치합니다.
# 이전에 문제가 되었던 시스템 라이브러리들도 함께 설치됩니다.
RUN playwright install --with-deps

# 애플리케이션의 나머지 파일들을 작업 디렉터리에 복사합니다.
COPY . .

# 컨테이너가 시작될 때 실행될 명령어를 정의합니다.
# Gunicorn을 사용하여 Flask 앱을 실행하고, Render가 제공하는 PORT 환경 변수를 사용합니다.
CMD gunicorn app:app --bind 0.0.0.0:$PORT
