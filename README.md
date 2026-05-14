# 서울시 예약 알림 봇 (Streamlit 버전)

서울시 공공서비스 예약 정보를 자동으로 수집하고 텔레그램으로 알림을 전송하는 Streamlit 웹 애플리케이션입니다.

## 🚀 주요 기능

- **직관적인 웹 인터페이스**: Streamlit 기반의 깔끔하고 사용하기 쉬운 UI
- **1회 전송 기능**: 버튼 클릭으로 즉시 예약 정보 확인 및 알림 전송
- **실시간 상태 모니터링**: 실행 결과 및 통계 실시간 표시
- **설정 가능한 파라미터**: 가져올 공고 수와 알림 전송 수 조정 가능
- **텔레그램 연동**: 새로운 예약 정보를 텔레그램으로 자동 전송
- **중복 방지**: SQLite 데이터베이스를 사용한 중복 알림 방지
- **Streamlit Cloud 배포 가능**: 클라우드 환경에서 쉽게 배포 가능

## 📋 사전 요구사항

- Python 3.8 이상
- 텔레그램 봇 토큰
- 텔레그램 채팅 ID
- 서울시 공공데이터 API 키

## 🛠 설치 및 설정

### 1. 저장소 클론

```bash
git clone <repository-url>
cd seoul_scrap_streamlit
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env_sample` 파일을 `.env`로 복사하고 필요한 정보를 입력하세요:

```bash
cp .env_sample .env
```

`.env` 파일 내용:

```env
# 텔레그램 봇 설정
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# 서울시 API 설정
SEOUL_API_KEY=your_seoul_api_key_here
```

### 4. 텔레그램 봇 설정 방법

1. **봇 생성**: [@BotFather](https://t.me/BotFather)에게 `/newbot` 명령어 전송
2. **봇 토큰 획득**: 봇 생성 후 받은 토큰을 `.env` 파일에 입력
3. **채팅 ID 확인**: 
   - 봇과 대화 시작
   - `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` 접속
   - 응답에서 `chat.id` 값을 확인하여 `.env` 파일에 입력

### 5. 서울시 API 키 발급

1. [서울 열린데이터광장](https://data.seoul.go.kr/) 회원가입
2. 마이페이지 > 인증키 신청
3. 발급받은 인증키를 `.env` 파일에 입력

## 🚀 실행 방법

### 로컬 실행

```bash
streamlit run streamlit_app.py
```

실행 후 브라우저에서 `http://localhost:8501`로 자동으로 접속됩니다.

### Streamlit Cloud 배포

1. [Streamlit Cloud](https://streamlit.io/cloud)에 로그인
2. GitHub 저장소 연결
3. 배포 설정:
   - Main file path: `streamlit_app.py`
   - Python version: 3.8+
4. Secrets 설정 (Settings > Secrets):

```toml
TELEGRAM_BOT_TOKEN = "your_bot_token_here"
TELEGRAM_CHAT_ID = "your_chat_id_here"
SEOUL_API_KEY = "your_seoul_api_key_here"
```

5. Deploy 버튼 클릭

## 🖥 사용 방법

1. **설정 조정**: 사이드바에서 가져올 공고 수와 알림 전송 수를 조정
2. **실행**: "1회 전송 실행" 버튼 클릭
3. **결과 확인**: 실행 결과 및 통계 확인

## 📁 프로젝트 구조

```
seoul_scrap_streamlit/
├── streamlit_app.py   # Streamlit 웹 애플리케이션
├── scraper.py         # 서울시 API 스크래퍼
├── storage.py         # SQLite 데이터베이스 관리
├── notifier.py        # 텔레그램 알림 전송
├── requirements.txt   # Python 의존성
├── .env_sample        # 환경 변수 샘플
├── .gitignore        # Git 무시 파일
└── README.md         # 프로젝트 문서
```

## ⚙️ 주요 설정

### API 파라미터

- **fetch_limit**: API에서 가져올 최대 공고 수 (기본값: 500)
- **notify_limit**: 텔레그램으로 전송할 최대 알림 수 (기본값: 30)

### 알림 우선순위

1. **높은 우선순위**: 오늘/내일 접수 시작하는 공고
2. **중간 우선순위**: 미래 접수 예정 공고
3. **낮은 우선순위**: 이미 접수가 시작된 공고

### 서비스 유형

다음 서비스 유형의 예약 정보를 수집합니다:

- 체육시설 예약
- 시설대관 예약
- 교육강좌 예약 (공예/취미, 자연/과학)
- 문화행사 예약 (문화행사, 전시/관람)
- 진료복지 예약

## 🔧 문제 해결

### 일반적인 오류

1. **텔레그램 연결 실패**
   - `.env` 파일의 봇 토큰과 채팅 ID 확인
   - 봇이 활성화되어 있는지 확인
   - Streamlit Cloud의 경우 Secrets 설정 확인

2. **서울시 API 오류**
   - 네트워크 연결 확인
   - API 키가 올바르게 설정되었는지 확인
   - API 사용량 제한 확인

3. **데이터베이스 오류**
   - `reservations.db` 파일 권한 확인
   - 파일이 손상된 경우 삭제 후 재실행

### 로그 확인

애플리케이션 실행 시 터미널에서 상세한 로그를 확인할 수 있습니다.

## 📝 주의사항

- 이 봇은 서울시 공공데이터를 사용하므로, 과도한 API 호출을 피하고 적절한 간격으로 사용해주세요.
- 중복 알림 방지를 위해 SQLite 데이터베이스(`reservations.db`)를 사용합니다.
- 이미 전송된 알림은 데이터베이스에 기록되어 다시 전송되지 않습니다.

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여하기

버그 리포트나 기능 제안은 GitHub Issues를 통해 제출해주세요.

---

**Made with ❤️ for Seoul Residents**
