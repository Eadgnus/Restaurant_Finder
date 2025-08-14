# run_app.py
import subprocess
import os

print("--- Playwright 브라우저 및 시스템 종속성 설치 시작 ---")
try:
    # 'playwright install --with-deps' 명령어를 실행하여 브라우저와 시스템 종속성을 모두 설치합니다.
    subprocess.run(["playwright", "install", "--with-deps"], check=True)
    print("--- Playwright 설치 완료 ---")

    # app.py 파일을 실행합니다.
    print("--- app.py 실행 시작 ---")
    os.system("python app.py")

except subprocess.CalledProcessError as e:
    print(f"Playwright 설치 중 오류 발생: {e}")
except FileNotFoundError:
    print("오류: 'playwright' 명령어를 찾을 수 없습니다. 'pip install playwright'를 먼저 실행했는지 확인하세요.")
except Exception as e:
    print(f"오류 발생: {e}")
