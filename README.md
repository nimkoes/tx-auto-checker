# TX Auto Checker

다양한 모니터링 작업을 자동화하고 문제 발생 시 슬랙으로 알림을 보내는 시스템입니다.

## 프로젝트 구조

```
├── monitoring/           # 모니터링 작업들
│   ├── dns/            # DNS 모니터링
│   │   ├── checker.py  # DNS 체크 로직
│   │   ├── config.json # DNS 설정
│   │   └── requirements.txt # DNS 의존성
│   └── [다른 모니터링]/  # 향후 추가될 모니터링
├── .github/workflows/   # GitHub Actions 워크플로우
│   ├── dns-monitor.yml # DNS 모니터링 워크플로우
│   └── [다른 워크플로우] # 향후 추가될 워크플로우
├── requirements.txt     # 공통 의존성
└── README.md          # 이 파일
```

## 네이밍 규칙

### 폴더 구조
- **대분류**: `monitoring/` - 모든 모니터링 작업의 상위 폴더
- **소분류**: `monitoring/dns/` - 각 모니터링 유형별 폴더

### 파일 네이밍
- **체커 파일**: `checker.py` - 각 모니터링의 메인 로직
- **설정 파일**: `config.json` - 각 모니터링의 설정
- **의존성 파일**: `requirements.txt` - 각 모니터링의 의존성
- **워크플로우 파일**: `{모니터링명}-monitor.yml` - GitHub Actions 워크플로우

### 워크플로우와 체커 연결
- 워크플로우 파일명: `dns-monitor.yml` → 실행할 파일: `monitoring/dns/checker.py`
- 워크플로우 파일명: `http-monitor.yml` → 실행할 파일: `monitoring/http/checker.py`

## 현재 구현된 모니터링

### DNS 모니터링

도메인의 A 레코드를 모니터링하고 문제가 발생하면 슬랙으로 알림을 보냅니다.

#### 기능
- 여러 도메인의 A 레코드를 동시 모니터링
- DNS 조회 실패 시 슬랙 알림
- 예상 IP와 다른 결과 시 슬랙 알림
- GitHub Actions를 통한 자동 스케줄링 (6시간마다)

#### 설정 방법

1. **슬랙 웹훅 설정**
   - 슬랙에서 Incoming Webhook을 생성합니다
   - GitHub Repository의 Settings > Secrets and variables > Actions에서 `SLACK_WEBHOOK_URL` 시크릿을 추가합니다

2. **모니터링할 도메인 설정**
   `monitoring/dns/config.json` 파일을 수정하여 모니터링할 도메인과 예상 IP를 설정합니다:

   ```json
   {
     "domains": [
       {
         "domain": "example.com",
         "expected_ip": "93.184.216.34"
       },
       {
         "domain": "google.com", 
         "expected_ip": "142.250.191.78"
       }
     ]
   }
   ```

3. **GitHub Actions 활성화**
   - Repository를 private으로 설정 (권장)
   - GitHub Actions가 자동으로 활성화됩니다
   - 6시간마다 자동으로 실행되며, 수동 실행도 가능합니다

#### 로컬 테스트

```bash
# 의존성 설치
pip install -r monitoring/dns/requirements.txt

# 환경변수 설정 (선택사항)
export SLACK_WEBHOOK_URL="your_webhook_url"

# DNS 체크 실행
python monitoring/dns/checker.py
```

#### 알림 메시지 형식

**DNS 조회 실패**
```
DNS 조회 실패
도메인: example.com
메시지: 도메인이 존재하지 않습니다: example.com
```

**DNS 결과 불일치**
```
DNS 결과 불일치
도메인: example.com
기대값: 93.184.216.34
결과값: 192.168.1.1
```

## 새로운 모니터링 추가 방법

1. **폴더 생성**: `monitoring/{모니터링명}/` 폴더 생성
2. **체커 파일 생성**: `monitoring/{모니터링명}/checker.py` 작성
3. **설정 파일 생성**: `monitoring/{모니터링명}/config.json` 작성
4. **의존성 파일 생성**: `monitoring/{모니터링명}/requirements.txt` 작성
5. **워크플로우 생성**: `.github/workflows/{모니터링명}-monitor.yml` 작성

### 워크플로우 템플릿

```yaml
name: {모니터링명} Monitor

on:
  schedule:
    - cron: '0 */6 * * *'  # 6시간마다
  workflow_dispatch:

jobs:
  {모니터링명}-check:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r monitoring/{모니터링명}/requirements.txt
        
    - name: Run {모니터링명} monitoring
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
      run: |
        python monitoring/{모니터링명}/checker.py
```

## 주의사항

- GitHub Actions 무료 플랜은 private repo에서 월 2,000분 제한이 있습니다
- 6시간마다 실행되므로 월 약 120분을 사용합니다
- 더 자주 실행하려면 유료 플랜을 고려하세요