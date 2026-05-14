import asyncio
import logging
import streamlit as st
from datetime import datetime
from scraper import Scraper
from storage import Storage
from notifier import Notifier

# 로깅 설정
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Streamlit 페이지 설정
st.set_page_config(
    page_title="서울시 예약 알림 봇",
    page_icon="🔔",
    layout="wide",
    initial_sidebar_state="expanded"
)


class ReservationBot:
    """서울시 예약 알림 봇의 핵심 로직을 담은 클래스"""
    
    def __init__(self):
        self.scraper = Scraper()
        self.storage = Storage()
        self.notifier = Notifier()
    
    async def send_notifications(self, fetch_limit=500, notify_limit=30):
        """
        예약 정보를 가져와서 텔레그램으로 알림을 전송하는 메인 로직
        
        Args:
            fetch_limit (int): API에서 가져올 최대 공고 수
            notify_limit (int): 텔레그램으로 알림을 보낼 최대 공고 수
            
        Returns:
            dict: 실행 결과 정보
        """
        try:
            logger.info("Starting notification job...")
            
            # 1. 서울시 API에서 예약 정보 가져오기
            reservations = self.scraper.fetch_new_reservations(fetch_limit=fetch_limit)
            logger.info(f"Fetched {len(reservations)} reservations.")
            
            if not reservations:
                return {
                    'success': True,
                    'message': '가져온 예약 정보가 없습니다.',
                    'total_fetched': 0,
                    'new_notifications': 0
                }
            
            # 2. 예약 정보 처리 및 알림 전송
            new_count = await self._process_reservations(reservations, notify_limit)
            
            result = {
                'success': True,
                'message': f'성공적으로 완료되었습니다. 새로운 알림 {new_count}개를 전송했습니다.',
                'total_fetched': len(reservations),
                'new_notifications': new_count
            }
            
            logger.info(f"Job completed. Sent {new_count} new notifications.")
            return result
            
        except Exception as e:
            error_msg = f"알림 전송 중 오류가 발생했습니다: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'total_fetched': 0,
                'new_notifications': 0
            }
    
    async def _process_reservations(self, reservations, notify_limit):
        """예약 정보를 처리하고 텔레그램 알림을 전송"""
        new_count = 0
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 접수 시작일이 있는 데이터만 필터링
        valid_reservations = [r for r in reservations if r.get('rcpt_bgndt')]
        logger.info(f"유효한 예약: {len(valid_reservations)}개")
        
        # 데이터를 과거/미래로 분류
        future_reservations = []
        past_reservations = []
        
        for r in valid_reservations:
            rcpt_date = r.get('rcpt_bgndt', '')[:10]
            if rcpt_date >= today:
                future_reservations.append(r)
            else:
                past_reservations.append(r)
        
        logger.info(f"과거 예약: {len(past_reservations)}개, 미래 예약: {len(future_reservations)}개")
        
        # 정렬: 과거는 오름차순, 미래는 내림차순
        past_reservations.sort(key=lambda x: x.get('rcpt_bgndt', ''))
        future_reservations.sort(key=lambda x: x.get('rcpt_bgndt', ''), reverse=True)
        
        # 최종 처리 순서: [과거] + [미래]
        sorted_reservations = past_reservations + future_reservations
        
        # notify_limit 개수만큼만 추출
        if len(sorted_reservations) > notify_limit:
            sorted_reservations = sorted_reservations[-notify_limit:]
        
        logger.info(f"처리할 예약: {len(sorted_reservations)}개")
        
        # 각 예약 정보에 대해 알림 전송
        for idx, reservation in enumerate(sorted_reservations, 1):
            svc_id = reservation["svc_id"]
            svc_name = reservation.get("svc_name", "알 수 없음")
            
            logger.debug(f"[{idx}/{len(sorted_reservations)}] 처리 중: {svc_name} (ID: {svc_id})")
            
            if not self.storage.is_seen(svc_id):
                logger.info(f"새 예약 발견: {svc_name}")
                
                try:
                    message = self.notifier.format_message(reservation)
                    logger.debug(f"메시지 포맷팅 완료")
                    
                    if await self.notifier.send_message(message):
                        self.storage.add_seen(svc_id, svc_name)
                        new_count += 1
                        logger.info(f"✓ [{new_count}] {svc_name} 알림 전송 성공")
                        await asyncio.sleep(1)
                    else:
                        logger.error(f"✗ {svc_name} 알림 전송 실패")
                except Exception as e:
                    logger.error(f"메시지 처리 중 오류 - {svc_name}: {type(e).__name__} - {str(e)}")
            else:
                logger.debug(f"이미 본 예약: {svc_name}")
        
        return new_count


