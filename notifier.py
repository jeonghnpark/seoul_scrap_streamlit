import os
import asyncio
import logging
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv
import html

# 로깅 설정
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# .env 파일에서 환경 변수를 로드합니다.
# 이를 통해 텔레그램 봇 토큰이나 채팅 ID와 같은 민감한 정보들을 안전하게 관리할 수 있습니다.
load_dotenv()


class Notifier:
    def __init__(self):
        # .env 파일에서 텔레그램 봇 토큰과 메시지를 보낼 채팅 ID를 가져옵니다.
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

        logger.info(f"🔍 Notifier 초기화 시작")
        logger.debug(f"Token exists: {bool(self.token)}")
        logger.debug(f"Chat ID: {self.chat_id}")

        # 토큰이 설정되지 않았다면 명확한 에러를 발생시켜 초기 설정을 유도합니다.
        if not self.token:
            error_msg = "TELEGRAM_BOT_TOKEN is not set in .env file"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        # 채팅 ID가 설정되지 않았다면 명확한 에러를 발생시켜 초기 설정을 유도합니다.
        if not self.chat_id:
            error_msg = "TELEGRAM_CHAT_ID is not set in .env file"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)

        # 텔레그램 봇 객체를 생성합니다. 이 객체를 통해 텔레그램 API와 상호작용합니다.
        self.bot = Bot(token=self.token)
        logger.info(f"✓ Telegram Bot 객체 생성 완료")

    async def send_message(self, message):
        """
        지정된 `chat_id`로 텔레그램 메시지를 비동기적으로 전송합니다.
        메시지 전송 실패 시 `TelegramError`를 처리하여 프로그램의 안정성을 높입니다.
        """
        try:
            logger.debug(f"📤 메시지 전송 시도 - Chat ID: {self.chat_id}")
            logger.debug(f"Message content: {message[:100]}...")
            
            result = await self.bot.send_message(
                chat_id=self.chat_id, text=message, parse_mode="HTML"
            )
            
            logger.info(f"✓ 메시지 전송 성공 - Message ID: {result.message_id}")
            return True
            
        except TelegramError as e:
            logger.error(f"❌ 텔레그램 전송 실패: {type(e).__name__} - {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ 예기치 않은 오류: {type(e).__name__} - {str(e)}")
            return False

    def format_message(self, reservation):
        """
        주어진 예약 정보(딕셔너리)를 텔레그램 메시지에 적합하고 가독성 좋은 형식으로 포맷팅합니다.
        사용자에게 중요한 정보(제목, 장소, 접수 기간, 링크 등)를 명확하게 전달하는 데 중점을 둡니다.
        """
        url = reservation.get("url", "#")

        title = html.escape(reservation.get("svc_name", "제목 없음"))
        place = html.escape(reservation.get("place_name", "장소 미정"))
        category = html.escape(reservation.get("category", "기타"))
        state = html.escape(reservation.get("state", "상태 미정"))
        url = html.escape(
            reservation.get("url", "#")
        )

        rcpt_bgndt = html.escape(reservation.get("rcpt_bgndt", ""))
        rcpt_enddt = html.escape(reservation.get("rcpt_enddt", ""))

        message = (
            f"🏷️ {category} | {state}\n"
            f"📌 {title}\n"
            f"🔗 <a href = '{url}'>바로가기</a>"
        )
        return message


if __name__ == "__main__":
    async def test():
        try:
            notifier = Notifier()
            await notifier.send_message(
                "테스트 메시지입니다. 이 메시지가 텔레그램으로 전송됩니다."
            )
            print("Message sent successfully")
        except Exception as e:
            print(f"Setup error: {e}")

    asyncio.run(test())
