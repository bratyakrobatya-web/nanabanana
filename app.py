import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
from datetime import datetime
import base64

# Настройка страницы
st.set_page_config(
    page_title="Imagen 3 Image Editor",
    page_icon="🎨",
    layout="wide"
)

# Инициализация API
try:
    genai.configure(api_key=st.secrets["GOOGLE_AI_STUDIO_KEY"])
except Exception as e:
    st.error("⚠️ Ошибка подключения к API. Проверьте ключ в secrets.toml")
    st.stop()

# Заголовок
st.title("🎨 Генерация изображений с Imagen 3")
st.markdown("Загрузите до 2-х изображений и опишите, что хотите получить")

# Боковая панель с настройками
with st.sidebar:
    st.header("⚙️ Настройки генерации")
    
    num_outputs = st.slider(
        "Количество вариантов",
        min_value=1,
        max_value=4,
        value=1,
        help="Сколько вариантов сгенерировать"
    )
    
    aspect_ratio = st.selectbox(
        "Соотношение сторон",
        options=["1:1", "9:16", "16:9", "4:3", "3:4"],
        index=0,
        help="Формат результирующего изображения"
    )
    
    safety_level = st.selectbox(
        "Фильтр безопасности",
        options=["block_some", "block_most", "block_few"],
        index=0,
        help="Уровень фильтрации контента"
    )
    
    negative_prompt = st.text_input(
        "Негативный промпт (что исключить)",
        placeholder="low quality, blurry, distorted",
        help="Что НЕ должно быть на изображении"
    )
    
    st.divider()
    
    st.markdown("### 💡 Советы:")
    st.markdown("""
    - Загрузите 1-2 референсных изображения
    - Опишите желаемые изменения детально
    - Укажите конкретный стиль
    - Используйте негативный промпт для улучшения качества
    """)
    
    st.divider()
    
    if 'generated_count' in st.session_state:
        st.metric("Изображений создано", st.session_state['generated_count'])

# Основная область - загрузка изображений
st.subheader("📤 Загрузка референсных изображений")

col1, col2 = st.columns(2)

# Инициализация переменных для изображений
image_1 = None
image_2 = None
uploaded_file_1 = None
uploaded_file_2 = None

with col1:
    uploaded_file_1 = st.file_uploader(
        "Изображение 1 (обязательно)",
        type=['png', 'jpg', 'jpeg', 'webp'],
        help="Загрузите первое референсное изображение",
        key="uploader_1"
    )
    if uploaded_file_1 is not None:
        try:
            image_1 = Image.open(uploaded_file_1)
            st.image(image_1, caption="Референс 1", use_container_width=True)
        except Exception as e:
            st.error(f"Ошибка загрузки изображения 1: {e}")

with col2:
    uploaded_file_2 = st.file_uploader(
        "Изображение 2 (опционально)",
        type=['png', 'jpg', 'jpeg', 'webp'],
        help="Загрузите второе референсное изображение",
        key="uploader_2"
    )
    if uploaded_file_2 is not None:
        try:
            image_2 = Image.open(uploaded_file_2)
            st.image(image_2, caption="Референс 2", use_container_width=True)
        except Exception as e:
            st.error(f"Ошибка загрузки изображения 2: {e}")

# Промпт
st.subheader("✍️ Опишите желаемый результат")

prompt = st.text_area(
    "Промпт для генерации:",
    placeholder="Например: Создай новое изображение на основе этих референсов, объедини их стиль, добавь кинематографическое освещение, фотореалистичность, высокая детализация",
    height=120,
    help="Опишите максимально детально, что должно получиться"
)

# Примеры промптов
with st.expander("📝 Примеры промптов"):
    examples = [
        "Создай композицию объединяющую элементы этих изображений в едином стиле киберпанк с неоновым освещением",
        "Возьми стиль первого изображения и примени его ко второму, сохраняя композицию второго",
        "Создай фотореалистичный коллаж из этих изображений с драматическим освещением и глубиной резкости",
        "Объедини эти изображения в единую сцену в стиле винтажной фотографии 1970-х",
        "Создай сюрреалистическую композицию смешивая элементы обоих изображений, студийное освещение"
    ]
    for idx, example in enumerate(examples):
        if st.button(example, key=f"example_{idx}"):
            st.session_state['prompt_text'] = example
            st.rerun()

# Применяем пример промпта если выбран
if 'prompt_text' in st.session_state and st.session_state['prompt_text']:
    prompt = st.session_state['prompt_text']

# Кнопка генерации
st.divider()
generate_button = st.button(
    "🚀 Сгенерировать новое изображение",
    type="primary",
    use_container_width=True,
    disabled=(image_1 is None)
)

# Функция для конвертации изображения в base64
def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()
    return base64.b64encode(img_bytes).decode()

