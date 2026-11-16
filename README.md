# 🌿 Film Green Book

영화 미술팀 프리프로덕션 소품·재료 수급(쿠팡·네이버쇼핑·다이소·당근·대여·재사용)의
탄소 절감량을 계산하고, 물·식량으로 환산해 보여주는 Streamlit 앱입니다.

## 실행
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 배포 (Streamlit Community Cloud + GitHub)
1. 이 폴더 전체를 GitHub 저장소에 올립니다.
2. https://share.streamlit.io 에서 **Create app** → 저장소 선택 → Main file: `app.py`
3. Deploy

## 계수 수정
`factors.py`의 재질·구입방법 계수는 예시용 기본값입니다. 검증된 LCI/물발자국 데이터로 교체해 사용하세요.
