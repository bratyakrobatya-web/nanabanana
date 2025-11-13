import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image
import json

# Настройка страницы
st.set_page_config(
    page_title="Cat Face Swap 🐱",
    page_icon="🐱",
    layout="wide"
)

# Заголовок приложения
st.title("🐱 Cat Face Swap - Замена мордочек котов")
st.markdown("Загрузите базовое изображение и фото с мордочкой кота для замены")

# Получение токена из secrets
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "")

if not OPENROUTER_API_KEY:
    st.error("⚠️ OpenRouter API ключ не найден! Добавьте OPENROUTER_API_KEY в Streamlit secrets.")
    st.stop()


def encode_image_to_base64(image):
    """Конвертирует PIL изображение в base64 строку"""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


def call_openrouter_vision(base_image_b64, cat_face_b64, custom_prompt, model="anthropic/claude-3.5-sonnet:beta"):
    """
    Вызов OpenRouter API с vision моделью для анализа изображений
    """
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://streamlit.io",
        "X-Title": "Cat Face Swap App"
    }

    # Формируем промпт с четкими указаниями для каждого изображения
    user_message = f"""I need your help with a face swap task. I'm providing you with TWO images:

IMAGE 1 (Base/Target image): This is the BASE image where I want to place a cat face.

IMAGE 2 (Source image): This is the photo with the CAT FACE that should be extracted and placed on the base image.

Task: {custom_prompt}

Please analyze BOTH images and provide:
1. Description of the first (base) image - where should the cat face be placed
2. Description of the second (source) image - where is the cat face located
3. Step-by-step instructions for swapping the cat face from image 2 onto image 1
4. What adjustments need to be made (size, angle, lighting, positioning)

Make sure to reference both images in your analysis."""

    payload = {
        "model": model,  # Vision модель
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Here is IMAGE 1 (BASE IMAGE - where we want to place the cat face):"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base_image_b64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "Here is IMAGE 2 (SOURCE IMAGE - the cat face to extract and use):"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{cat_face_b64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": user_message
                    }
                ]
            }
        ],
        "max_tokens": 2000
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()

        # Выводим информацию о модели
        model_used = result.get('model', 'unknown')
        st.info(f"🤖 Использована модель: {model_used}")

        return result['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка при вызове OpenRouter API: {str(e)}")
        if hasattr(e.response, 'text'):
            st.error(f"Детали ошибки: {e.response.text}")
        return None


def call_openrouter_image_generation(prompt, base_image_b64=None):
    """
    Вызов OpenRouter API для генерации изображения
    """
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://streamlit.io",
        "X-Title": "Cat Face Swap App"
    }

    # Используем модель с поддержкой генерации изображений
    payload = {
        "model": "openai/gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 4096
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка при генерации изображения: {str(e)}")
        if hasattr(e.response, 'text'):
            st.error(f"Детали ошибки: {e.response.text}")
        return None


# Боковая панель с настройками
with st.sidebar:
    st.header("⚙️ Настройки")

    st.subheader("1️⃣ Базовое изображение")
    st.markdown("Загрузите изображение, на котором будет производиться замена")
    base_image_file = st.file_uploader(
        "Выберите базовое изображение",
        type=['png', 'jpg', 'jpeg'],
        key="base_image"
    )

    st.subheader("2️⃣ Фото с мордочкой кота")
    st.markdown("Загрузите фото кота, мордочку которого нужно использовать")
    cat_face_file = st.file_uploader(
        "Выберите фото кота",
        type=['png', 'jpg', 'jpeg'],
        key="cat_face"
    )

    st.subheader("3️⃣ Выбор AI модели")
    model_choice = st.selectbox(
        "Выберите модель для анализа",
        options=[
            "anthropic/claude-3.5-sonnet:beta",
            "anthropic/claude-3-5-sonnet-20241022",
            "google/gemini-pro-1.5",
            "openai/gpt-4-vision-preview",
            "google/gemini-flash-1.5"
        ],
        index=0,
        help="Разные модели могут давать разные результаты. Claude обычно лучше для детального анализа."
    )

    st.subheader("4️⃣ Промпт для обработки")
    custom_prompt = st.text_area(
        "Опишите как должна быть размещена мордочка кота",
        value="Аккуратно разместить мордочку кота из второго изображения на первом изображении, сохраняя естественный вид и правильные пропорции.",
        height=100
    )

    process_button = st.button("🚀 Обработать изображения", type="primary", use_container_width=True)


# Основная область
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📷 Базовое изображение")
    if base_image_file:
        base_image = Image.open(BytesIO(base_image_file.getvalue()))
        st.image(base_image, use_column_width=True)
    else:
        st.info("Загрузите базовое изображение")

with col2:
    st.subheader("🐱 Мордочка кота")
    if cat_face_file:
        cat_face_image = Image.open(BytesIO(cat_face_file.getvalue()))
        st.image(cat_face_image, use_column_width=True)
    else:
        st.info("Загрузите фото кота")

with col3:
    st.subheader("✨ Результат")
    if 'result_placeholder' not in st.session_state:
        st.session_state.result_placeholder = None

    if st.session_state.result_placeholder:
        st.info(st.session_state.result_placeholder)
    else:
        st.info("Результат появится здесь после обработки")


# Обработка изображений
if process_button:
    if not base_image_file or not cat_face_file:
        st.error("⚠️ Пожалуйста, загрузите оба изображения!")
    else:
        with st.spinner("🔄 Обработка изображений через OpenRouter API..."):
            # Конвертируем изображения в base64
            base_image = Image.open(BytesIO(base_image_file.getvalue()))
            cat_face_image = Image.open(BytesIO(cat_face_file.getvalue()))

            # Изменяем размер для оптимизации
            max_size = (1024, 1024)
            base_image.thumbnail(max_size, Image.Resampling.LANCZOS)
            cat_face_image.thumbnail(max_size, Image.Resampling.LANCZOS)

            base_image_b64 = encode_image_to_base64(base_image)
            cat_face_b64 = encode_image_to_base64(cat_face_image)

            # Вызов OpenRouter Vision API для анализа
            st.info(f"📊 Анализ изображений с помощью AI (модель: {model_choice})...")
            analysis_result = call_openrouter_vision(base_image_b64, cat_face_b64, custom_prompt, model=model_choice)

            if analysis_result:
                st.success("✅ Анализ завершен!")

                with st.expander("📋 Результат анализа от AI", expanded=True):
                    st.markdown(analysis_result)

                st.session_state.result_placeholder = analysis_result

                st.info("""
                📝 **Примечание**:
                Автоматическая замена лиц требует специализированных моделей для image editing/inpainting.
                OpenRouter предоставляет анализ изображений через vision модели.

                Для полной автоматизации замены лиц можно:
                1. Использовать специализированные API (Replicate, RunwayML)
                2. Внедрить локальные модели (InsightFace, Face Swap)
                3. Использовать Stable Diffusion с ControlNet для inpainting
                """)
            else:
                st.error("❌ Не удалось обработать изображения")


# Футер
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>🐱 Cat Face Swap | Powered by OpenRouter API</p>
    <p><small>Загрузите ваши изображения и получите AI-анализ для замены мордочек котов</small></p>
</div>
""", unsafe_allow_html=True)
