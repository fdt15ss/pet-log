# Project 4

# 🐾 Project 4: AI Pet Care Agent (Pet Log)

## 1. 프로젝트 개요 (Overview)

- **프로젝트 명**: 반려동물의 행동과 건강 기록을 해석해 다음 행동까지 제안하는 AI 반려동물 관리 서비스, Pet Log
- **팀 구성**: 강현준, 김경표, 복만수, 임경빈
- **배경 및 필요성**:
    - **기록 중심 서비스의 한계**: 기존 반려동물 관리 앱은 예방접종, 진료, 사료량 등을 캘린더나 기록 형태로 누적하는 데 집중함
    - **기록 지속성 문제**: 보호자가 직접 입력해야 하는 구조로 인해 기록 누락, 기록 중단, 데이터 미활용 문제가 발생함
    - **맥락 기반 해석 부재**: 같은 행동이라도 반려동물의 상태, 최근 기록, 시간 흐름에 따라 원인이 달라질 수 있지만 기존 서비스는 누적 맥락을 충분히 반영하지 못함
    - **행동 제안 연결 부족**: 단순 저장을 넘어 이상 변화 감지, 원인 추정, 행동 개선 가이드로 이어지는 AI Agent 기반 관리 흐름이 필요함

## 2. 데이터 전략 (Data Strategy)

반려동물의 일상 기록, 프로필, 일정, 알림, 커뮤니티, 외부 API 데이터를 결합해 보호자가 입력한 자연어를 구조화하고, 누적 맥락을 분석할 수 있는 데이터 기반을 구축했습니다.

### 2.1 데이터 확보 및 증강

- **반려동물 프로필 DB**: 이름, 나이, 품종, 성별, 체중, 질환 정보, 복용 약, 생활 정보 등 개인화 분석에 필요한 기본 정보를 관리
- **케어 기록 DB**: 급여, 배변, 산책/활동, 행동, 병원, 약, 접종, 체중 등 일상 기록을 SQLite 기반 영구 저장소에 저장
- **음성 및 이미지 입력 데이터**: Whisper 기반 STT, 이미지 업로드 API, 사진 기반 기록 이해 provider 구조를 통해 텍스트 외 입력 채널 확장
- **일정 및 알림 데이터**: 예방접종, 약 복용, 건강검진, 사료 변경 시기, 기록 누락, 위험 신호, 행동 변화, 일정 리마인더를 알림 후보로 생성
- **외부 연동 데이터**: Google Places API로 위치 기반 동물병원 추천을 제공하고, Naver Shopping API와 LLM을 결합해 케어 맥락 기반 상품 추천 이유를 생성
- **케어 지식 데이터**: 관리자가 승인한 외부 케어 가이드 URL을 RAG 지식 출처로 삼고, 향후 chunking, embedding, similarity search 구조로 확장 가능하게 설계

### 2.2 전처리 파이프라인

- **자연어 기록 구조화**: 자유 텍스트를 원문, 요약, 추천 분류, 측정값, 신뢰도, 확인 필요 여부로 변환
- **카테고리 정규화**: 식사, 산책/활동, 배변/소변, 병원/약/접종, 행동 등 MVP 기준 분류 체계로 기록을 정리
- **음성 텍스트 보정**: 음성 파일은 Whisper로 변환하고, 변환된 문장을 AI가 `corrected_text`로 정리해 기록 입력 품질을 높임
- **컨텍스트 조립**: 반려동물 프로필, 최근 기록, 일정, 알림 후보를 `CareContextBuilder`에서 통합해 agent 분석 입력으로 사용
- **패턴 및 누락 분석**: 최근 기록을 기준으로 반복 행동, 기록 누락, 이상 징후, 일정 기반 리마인더를 rule-based policy와 agent pipeline으로 감지
- **RAG 확장 설계**: 케어 질문 답변을 위해 승인 URL → 텍스트 추출 → chunking → embedding → SQLite vector storage → 검색 → 근거 기반 답변 흐름을 설계

## 3. AI 모델 아키텍처 (AI Model Architecture)

Pet Log는 자연어 구조화, 누적 맥락 분석, 위험 신호 탐지, 제안 생성, 알림 계획, 대화형 응답을 결합한 AI Agent 기반 아키텍처를 채택했습니다.

### 3.1 기록 분석 및 케어 Agent Track

