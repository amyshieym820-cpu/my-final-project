import pandas as pd
import streamlit as st

from factors import BASELINE_METHOD, DEFAULTS, MATERIALS, METHODS, PRESETS

st.set_page_config(page_title="Film Green Book", page_icon="🌿", layout="wide")

COLS = ["소품명", "재질", "수량", "개당 무게(kg)", "구입방법"]
DEFAULT_METHOD = list(METHODS.keys())[2]  # 당근

# ---------------- state ----------------
if "items" not in st.session_state:
    st.session_state["items"] = pd.DataFrame(columns=COLS)


def add_item(name, qty, method):
    mat, weight = PRESETS[name]
    row = pd.DataFrame([[name, mat, qty, weight, method]], columns=COLS)
    st.session_state["items"] = pd.concat([st.session_state["items"], row], ignore_index=True)


def load_example():
    ex = [
        ["의자 (목재)", "🪑 목재 가구·소품", 6, 5.0, "🥕 당근 (중고)"],
        ["커튼", "🧵 섬유·패브릭·의류", 4, 1.5, "🔁 소품 대여 (렌탈)"],
        ["그릇·접시·컵", "🍽️ 유리·도자기", 20, 0.4, "🥕 당근 (중고)"],
        ["스탠드·조명", "💡 조명·전구", 5, 2.0, "🏪 다이소 (오프라인 신품)"],
        ["합판 (1장)", "🏗️ 합판·MDF·폼보드", 10, 12.0, "♻️ 폐자재·업사이클"],
        ["소파 (패브릭)", "🧵 섬유·패브릭·의류", 1, 30.0, "🛒 쿠팡·네이버쇼핑 (온라인 신품)"],
    ]
    st.session_state["items"] = pd.DataFrame(ex, columns=COLS)


# ---------------- sidebar ----------------
with st.sidebar:
    st.header("⚙️ 환산 기준")
    water_pp = st.number_input("1인 하루 식수량 (L)", 0.5, 10.0, DEFAULTS["water_per_person_day_L"], 0.5)
    meal_co2 = st.number_input("한 끼 식사의 탄소발자국 (kgCO2e)", 0.1, 10.0, DEFAULTS["meal_co2_kg"], 0.1)
    meals_day = st.number_input("하루 식사 횟수", 1, 5, DEFAULTS["meals_per_day"])
    st.caption("환산 기준은 팀 상황에 맞게 바꿀 수 있어요.")
    st.divider()
    st.caption("기준(비교 대상): " + BASELINE_METHOD)

# ---------------- header ----------------
st.title("🌿 Film Green Book")
st.write("영화 미술팀 프리프로덕션 소품·재료 수급의 탄소발자국을 계산하고, 줄인 만큼을 물과 식량으로 환산해 보세요.")
project = st.text_input("🎬 작품명 / 프로젝트", placeholder="예: 단편영화 〈제목〉 미술팀")

# ---------------- input ----------------
st.subheader("1. 소품 목록")
c1, c2, c3, c4 = st.columns([3, 1.2, 3, 1.2])
preset = c1.selectbox("자주 쓰는 소품", list(PRESETS.keys()))
qty = c2.number_input("수량", 1, 1000, 1)
method = c3.selectbox("구입 방법", list(METHODS.keys()), index=2)
c4.write("")
c4.write("")
if c4.button("➕ 추가", use_container_width=True):
    add_item(preset, qty, method)

b1, b2 = st.columns([1, 6])
if b1.button("예시 불러오기"):
    load_example()
if b2.button("목록 비우기"):
    st.session_state["items"] = pd.DataFrame(columns=COLS)

st.caption("표에서 직접 수정하거나, 맨 아래 빈 줄에 새 소품을 입력할 수도 있어요. 행을 선택하고 Delete 키로 삭제합니다.")
edited = st.data_editor(
    st.session_state["items"],
    num_rows="dynamic",
    use_container_width=True,
    key="editor",
    column_config={
        "소품명": st.column_config.TextColumn("소품명"),
        "재질": st.column_config.SelectboxColumn("재질", options=list(MATERIALS.keys()), required=True),
        "수량": st.column_config.NumberColumn("수량", min_value=0, step=1),
        "개당 무게(kg)": st.column_config.NumberColumn("개당 무게(kg)", min_value=0.0, step=0.1),
        "구입방법": st.column_config.SelectboxColumn("구입방법", options=list(METHODS.keys()), required=True),
    },
)
st.session_state["items"] = edited.reset_index(drop=True)


