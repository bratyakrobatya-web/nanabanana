import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image
import json
import numpy as np
from rembg import remove
import cv2

# Настройка страницы
st.set_page_config(
    page_title="Cat Face Swap 🐱",
    page_icon="🐱",
    layout="wide"
)

# Заголовок приложения
st.title("🐱 Cat Face Swap - Замена мордочек котов")
st.markdown("Загрузите базовое изображение и фото с мордочкой кота для автоматической замены")

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


def call_gemini_for_analysis(base_image_b64, cat_face_b64, custom_prompt, model="gemini-2.0-flash-exp"):
    """
    Вызов Gemini для анализа изображений и получения инструкций
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GOOGLE_AI_STUDIO_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    # Промпт с запросом JSON структуры
    user_message = f"""Analyze these two images for a cat face swap task:

IMAGE 1: Base image where we want to place the cat face
IMAGE 2: Source image with the cat face to extract

Task: {custom_prompt}

Please provide a detailed analysis in the following JSON format:
{{
    "base_image_description": "description of the base image",
    "cat_face_description": "description of the cat face in source image",
    "placement_instructions": {{
        "position": "where to place (e.g., center, top-left, etc.)",
        "suggested_x_percent": 50,
        "suggested_y_percent": 50,
        "suggested_scale_percent": 100,
        "rotation_degrees": 0
    }},
    "adjustments": "color, lighting, and other adjustments needed",
    "step_by_step": ["step 1", "step 2", "..."]
}}