- **RecordStructuringAgent**: 보호자의 자유 텍스트 입력을 카테고리, 제목, 상세 내용, 상태, 신뢰도, 확인 필요 여부로 구조화
- **ContextAnalysisAgent**: 최근 기록 패턴, 누락 기록, 상태 변화, UI 이동 경로를 분석
- **RiskDetectionAgent**: 통증, 호흡 이상, 혈변, 반복 구토, 지속적인 식욕 저하 등 건강/안전 위험 신호를 탐지
- **SuggestionAgent**: 기록과 분석 결과를 기반으로 행동 개선 가이드와 건강 관리 제안을 생성
- **ReminderAgent**: 접종, 약 복용, 사료 변경, 건강검진 같은 케어 일정 기반 리마인더를 계획
- **NotificationAgent**: `missing_record`, `risk`, `behavior_change`, `schedule` 4가지 알림 후보를 생성하고 중복 제거 정책을 적용

### 3.2 대화, 검색 및 외부 연동 Track

- **PetPersonaAgent**: 반려동물 이름, 사진, 성격, 최근 기록을 반영해 보호자가 현재 키우는 펫과 대화하는 듯한 응답을 제공
- **CareAnswerProvider**: 보호자의 케어 질문에 반려동물 컨텍스트와 케어 지식 검색 결과를 함께 활용하는 RAG 기반 답변 구조를 지원
- **ShoppingAgent**: 케어 맥락을 바탕으로 Naver Shopping 상품 후보를 검색하고 LLM으로 추천 이유를 생성
- **HospitalRecommendationAgent**: Google Places API를 활용해 현재 위치, 반경, 응급 여부, 영업 상태를 반영한 동물병원 추천을 제공
- **PhotoRecordUnderstandingAgent**: 이미지에서 케어 기록을 추출하는 멀티모달 확장 지점으로 설계
- **LangGraph + LangChain 기반 실행**: LangGraph는 agent pipeline orchestration에, LangChain은 model, tool, middleware adapter에 사용
- **LLM 운용 방식**: Gemma(Ollama)와 GPT를 primary/fallback으로 전환할 수 있는 하이브리드 구조를 지원하며, 작업별 `OPENAI_*_MODEL` 환경변수로 모델을 분리

## 4. 시스템 구현 (Implementation)

- **UI/UX**: Next.js App Router, React, TypeScript, Tailwind CSS 기반의 모바일 우선 웹 MVP 구현
- **백엔드**: Python 3.12, FastAPI, LangGraph, LangChain, SQLite 기반 AI agent backend 구현
- **주요 프로세스**:
    - 자연어, 음성, 사진 기반 기록 입력
    - AI 구조화 미리보기 후 저장 여부 확인
    - 기록 타임라인과 카테고리 필터를 통한 일상 기록 조회
    - 식사, 행동, 체중, 활동량 변화 분석 및 이상 징후 표시
    - 누락 기록, 위험 신호, 행동 변화, 일정 기반 알림 생성
    - 홈 요약, AI 제안, 펫 대화, 케어 질문 응답 제공
    - 위치 기반 동물병원 추천 및 케어 맥락 기반 쇼핑 추천 제공
- **구현된 주요 화면**:
    - `/` 홈
    - `/record` 기록
    - `/analysis` 분석
    - `/timeline` 기록 타임라인
    - `/suggestions` AI 제안
    - `/profile` 반려동물 프로필
    - `/notifications` 알림
    - `/schedule` 일정
    - `/community` 커뮤니티
    - `/hospital` 병원 연계
    - `/shopping` 쇼핑
    - `/shared-care` 공동 관리
    - `/settings` 설정

## 5. 기대 효과 및 향후 계획 (Expected Effects & Future)

- **기대 효과**:
    - **관리 지속성 향상**: 자연어와 음성 입력으로 기록 부담을 줄이고, 기록 누락 알림으로 꾸준한 관리를 유도
    - **상태 이해 향상**: 단일 기록이 아니라 누적 기록의 시간 흐름을 기반으로 식사, 배변, 행동, 체중, 활동량 변화를 해석
    - **행동 의사결정 지원**: 이상 징후, 반복 행동, 일정 리마인더, 병원 상담 권장 문구를 통해 보호자가 다음 행동을 판단하도록 지원
    - **감성적 재방문 동기 강화**: 반려동물 페르소나 기반 대화 인터페이스로 기록 관리 피로도를 낮추고 서비스 재사용률을 높임
    - **서비스 확장성 확보**: 병원, 커머스, 커뮤니티, RAG 케어 지식, 멀티모달 이미지 기록으로 확장 가능한 구조 마련