# ---------------- calculation ----------------
def calculate(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d = d[d["재질"].isin(MATERIALS) & d["구입방법"].isin(METHODS)]
    d["수량"] = pd.to_numeric(d["수량"], errors="coerce").fillna(0)
    d["개당 무게(kg)"] = pd.to_numeric(d["개당 무게(kg)"], errors="coerce").fillna(0)
    d["총무게(kg)"] = d["수량"] * d["개당 무게(kg)"]

    co2 = d["재질"].map(lambda x: MATERIALS[x]["co2"])
    water = d["재질"].map(lambda x: MATERIALS[x]["water"])
    share = d["구입방법"].map(lambda x: METHODS[x]["prod_share"])
    trans = d["구입방법"].map(lambda x: METHODS[x]["transport"])
    base_trans = METHODS[BASELINE_METHOD]["transport"]

    d["기준 탄소(kg)"] = d["총무게(kg)"] * (co2 + base_trans)
    d["선택 탄소(kg)"] = d["총무게(kg)"] * (co2 * share + trans)
    d["절감 탄소(kg)"] = d["기준 탄소(kg)"] - d["선택 탄소(kg)"]
    d["절감 물(L)"] = d["총무게(kg)"] * water * (1 - share)
    return d


result = calculate(st.session_state["items"])

# ---------------- results ----------------
st.subheader("2. 우리 팀이 줄인 탄소")
if result.empty or result["총무게(kg)"].sum() == 0:
    st.info("소품을 추가하면 결과가 나타나요. '예시 불러오기'로 먼저 체험해 보세요.")
    st.stop()

base_total = result["기준 탄소(kg)"].sum()
chosen_total = result["선택 탄소(kg)"].sum()
saved_co2 = result["절감 탄소(kg)"].sum()
saved_water = result["절감 물(L)"].sum()
pct = saved_co2 / base_total * 100 if base_total else 0

m1, m2, m3 = st.columns(3)
m1.metric("전부 온라인 신품으로 샀다면", f"{base_total:,.0f} kgCO₂e")
m2.metric("우리가 선택한 방법", f"{chosen_total:,.0f} kgCO₂e")
m3.metric("절감량", f"{saved_co2:,.0f} kgCO₂e", f"-{pct:.0f}%", delta_color="inverse")

st.subheader("3. 이만큼이면…")
meals = saved_co2 / meal_co2
water_days = saved_water / water_pp
e1, e2 = st.columns(2)
with e1:
    st.markdown("#### 💧 물")
    st.metric("절감한 물발자국", f"{saved_water:,.0f} L")
    st.write(f"**{water_days:,.0f}명**이 하루 마실 물, 또는 **{water_days / 365:,.1f}명**이 1년간 마실 물")
with e2:
    st.markdown("#### 🍚 식량")
    st.metric("절감한 탄소 = 식사 탄소발자국", f"{meals:,.0f} 끼")
    st.write(f"하루 {meals_day}끼 기준 **{meals / meals_day:,.0f}명**의 하루 식사와 같은 탄소량")

st.caption("※ 줄인 자원을 '환산'한 값이에요. 실제 기부·배분량이 아니라 규모를 체감하기 위한 비교 지표입니다.")

st.subheader("4. 구입 방법별 절감량")
by_method = result.groupby("구입방법")[["절감 탄소(kg)"]].sum()
st.bar_chart(by_method)

st.subheader("5. 소품별 상세")
show = result[["소품명", "재질", "수량", "구입방법", "기준 탄소(kg)", "선택 탄소(kg)", "절감 탄소(kg)", "절감 물(L)"]]
st.dataframe(show.round(1), use_container_width=True, hide_index=True)

csv = show.round(2).to_csv(index=False).encode("utf-8-sig")
st.download_button("📥 그린북 CSV 내려받기", csv, file_name=f"film_green_book_{project or 'project'}.csv", mime="text/csv")

with st.expander("📐 계산 방법과 한계"):
    st.markdown(
        """
- **탄소** = 총무게(kg) × (재질별 생산배출 × 구입방법별 생산 비율 + 구입방법별 배송·이동 배출)
- **기준** = 같은 소품을 쿠팡·네이버쇼핑에서 새로 구입했을 때
- **절감 물** = 총무게 × 재질별 물발자국 × (1 − 구입방법별 생산 비율)
- 중고·대여·재사용은 '새로 만들 필요가 없었다'는 점을 생산 비율을 낮춰 반영했어요.
- 모든 계수는 `factors.py`의 **예시용 기본값**입니다. 공식 보고서에 쓰기 전 검증된 데이터로 교체하세요.
- 실제 무게·이동거리·대여 횟수에 따라 결과는 달라질 수 있어요.
        """
    )

st.divider()
st.caption("Film Green Book • 영화 미술팀을 위한 친환경 소품 수급 계산기")
