#!/usr/bin/env python3
"""
DNS 모니터링 시스템
도메인의 A 레코드를 확인하고 예상값과 다르면 슬랙으로 알림을 보냅니다.
"""

import json
import os
import sys
import dns.resolver
import requests
from typing import Dict, List, Optional, Tuple


class DNSChecker:
    def __init__(self, config_file: str = None):
        """DNS 체커 초기화"""
        if config_file is None:
            # 현재 파일의 디렉토리에 있는 config.json 사용
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_file = os.path.join(current_dir, "config.json")
        
        self.config_file = config_file
        self.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        
        if not self.slack_webhook_url:
            print("경고: SLACK_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")
        
        self.load_config()
    
    def load_config(self) -> None:
        """설정 파일 로드"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print(f"설정 파일 로드 완료: {len(self.config['domains'])}개 도메인")
        except FileNotFoundError:
            print(f"오류: 설정 파일 {self.config_file}을 찾을 수 없습니다.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"오류: 설정 파일 JSON 파싱 실패: {e}")
            sys.exit(1)
    
    def check_dns(self, domain: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        도메인의 A 레코드를 확인합니다.
        
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: 
            (성공여부, IP주소 또는 에러메시지, 에러타입)
        """
        try:
            print(f"DNS 조회 중: {domain}")
            answers = dns.resolver.resolve(domain, 'A')
            ip_addresses = [str(answer) for answer in answers]
            print(f"DNS 조회 성공: {domain} -> {ip_addresses}")
            return True, ip_addresses[0], None
        except dns.resolver.NXDOMAIN:
            error_msg = f"도메인이 존재하지 않습니다: {domain}"
            print(f"DNS 조회 실패: {error_msg}")
            return False, error_msg, "NXDOMAIN"
        except dns.resolver.NoAnswer:
            error_msg = f"A 레코드가 없습니다: {domain}"
            print(f"DNS 조회 실패: {error_msg}")
            return False, error_msg, "NoAnswer"
        except dns.resolver.Timeout:
            error_msg = f"DNS 조회 시간 초과: {domain}"
            print(f"DNS 조회 실패: {error_msg}")
            return False, error_msg, "Timeout"
        except Exception as e:
            error_msg = f"DNS 조회 중 예상치 못한 오류: {domain} - {str(e)}"
            print(f"DNS 조회 실패: {error_msg}")
            return False, error_msg, "Unknown"
    
    def send_slack_notification(self, message: str) -> bool:
        """슬랙으로 알림을 보냅니다."""
        if not self.slack_webhook_url:
            print("슬랙 웹훅 URL이 설정되지 않아 알림을 보낼 수 없습니다.")
            return False
        
        payload = {
            "text": message
        }
        
        try:
            response = requests.post(self.slack_webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                print("슬랙 알림 전송 성공")
                return True
            else:
                print(f"슬랙 알림 전송 실패: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"슬랙 알림 전송 중 오류: {e}")
            return False
    
    def check_all_domains(self) -> None:
        """모든 도메인을 확인하고 문제가 있으면 알림을 보냅니다."""
        print("=== DNS 모니터링 시작 ===")
        
        for domain_config in self.config['domains']:
            domain = domain_config['domain']
            expected_ip = domain_config['expected_ip']
            
            print(f"\n도메인 확인 중: {domain}")
            print(f"예상 IP: {expected_ip}")
            
            success, result, error_type = self.check_dns(domain)
            
            if not success:
                # DNS 조회 실패
                message = f"DNS 조회 실패\n도메인: {domain}\n메시지: {result}"
                print(f"알림 전송: {message}")
                self.send_slack_notification(message)
            elif result != expected_ip:
                # DNS 결과 불일치
                message = f"DNS 결과 불일치\n도메인: {domain}\n기대값: {expected_ip}\n결과값: {result}"
                print(f"알림 전송: {message}")
                self.send_slack_notification(message)
            else:
                print(f"✅ {domain} DNS 정상 동작")
        
        print("\n=== DNS 모니터링 완료 ===")


def main():
    """메인 함수"""
    checker = DNSChecker()
    checker.check_all_domains()


if __name__ == "__main__":
    main() 