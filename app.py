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
st.markdown("Загрузите базовое изображение и фото с мордочкой кота. Gemini 2.0 Flash автоматически создаст результат!")

# Получение токена из secrets
GOOGLE_AI_STUDIO_KEY = st.secrets.get("GOOGLE_AI_STUDIO_KEY", "")

if not GOOGLE_AI_STUDIO_KEY:
    st.error("⚠️ Google AI Studio API ключ не найден! Добавьте GOOGLE_AI_STUDIO_KEY в Streamlit secrets.")
    st.info("Получите ключ на: https://aistudio.google.com/app/apikey")
    st.stop()


def encode_image_to_base64(image):
    """Конвертирует PIL изображение в base64 строку"""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


def generate_face_swap_with_gemini(base_image_b64, cat_face_b64, custom_prompt):
    """
    Отправляет два изображения в Gemini 2.0 Flash для генерации результата
    """
    # Используем модель с поддержкой генерации изображений
    model = "gemini-2.0-flash-exp"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GOOGLE_AI_STUDIO_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    # Промпт для генерации изображения
    generation_prompt = f"""You are an expert image editor. I'm providing you with TWO images:

IMAGE 1 (Base image): The background/target image where the cat face should be placed.
IMAGE 2 (Cat face source): The image containing the cat face that needs to be extracted and placed onto Image 1.

Task: {custom_prompt}

IMPORTANT: Generate a NEW IMAGE as output where you have seamlessly placed the cat face from Image 2 onto Image 1. The result should look natural with proper:
- Positioning and scale
- Color matching and lighting
- Smooth blending at edges
- Maintaining the quality of both images

Please generate the final composite image."""

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "IMAGE 1 (Base/Background):"
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": base_image_b64
                        }
                    },
                    {
                        "text": "IMAGE 2 (Cat face to use):"
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": cat_face_b64
                        }
                    },
                    {
                        "text": generation_prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 8192,
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()

        # Проверяем есть ли сгенерированное изображение в ответе
        if 'candidates' in result and len(result['candidates']) > 0:
            candidate = result['candidates'][0]

            # Ищем изображение в частях ответа
            if 'content' in candidate and 'parts' in candidate['content']:
                for part in candidate['content']['parts']:
                    # Проверяем есть ли inline_data с изображением
                    if 'inline_data' in part:
                        image_data = part['inline_data'].get('data')
                        if image_data:
                            # Декодируем base64 в изображение
                            image_bytes = base64.b64decode(image_data)
                            return Image.open(BytesIO(image_bytes))

                    # Если есть текстовый ответ, сохраняем его
                    if 'text' in part:
                        st.info(f"Ответ Gemini: {part['text'][:500]}")

        st.error("Gemini не вернул изображение в ответе. Возможно модель не поддерживает генерацию изображений или нужен другой промпт.")
        st.json(result)
        return None

    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка при вызове Gemini API: {str(e)}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            st.error(f"Детали: {e.response.text}")
        return None


# Боковая панель с настройками
with st.sidebar:
    st.header("⚙️ Настройки")

    st.subheader("1️⃣ Базовое изображение")
    st.markdown("Изображение-фон, куда будет помещена мордочка")
    base_image_file = st.file_uploader(
        "Выберите базовое изображение",
        type=['png', 'jpg', 'jpeg'],
        key="base_image"
    )

    st.subheader("2️⃣ Мордочка кота")
    st.markdown("Фото с мордочкой кота для замены")
    cat_face_file = st.file_uploader(
        "Выберите фото кота",
        type=['png', 'jpg', 'jpeg'],
        key="cat_face"
    )

    st.subheader("3️⃣ Инструкция для AI")
    custom_prompt = st.text_area(
        "Опишите что должен сделать Gemini",
        value="Аккуратно извлеките мордочку кота из второго изображения и разместите её на первом изображении в естественной позиции. Подберите оптимальный размер, угол и освещение для реалистичного результата.",
        height=120
    )

    st.markdown("---")

    process_button = st.button(
        "🚀 Создать изображение",
        type="primary",
        use_container_width=True,
        help="Gemini 2.0 Flash сгенерирует новое изображение"
    )


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
    st.subheader("✨ Результат от Gemini")
    if 'result_image' not in st.session_state:
        st.session_state.result_image = None

    if st.session_state.result_image:
        st.image(st.session_state.result_image, use_column_width=True)

        # Кнопка скачивания
        buf = BytesIO()
        st.session_state.result_image.save(buf, format="PNG")
        st.download_button(
            label="💾 Скачать результат",
            data=buf.getvalue(),
            file_name="cat_face_swap_gemini.png",
            mime="image/png",
            use_container_width=True
        )
    else:
        st.info("Результат появится здесь")


# Обработка
if process_button:
    if not base_image_file or not cat_face_file:
        st.error("⚠️ Пожалуйста, загрузите оба изображения!")
    else:
        with st.spinner("🤖 Gemini 2.0 Flash генерирует изображение..."):
            # Загружаем изображения
            base_image = Image.open(BytesIO(base_image_file.getvalue()))
            cat_face_image = Image.open(BytesIO(cat_face_file.getvalue()))

            # Конвертируем в RGB
            if base_image.mode != 'RGB':
                base_image = base_image.convert('RGB')
            if cat_face_image.mode != 'RGB':
                cat_face_image = cat_face_image.convert('RGB')

            # Оптимизируем размер для API
            max_size = (1024, 1024)
            base_image.thumbnail(max_size, Image.Resampling.LANCZOS)
            cat_face_image.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Кодируем в base64
            base_b64 = encode_image_to_base64(base_image)
            cat_b64 = encode_image_to_base64(cat_face_image)

            # Отправляем в Gemini
            result_image = generate_face_swap_with_gemini(base_b64, cat_b64, custom_prompt)

            if result_image:
                st.session_state.result_image = result_image
                st.success("✅ Готово! Результат в правой колонке")
                st.rerun()
            else:
                st.error("❌ Не удалось получить изображение от Gemini")


# Футер
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>🐱 Cat Face Swap | Powered by Gemini 2.0 Flash Experimental (Nano Banana)</p>
    <p><small>Прямая генерация изображений через Google AI</small></p>
</div>
""", unsafe_allow_html=True)