def main():
    """Streamlit 메인 애플리케이션"""
    
    # 헤더
    st.title("🔔 서울시 예약 알림 봇")
    st.markdown("---")
    
    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 설정")
        
        fetch_limit = st.slider(
            "가져올 공고 수",
            min_value=1,
            max_value=1000,
            value=500,
            step=50,
            help="API에서 가져올 최대 공고 수입니다."
        )
        
        notify_limit = st.slider(
            "알림 전송 수",
            min_value=1,
            max_value=100,
            value=30,
            step=5,
            help="텔레그램으로 알림을 보낼 최대 공고 수입니다."
        )
        
        st.markdown("---")
        st.info(
            "**알림 우선순위**\n\n"
            "1. 높음: 오늘/내일 접수 시작\n"
            "2. 중간: 미래 접수 예정\n"
            "3. 낮음: 이미 접수 시작된 공고"
        )
    
    # 메인 영역
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 실행 정보")
        
        if st.button("🚀 1회 전송 실행", type="primary", use_container_width=True):
            try:
                with st.spinner("예약 정보를 가져오는 중..."):
                    # 봇 인스턴스 생성 및 실행
                    bot = ReservationBot()
                    
                    # 비동기 함수 실행
                    result = asyncio.run(
                        bot.send_notifications(
                            fetch_limit=fetch_limit,
                            notify_limit=notify_limit
                        )
                    )
                    
                    # 결과 표시
                    if result['success']:
                        st.success(result['message'])
                        
                        # 통계 표시
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("가져온 공고", result['total_fetched'])
                        with col_b:
                            st.metric("새로운 알림", result['new_notifications'])
                        with col_c:
                            st.metric("중복 제외", result['total_fetched'] - result['new_notifications'])
                    else:
                        st.error(result['message'])
                        
            except ValueError as e:
                st.error(f"⚠️ 설정 오류: {str(e)}")
                st.info(
                    "`.env` 파일을 확인하세요:\n"
                    "- TELEGRAM_BOT_TOKEN\n"
                    "- TELEGRAM_CHAT_ID\n"
                    "- SEOUL_API_KEY"
                )
            except Exception as e:
                st.error(f"❌ 오류가 발생했습니다: {str(e)}")
    
    with col2:
        st.subheader("ℹ️ 서버 상태")
        status_placeholder = st.empty()
        
        with status_placeholder.container():
            st.success("🟢 실행 중")
            st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 하단 정보
    st.markdown("---")
    
    # 전송한 알림 목록
    with st.expander("📋 전송한 알림 목록", expanded=False):
        try:
            storage = Storage()
            total_count = storage.get_total_count()
            
            st.caption(f"총 {total_count}개의 알림을 전송했습니다.")
            
            if total_count > 0:
                # 표시할 개수 선택
                display_limit = st.select_slider(
                    "표시할 개수",
                    options=[10, 20, 30, 50, 100],
                    value=20
                )
                
                notifications = storage.get_sent_notifications(limit=display_limit)
                
                # 테이블로 표시
                st.markdown("### 최근 전송 알림")
                for idx, notif in enumerate(notifications, 1):
                    created_time = datetime.strptime(notif['created_at'], '%Y-%m-%d %H:%M:%S.%f') if '.' in notif['created_at'] else datetime.strptime(notif['created_at'], '%Y-%m-%d %H:%M:%S')
                    formatted_time = created_time.strftime('%Y-%m-%d %H:%M')
                    
                    with st.container():
                        col_num, col_title, col_time = st.columns([0.5, 4, 1.5])
                        with col_num:
                            st.caption(f"{idx}")
                        with col_title:
                            st.write(notif['svc_name'] if notif['svc_name'] else "제목 없음")
                        with col_time:
                            st.caption(formatted_time)
            else:
                st.info("아직 전송한 알림이 없습니다.")
                
        except Exception as e:
            st.error(f"알림 목록을 불러오는 중 오류가 발생했습니다: {str(e)}")
    
    with st.expander("📖 사용 방법"):
        st.markdown("""
        ### 사용 방법
        
        1. **설정 조정**: 사이드바에서 가져올 공고 수와 알림 전송 수를 조정하세요.
        2. **실행**: "1회 전송 실행" 버튼을 클릭하세요.
        3. **결과 확인**: 실행 결과 및 통계를 확인하세요.
        
        ### 환경 설정
        
        `.env` 파일에 다음 환경 변수를 설정해야 합니다:
        
        ```
        TELEGRAM_BOT_TOKEN=your_bot_token_here
        TELEGRAM_CHAT_ID=your_chat_id_here
        SEOUL_API_KEY=your_seoul_api_key_here
        ```
        
        ### 주의사항
        
        - 중복 알림 방지를 위해 SQLite 데이터베이스를 사용합니다.
        - 이미 전송된 알림은 다시 전송되지 않습니다.
        - 과도한 API 호출을 피하기 위해 적절한 간격으로 사용하세요.
        """)


if __name__ == "__main__":
    main()
