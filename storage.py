import sqlite3
import os
from datetime import datetime

class Storage:
    def __init__(self, db_path='reservations.db'):
        # SQLite 데이터베이스 파일 경로를 설정합니다. 이 파일은 중복 알림을 방지하기 위해
        # 이미 텔레그램으로 전송된 예약 정보의 ID를 저장하는 데 사용됩니다.
        self.db_path = db_path
        # Storage 객체 초기화 시 데이터베이스 테이블이 존재하지 않으면 생성합니다.
        self.create_table()

    def get_connection(self):
        """
        SQLite 데이터베이스 연결 객체를 반환합니다.
        이 메서드는 데이터베이스 작업 시마다 호출되어 연결을 얻습니다.
        """
        return sqlite3.connect(self.db_path)

    def create_table(self):
        """
        'seen_reservations' 테이블을 생성합니다. 만약 테이블이 이미 존재한다면
        이 작업은 무시됩니다 (IF NOT EXISTS 절 사용). 이는 스크립트 재실행 시
        데이터 손실을 방지하고 안정성을 높입니다.
        
        - `svc_id`: 서비스 고유 ID. Primary Key로 설정되어 중복 저장을 자동으로 방지합니다.
        - `svc_name`: 서비스 제목을 저장합니다.
        - `created_at`: 해당 예약 정보가 데이터베이스에 추가된 일시를 기록합니다.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS seen_reservations (
                    svc_id TEXT PRIMARY KEY,
                    svc_name TEXT,
                    created_at DATETIME
                )
            ''')
            conn.commit()

    def is_seen(self, svc_id):
        """
        특정 서비스 ID(`svc_id`)가 이미 데이터베이스의 `seen_reservations` 테이블에
        저장되어 있는지 확인합니다. 이 함수는 새로운 예약인지 판단하는 핵심 로직입니다.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM seen_reservations WHERE svc_id = ?', (svc_id,))
            return cursor.fetchone() is not None

    def add_seen(self, svc_id, svc_name=None):
        """
        새로운 서비스 ID(`svc_id`)와 제목(`svc_name`)을 `seen_reservations` 테이블에 추가합니다.
        만약 동일한 `svc_id`가 이미 존재한다면 Primary Key 제약 조건 위반으로
        `sqlite3.IntegrityError`가 발생하며, 이는 중복 추가 시도를 방지합니다.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO seen_reservations (svc_id, svc_name, created_at) VALUES (?, ?, ?)',
                    (svc_id, svc_name, datetime.now())
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_sent_notifications(self, limit=50):
        """
        전송한 알림 목록을 최근 순으로 조회합니다.
        
        Args:
            limit (int): 조회할 최대 알림 수
            
        Returns:
            list: 알림 정보가 담긴 딕셔너리 리스트 (svc_id, svc_name, created_at)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT svc_id, svc_name, created_at 
                FROM seen_reservations 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            return [
                {
                    'svc_id': row[0],
                    'svc_name': row[1],
                    'created_at': row[2]
                }
                for row in rows
            ]
    
    def get_total_count(self):
        """
        전송한 알림의 총 개수를 반환합니다.
        
        Returns:
            int: 전송한 알림의 총 개수
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM seen_reservations')
            return cursor.fetchone()[0]