- **향후 계획**:
    - **RAG 고도화**: 승인된 케어 URL 수집, SSRF 보호, chunking, embedding persistence, similarity search, citation prompt 구현
    - **멀티모달 기록 강화**: 사진 기반 사료량, 자세, 배변 상태, 행동 기록 이해 기능 고도화
    - **병원 연계 확장**: 누적 기록과 증상 요약을 병원 제출용 리포트로 정리하고 예약/상담 흐름과 연결
    - **커머스 개인화**: 건강 상태와 기록 맥락 기반 사료, 용품, 보험, 제휴 상품 추천 정교화
    - **공동 관리 및 목표 기능**: 가족/보호자 초대, 역할 설정, 산책·다이어트·문제행동 개선 미션 등 관리 참여 기능 확대

## 6. 프로젝트 스케줄 (Project Schedule)

- **전체 일정**: 2026. 04. 22 ~ 2026. 05. 18
- **기획 기준일**: 2026. 04. 28 (`기획.md`, `펫로그_20260428` 자료 기준)
- **주요 마일스톤**:
    - 서비스 문제 정의 및 핵심 차별점 도출
    - 모바일 우선 MVP 범위 정의
    - Next.js 기반 프론트엔드 화면 구현
    - FastAPI 기반 백엔드 및 SQLite 저장소 연동
    - 자연어 기록 구조화 및 AI agent pipeline 구현
    - 알림, 일정, 동물병원, 쇼핑 추천 API 확장
    - 프론트/백엔드 통합 테스트 및 QA 검증

## 7. 프로젝트 결과 및 회고 (Results & Retrospection)

### 7.1 정량적 성과

- **API 구현 범위 확대**: 사용자, 반려동물, 기록, 일정, 파일, 음성, 병원 추천, 커뮤니티, 알림, 쇼핑 추천 API를 백엔드와 연동
- **알림 정책 구현**: `missing_record`, `risk`, `behavior_change`, `schedule` 4가지 알림 후보 생성 구조와 DB 기반 읽음 처리를 구현
- **기록 입력 파이프라인 완성**: 자연어 입력 → 구조화 → 분석 → DB 저장 흐름을 FastAPI route와 연결
- **검증 체계 확보**: 프론트엔드 lint, typecheck, build, 단위 테스트, Playwright 기반 모바일 QA와 백엔드 unittest 검증 명령을 정리
- **배포 준비**: Next.js standalone 및 FastAPI Azure App Service 배포 스크립트와 운영 문서를 마련

### 7.2 정성적 성과

- **기록 앱에서 케어 Agent로 전환**: 단순 저장이 아니라 해석, 제안, 알림, 대화로 이어지는 제품 흐름을 구현
- **설명 가능한 AI 응답 지향**: 사용자에게 보이는 기록과 프로필 데이터를 근거로 알림과 제안을 생성하도록 설계
- **안전 경계 명확화**: 질병 확정 진단, 처방, 치료 결정을 비목표로 두고 위험 신호에는 병원 상담 권장 문구를 유지
- **확장 가능한 계층 구조**: `presentation -> application pipelines -> application agents -> interfaces -> infrastructure/tools/agent_runtime` 흐름으로 외부 SDK와 비즈니스 로직을 분리
- **하네스 엔지니어링 적용**: Product Planner, UX Designer, AI Agent Designer, Orchestrator, QA Reviewer 흐름으로 MVP 범위와 검증 기준을 정리

### 7.3 회고

- **데이터 정규화의 중요성**: 자연어, 음성, 사진처럼 입력 형태가 다양한 데이터를 동일한 기록 계약으로 구조화해야 분석과 제안이 안정적으로 이어짐
- **AI 안전성의 중요성**: 반려동물 건강 맥락에서는 편리한 답변보다 진단성 표현 제한, 위험 신호 안내, 병원 상담 연결이 우선되어야 함
- **누적 맥락의 가치**: 단발성 질문보다 최근 기록, 일정, 프로필, 반복 패턴을 함께 볼 때 보호자에게 실질적인 행동 가이드를 제공할 수 있음
- **확장 가능성 확인**: 현재 agent pipeline과 provider 경계를 기반으로 RAG, 이미지 기록 이해, 병원 리포트, 커머스 추천, 공동 관리 기능을 단계적으로 확장할 수 있음