# Обработка генерации
if generate_button:
    if not prompt or len(prompt.strip()) < 10:
        st.warning("⚠️ Пожалуйста, введите описание (минимум 10 символов)")
    elif image_1 is None:
        st.warning("⚠️ Загрузите хотя бы одно изображение")
    else:
        with st.spinner("🎨 Генерирую изображение на основе ваших референсов... Это может занять 30-60 секунд..."):
            try:
                # Создаём расширенный промпт с описанием референсов
                enhanced_prompt = f"{prompt}\n\nReference image style characteristics to incorporate:"
                
                # Анализируем первое изображение через Gemini
                analyzer_model = genai.GenerativeModel('gemini-2.0-flash-exp')
                
                analysis_prompt = "Describe the visual style, colors, composition, lighting, and mood of this image in detail for image generation purposes. Be specific and technical."
                
                analysis_1 = analyzer_model.generate_content([analysis_prompt, image_1])
                enhanced_prompt += f"\n- Image 1 style: {analysis_1.text}"
                
                # Если есть второе изображение - анализируем его тоже
                if image_2 is not None:
                    analysis_2 = analyzer_model.generate_content([analysis_prompt, image_2])
                    enhanced_prompt += f"\n- Image 2 style: {analysis_2.text}"
                
                # Добавляем негативный промпт если есть
                if negative_prompt:
                    enhanced_prompt += f"\n\nAvoid: {negative_prompt}"
                
                st.info(f"📝 Расширенный промпт создан на основе анализа ваших изображений")
                
                # Теперь генерируем через Imagen
                try:
                    imagen_model = genai.GenerativeModel('imagen-3.0-generate-001')
                    
                    response = imagen_model.generate_images(
                        prompt=enhanced_prompt,
                        number_of_images=num_outputs,
                        aspect_ratio=aspect_ratio,
                        safety_filter_level=safety_level,
                        person_generation="allow_adult"
                    )
                    
                    if response.images:
                        st.session_state['generated_images'] = response.images
                        
                        # Счетчик
                        if 'generated_count' not in st.session_state:
                            st.session_state['generated_count'] = 0
                        st.session_state['generated_count'] += len(response.images)
                        
                        st.success(f"✅ Успешно сгенерировано {len(response.images)} изображение(й)!")
                    else:
                        st.error("❌ Не удалось сгенерировать изображения")
                        
                except Exception as imagen_error:
                    error_msg = str(imagen_error)
                    
                    if "imagen" in error_msg.lower() or "not found" in error_msg.lower():
                        st.error("❌ Модель Imagen 3.0 недоступна")
                        st.warning("""
                        **Imagen 3 недоступен в вашем регионе или требует:**
                        1. Включения Vertex AI в Google Cloud
                        2. Настройки биллинга
                        3. Активации API Imagen
                        
                        **Альтернативы:**
                        - Используйте веб-интерфейс Google AI Studio для генерации
                        - Попробуйте Vertex AI с правильной настройкой проекта
                        - Используйте другие сервисы: DALL-E 3, Midjourney, Stable Diffusion
                        """)
                        
                        # Показываем доступные модели
                        with st.expander("🔍 Доступные модели в вашем API"):
                            try:
                                for m in genai.list_models():
                                    st.code(f"{m.name} - {m.supported_generation_methods}")
                            except:
                                st.write("Не удалось получить список моделей")
                    else:
                        st.error(f"❌ Ошибка Imagen: {error_msg}")
                
            except Exception as e:
                error_message = str(e)
                st.error(f"❌ Ошибка: {error_message}")

# Отображение результатов
if 'generated_images' in st.session_state and st.session_state['generated_images']:
    st.divider()
    st.subheader("🖼️ Сгенерированные изображения")
    
    # Отображение в колонках
    num_cols = min(len(st.session_state['generated_images']), 3)
    cols = st.columns(num_cols)
    
    for idx, image_result in enumerate(st.session_state['generated_images']):
        with cols[idx % num_cols]:
            try:
                # Imagen возвращает объект с _pil_image
                img = image_result._pil_image
                st.image(img, caption=f"Результат {idx + 1}", use_container_width=True)
                
                # Кнопка скачивания
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                byte_data = buf.getvalue()
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"imagen_result_{timestamp}_{idx + 1}.png"
                
                st.download_button(
                    label="⬇️ Скачать",
                    data=byte_data,
                    file_name=filename,
                    mime="image/png",
                    key=f"download_result_{idx}",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Ошибка отображения результата {idx + 1}: {e}")

# Информационный блок
with st.expander("ℹ️ Как это работает"):
    st.markdown("""
    ### Процесс генерации:
    
    1. **Анализ референсов**: Gemini 2.5 Flash анализирует ваши загруженные изображения
    2. **Создание промпта**: Система создаёт детальный промпт на основе анализа
    3. **Генерация**: Imagen 3 создаёт новое изображение учитывая стиль референсов
    4. **Результат**: Вы получаете новое изображение, вдохновлённое вашими референсами
    
    ### Советы для лучших результатов:
    - Используйте чёткие, качественные референсные изображения
    - Детально описывайте желаемый результат
    - Экспериментируйте с негативными промптами
    - Генерируйте несколько вариантов для выбора лучшего
    """)

# Футер
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; padding: 20px;'>
    Powered by Google Imagen 3 + Gemini 2.5 Flash | Streamlit
</div>
""", unsafe_allow_html=True)