Provide both the JSON and a human-readable explanation."""

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Here is IMAGE 1 (BASE IMAGE):"
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": base_image_b64
                        }
                    },
                    {
                        "text": "Here is IMAGE 2 (SOURCE - cat face to extract):"
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": cat_face_b64
                        }
                    },
                    {
                        "text": user_message
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 2048
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()

        if 'candidates' in result and len(result['candidates']) > 0:
            content = result['candidates'][0]['content']
            if 'parts' in content and len(content['parts']) > 0:
                return content['parts'][0]['text']
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка при вызове Gemini API: {str(e)}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            st.error(f"Детали: {e.response.text}")
        return None


def remove_background(image):
    """Удаляет фон с изображения используя rembg"""
    try:
        # Конвертируем PIL Image в bytes
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        # Удаляем фон
        output = remove(img_byte_arr)

        # Конвертируем обратно в PIL Image
        result_image = Image.open(BytesIO(output))
        return result_image
    except Exception as e:
        st.warning(f"Не удалось удалить фон: {str(e)}")
        return image


def overlay_cat_face(base_image, cat_face_image, x_percent=50, y_percent=50, scale_percent=100, rotation=0, remove_bg=True):
    """
    Накладывает мордочку кота на базовое изображение

    Args:
        base_image: PIL Image - базовое изображение
        cat_face_image: PIL Image - изображение с мордочкой кота
        x_percent: позиция по X в процентах (0-100)
        y_percent: позиция по Y в процентах (0-100)
        scale_percent: масштаб мордочки в процентах (10-200)
        rotation: угол поворота в градусах
        remove_bg: удалить ли фон у мордочки

    Returns:
        PIL Image - результирующее изображение
    """
    # Создаем копию базового изображения
    result = base_image.copy()

    # Удаляем фон с мордочки кота если нужно
    if remove_bg:
        cat_face = remove_background(cat_face_image)
    else:
        cat_face = cat_face_image.copy()

    # Изменяем размер мордочки
    base_width = base_image.width
    base_height = base_image.height

    # Вычисляем новый размер мордочки
    scale_factor = scale_percent / 100.0
    new_width = int(cat_face.width * scale_factor)
    new_height = int(cat_face.height * scale_factor)

    # Ограничиваем размер
    max_width = int(base_width * 0.8)
    max_height = int(base_height * 0.8)
    if new_width > max_width:
        ratio = max_width / new_width
        new_width = max_width
        new_height = int(new_height * ratio)
    if new_height > max_height:
        ratio = max_height / new_height
        new_height = max_height
        new_width = int(new_width * ratio)

    cat_face = cat_face.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Поворачиваем если нужно
    if rotation != 0:
        cat_face = cat_face.rotate(rotation, expand=True, fillcolor=(0, 0, 0, 0))

    # Вычисляем позицию для вставки
    x_pos = int((base_width * x_percent / 100) - (cat_face.width / 2))
    y_pos = int((base_height * y_percent / 100) - (cat_face.height / 2))

    # Ограничиваем позицию чтобы мордочка не выходила за границы
    x_pos = max(0, min(x_pos, base_width - cat_face.width))
    y_pos = max(0, min(y_pos, base_height - cat_face.height))

    # Накладываем мордочку на базовое изображение
    if cat_face.mode == 'RGBA':
        result.paste(cat_face, (x_pos, y_pos), cat_face)
    else:
        result.paste(cat_face, (x_pos, y_pos))

    return result


# Боковая панель с настройками
with st.sidebar:
    st.header("⚙️ Настройки")

    st.subheader("1️⃣ Базовое изображение")
    st.markdown("Загрузите изображение, на котором будет размещена мордочка")
    base_image_file = st.file_uploader(
        "Выберите базовое изображение",
        type=['png', 'jpg', 'jpeg'],
        key="base_image"
    )

    st.subheader("2️⃣ Фото с мордочкой кота")
    st.markdown("Загрузите фото с мордочкой кота")
    cat_face_file = st.file_uploader(
        "Выберите фото кота",
        type=['png', 'jpg', 'jpeg'],
        key="cat_face"
    )

    st.subheader("3️⃣ Модель Gemini")
    model_choice = st.selectbox(
        "Выберите модель",
        options=[
            "gemini-2.0-flash-exp",
            "gemini-1.5-pro-latest",
            "gemini-1.5-flash-latest"
        ],
        index=0,
        help="Gemini 2.0 Flash Experimental - лучший вариант для анализа изображений"
    )

    st.subheader("4️⃣ Настройки наложения")

    use_ai_position = st.checkbox(
        "Использовать AI для определения позиции",
        value=True,
        help="Gemini автоматически определит где разместить мордочку"
    )

    if not use_ai_position:
        x_position = st.slider("Позиция по горизонтали (%)", 0, 100, 50)
        y_position = st.slider("Позиция по вертикали (%)", 0, 100, 50)
    else:
        x_position = 50
        y_position = 50

    scale = st.slider("Размер мордочки (%)", 10, 200, 100)
    rotation = st.slider("Поворот (градусы)", -180, 180, 0)
    remove_bg = st.checkbox("Удалить фон у мордочки", value=True)

    st.subheader("5️⃣ Промпт для AI")
    custom_prompt = st.text_area(
        "Опишите как должна быть размещена мордочка",
        value="Разместить мордочку кота естественным образом на базовом изображении, подобрав оптимальный размер и позицию.",
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
    if 'result_image' not in st.session_state:
        st.session_state.result_image = None

    if st.session_state.result_image:
        st.image(st.session_state.result_image, use_column_width=True)

        # Кнопка для скачивания
        buf = BytesIO()
        st.session_state.result_image.save(buf, format="PNG")
        st.download_button(
            label="💾 Скачать результат",
            data=buf.getvalue(),
            file_name="cat_face_swap_result.png",
            mime="image/png",
            use_container_width=True
        )
    else:
        st.info("Результат появится здесь после обработки")


# Обработка изображений
if process_button:
    if not base_image_file or not cat_face_file:
        st.error("⚠️ Пожалуйста, загрузите оба изображения!")
    else:
        with st.spinner("🔄 Обработка изображений..."):
            # Загружаем изображения
            base_image = Image.open(BytesIO(base_image_file.getvalue()))
            cat_face_image = Image.open(BytesIO(cat_face_file.getvalue()))

            # Конвертируем в RGB если нужно
            if base_image.mode != 'RGB':
                base_image = base_image.convert('RGB')
            if cat_face_image.mode not in ['RGB', 'RGBA']:
                cat_face_image = cat_face_image.convert('RGBA')

            final_x = x_position
            final_y = y_position
            final_scale = scale

            # Используем AI для анализа если включено
            if use_ai_position:
                with st.spinner("🤖 AI анализирует изображения..."):
                    # Изменяем размер для быстрой обработки
                    temp_base = base_image.copy()
                    temp_cat = cat_face_image.copy()
                    temp_base.thumbnail((512, 512), Image.Resampling.LANCZOS)
                    temp_cat.thumbnail((512, 512), Image.Resampling.LANCZOS)

                    base_b64 = encode_image_to_base64(temp_base)
                    cat_b64 = encode_image_to_base64(temp_cat)

                    analysis = call_gemini_for_analysis(base_b64, cat_b64, custom_prompt, model=model_choice)

                    if analysis:
                        with st.expander("📋 Анализ от AI", expanded=False):
                            st.markdown(analysis)

                        # Пытаемся извлечь координаты из анализа
                        try:
                            # Ищем JSON в ответе
                            import re
                            json_match = re.search(r'\{[\s\S]*\}', analysis)
                            if json_match:
                                data = json.loads(json_match.group())
                                if 'placement_instructions' in data:
                                    pi = data['placement_instructions']
                                    final_x = pi.get('suggested_x_percent', x_position)
                                    final_y = pi.get('suggested_y_percent', y_position)
                                    final_scale = pi.get('suggested_scale_percent', scale)
                                    rotation = pi.get('rotation_degrees', rotation)
                                    st.success(f"✅ AI предлагает: позиция ({final_x}%, {final_y}%), размер {final_scale}%")
                        except:
                            st.info("Используем заданные вручную параметры")

            # Создаем результирующее изображение
            with st.spinner("🎨 Создаю результирующее изображение..."):
                result_image = overlay_cat_face(
                    base_image,
                    cat_face_image,
                    x_percent=final_x,
                    y_percent=final_y,
                    scale_percent=final_scale,
                    rotation=rotation,
                    remove_bg=remove_bg
                )

                st.session_state.result_image = result_image
                st.success("✅ Готово! Результат в правой колонке")
                st.rerun()


# Футер
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>🐱 Cat Face Swap | Powered by Gemini 2.0 Flash & Python Image Processing</p>
    <p><small>Реальная замена мордочек котов с использованием AI и обработки изображений</small></p>
</div>
""", unsafe_allow_html=True)
