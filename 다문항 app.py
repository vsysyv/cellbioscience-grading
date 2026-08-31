import streamlit as st
from google import genai
from PIL import Image

st.title("📝 루브릭(채점 기준표) 기반 AI 자동 채점 툴")
api_key = st.sidebar.text_input("Google Gemini API Key", type="password")

if api_key:
    client = genai.Client(api_key=api_key)

    st.subheader("1. 문항 및 루브릭(채점 기준표) 설정")
    
    if "questions_count" not in st.session_state:
        st.session_state.questions_count = 2

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ 문항 추가"):
            st.session_state.questions_count += 1
    with col2:
        if st.button("➖ 문항 삭제") and st.session_state.questions_count > 1:
            st.session_state.questions_count -= 1

    default_data = [
        {
            "q": "추운 지방에 사는 이누이트들은 탄수화물보다 지방을 더 많이 섭취한다고 한다. 그 까닭을 에너지 사용 측면에서 서술해 보자.",
            "a": "탄수화물과 단백질은 1 g당 4 kcal, 지방은 1 g당 9 kcal의 에너지를 생산한다. 추운 곳에서 체온을 유지하기 위해서는 체내 에너지를 많이 생산해야 하므로 에너지 생산량이 높은 지방을 더 많이 섭취해야 한다.",
            "r": """- [4점] 지방이 1g당 9kcal, 탄수화물/단백질이 1g당 4kcal의 에너지를 냄을 정확히 제시함.
- [3점] 체온 유지를 위해 체내 에너지를 많이 생산해야 함을 언급함.
- [3점] 에너지 생산량이 상대적으로 더 높은 지방을 선택해야 하는 인과관계를 바르게 서술함.
※ 감점 감안 사항: 숫자를 잘못 적거나 일부 핵심 단어가 누락된 경우 항목당 1~2점 감점."""
        },
        {
            "q": "인슐린 단백질 모형의 1차 구조, 2차 구조, 3차 구조는 각각 어떤 모습인지 펩타이드 결합, 수소결합, 입체구조를 포함하여 서술하시오.",
            "a": "모형의 1차 구조는 아미노산이 펩타이드결합에 의해 일렬로 연결된 사슬의 형태이다. 2차 구조는 사슬의 수소결합에 의해 구조가 만들어진다.. 3차 구조는 입체 구조를 하고 있다.",
            "r": """- [3점] 1차 구조: 아미노산이 펩타이드 결합으로 일렬로 연결된 사슬 형태임을 언급함.
- [3점] 2차 구조: 수소 결합에 의해 구조를 형성함을 언급함.
- [3점] 3차 구조: 입체 구조를 이루고 있음을 바르게 서술함.
- [1점] 전체적인 과학적 용어 표현 및 서술의 완성도
※ 감점 감안 사항: 주요 결합 종류나 구조적 특징 설명이 미비한 경우 항목당 1점씩 감점."""
        }
    ]

    questions_data = []
    
    for i in range(st.session_state.questions_count):
        st.markdown(f"#### 📌 [문항 {i+1}]")
        
        default_q = default_data[i]["q"] if i < len(default_data) else ""
        default_a = default_data[i]["a"] if i < len(default_data) else ""
        default_r = default_data[i]["r"] if i < len(default_data) else ""

        q_text = st.text_area(f"문항 {i+1} 문제 설명", key=f"q_{i}", value=default_q)
        a_text = st.text_area(f"문항 {i+1} 모범 답안", key=f"a_{i}", value=default_a)
        rubric_text = st.text_area(f"문항 {i+1} 세부 채점 기준표 (루브릭)", key=f"r_{i}", value=default_r)
        score = st.number_input(f"문항 {i+1} 만점 배점", min_value=1, value=10, key=f"s_{i}")
        
        questions_data.append({"no": i+1, "question": q_text, "answer": a_text, "rubric": rubric_text, "score": score})
        st.divider()

    st.subheader("2. 수기 답안지 사진 업로드")
    uploaded_file = st.file_uploader("학생의 답안지 사진을 올려주세요", type=["jpg", "jpeg", "png"])
    
    uploaded_image = None
    if uploaded_file is not None:
        uploaded_image = Image.open(uploaded_file)
        st.image(uploaded_image, caption="업로드된 수기 답안지", width=450)

    if st.button("🚀 루브릭 기반 일괄 채점 실행"):
        if uploaded_image is None:
            st.warning("수기 답안지 사진을 먼저 올려주세요!")
        else:
            prompt_rubric = ""
            for q in questions_data:
                prompt_rubric += f"""
                [문항 {q['no']}]
                - 문제: {q['question']}
                - 모범답안: {q['answer']}
                - 세부 채점 기준표(루브릭):
                {q['rubric']}
                - 만점: {q['score']}점
                """

            optimized_image = uploaded_image.copy()
            optimized_image.thumbnail((1024, 1024))

            # 루브릭 각 항목을 누락 없이 구체적으로 적도록 프롬프트 강화
            prompt = f"""
            당신은 공정한 채점관입니다. 
            제공된 이미지의 손글씨 답안을 판독한 뒤, 입력된 **[세부 채점 기준표(루브릭)]**의 각 항목별로 충족 여부와 점수를 명확히 평가해 주세요.

            {prompt_rubric}

            응답은 반드시 아래 양식을 지켜 작성해 주세요. (루브릭 항목별 평가란에 공백이나 빈 부호만 남기지 말고, 루브릭에 제시된 세부 조건별로 판독 결과를 바탕으로 구체적인 평가 내용을 작성하세요):

            ---
            ### 📌 [문항 번호] 채점 결과
            - **인식된 학생 답안**: [이미지에서 판독한 학생 답안 전체]
            - **루브릭 항목별 평가**:
              * (루브릭 조건 1 내용): [충족 여부, 판독 근거, 부여 점수]
              * (루브릭 조건 2 내용): [충족 여부, 판독 근거, 부여 점수]
              * (루브릭 조건 3 내용): [충족 여부, 판독 근거, 부여 점수]
            - **최종 획득 점수**: [획득 점수] / [만점]점
            - **감점 사유**: [감점된 이유를 간결하게 정리]
            - **피드백**: [학생에게 줄 핵심 조언 1~2문장]
            ---
            - **총점**: [획득 점수 합] / [총 배점 합]점
            """

            with st.spinner("AI가 루브릭 세부 항목별로 정밀 검토 중입니다..."):
                try:
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=[prompt, optimized_image],
                        config={
                            "temperature": 0.0,
                        }
                    )
                    st.success("채점 완료!")
                    st.markdown("### 📊 최종 채점 결과")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"채점 도중 오류가 발생했습니다: {e}")
else:
    st.warning("왼쪽 사이드바에 Google Gemini API Key를 입력해주세요.")
