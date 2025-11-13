import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
from datetime import datetime

# Настройка страницы
st.set_page_config(
    page_title="Gemini Image Editor",
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
st.title("🎨 Редактор изображений с Gemini 2.5 Flash")
st.markdown("Загрузите до 2-х изображений и опишите, что хотите получить")

# Боковая панель с настройками
with st.sidebar:
    st.header("⚙️ Настройки")
    
    aspect_ratio = st.selectbox(
        "Соотношение сторон",
        options=["1:1", "16:9", "9:16", "4:3", "3:4"],
        index=0,
        help="Формат результирующего изображения"
    )
    
    num_outputs = st.slider(
        "Количество вариантов",
        min_value=1,
        max_value=4,
        value=1,
        help="Сколько вариантов сгенерировать"
    )
    
    st.divider()
    
    st.markdown("### 💡 Советы:")
    st.markdown("""
    - Загрузите 1-2 референсных изображения
    - Опишите желаемые изменения
    - Укажите стиль обработки
    - Будьте конкретны в деталях
    """)
    
    st.divider()
    
    if 'generated_count' in st.session_state:
        st.metric("Изображений создано", st.session_state['generated_count'])

# Основная область - загрузка изображений
st.subheader("📤 Загрузка изображений")

col1, col2 = st.columns(2)

with col1:
    uploaded_file_1 = st.file_uploader(
        "Изображение 1",
        type=['png', 'jpg', 'jpeg', 'webp'],
        help="Загрузите первое изображение"
    )
    if uploaded_file_1:
        image_1 = Image.open(uploaded_file_1)
        st.image(image_1, caption="Изображение 1", use_container_width=True)

with col2:
    uploaded_file_2 = st.file_uploader(
        "Изображение 2 (опционально)",
        type=['png', 'jpg', 'jpeg', 'webp'],
        help="Загрузите второе изображение (необязательно)"
    )
    if uploaded_file_2:
        image_2 = Image.open(uploaded_file_2)
        st.image(image_2, caption="Изображение 2", use_container_width=True)

# Промпт
st.subheader("✍️ Опишите желаемый результат")

prompt = st.text_area(
    "Промпт для обработки изображений:",
    placeholder="Например: Объедини эти два изображения в едином стиле киберпанк, добавь неоновое освещение и футуристические элементы",
    height=120,
    help="Опишите, что должно получиться из загруженных изображений"
)

# Примеры промптов
with st.expander("📝 Примеры промптов для работы с изображениями"):
    examples = [
        "Объедини эти изображения в коллаж в стиле винтажного постера",
        "Примени стиль первого изображения ко второму",
        "Создай фотореалистичную композицию из этих элементов",
        "Объедини в единую сцену с драматическим освещением",
        "Сделай микс этих изображений в стиле акварельной живописи"
    ]
    for example in examples:
        if st.button(example, key=example):
            st.session_state['prompt_example'] = example
            st.rerun()

# Применяем пример промпта если выбран
if 'prompt_example' in st.session_state:
    prompt = st.session_state['prompt_example']
    del st.session_state['prompt_example']

# Кнопка генерации
st.divider()
generate_button = st.button(
    "🚀 Сгенерировать результат",
    type="primary",
    use_container_width=True,
    disabled=not uploaded_file_1
)

# Обработка генерации
if generate_button:
    if not prompt or len(prompt.strip()) < 10:
        st.warning("⚠️ Пожалуйста, введите описание (минимум 10 символов)")
    elif not uploaded_file_1:
        st.warning("⚠️ Загрузите хотя бы одно изображение")
    else:
        with st.spinner("🎨 Обрабатываю изображения... Это может занять 20-40 секунд..."):
            try:
                # Подготовка модели
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
                
                # Подготовка контента для запроса
                content_parts = []
                
                # Добавляем промпт
                content_parts.append(prompt)
                
                # Добавляем первое изображение
                content_parts.append(image_1)
                
                # Добавляем второе изображение если есть
                if uploaded_file_2:
                    content_parts.append(image_2)
                
                # Генерация с изображениями
                response = model.generate_content(
                    content_parts,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.4,
                    )
                )
                
                # Проверяем, вернулась ли картинка
                if hasattr(response, 'parts'):
                    # Ищем изображения в ответе
                    generated_images = []
                    
                    for part in response.parts:
                        if hasattr(part, 'inline_data'):
                            # Получаем данные изображения
                            image_data = part.inline_data.data
                            mime_type = part.inline_data.mime_type
                            
                            # Конвертируем в PIL Image
                            img = Image.open(io.BytesIO(image_data))
                            generated_images.append(img)
                    
                    if generated_images:
                        st.session_state['generated_images'] = generated_images
                        
                        # Счетчик
                        if 'generated_count' not in st.session_state:
                            st.session_state['generated_count'] = 0
                        st.session_state['generated_count'] += len(generated_images)
                        
                        st.success(f"✅ Успешно сгенерировано {len(generated_images)} изображение(й)!")
                    else:
                        # Если изображения не вернулись, показываем текстовый ответ
                        st.warning("⚠️ Модель вернула текстовый ответ вместо изображения")
                        st.info("Ответ модели:")
                        st.write(response.text)
                        
                        st.error("""
                        **Возможные причины:**
                        - Gemini 2.5 Flash не поддерживает генерацию изображений (только анализ)
                        - Нужно использовать Imagen для генерации
                        - Требуется другая модель или настройка API
                        """)
                else:
                    st.warning("⚠️ Модель не вернула изображение")
                    st.info(f"Ответ: {response.text if hasattr(response, 'text') else 'Нет данных'}")
                
            except Exception as e:
                error_message = str(e)
                st.error(f"❌ Ошибка: {error_message}")
                
                st.info("""
                **Важная информация:**
                
                Gemini 2.5 Flash (включая версию "Nano Banana") - это модель для **анализа** изображений, 
                а не для их **генерации**.
                
                Для генерации изображений используйте:
                - **Imagen 3** (через Google AI Studio / Vertex AI)
                - **DALL-E** (OpenAI)
                - **Stable Diffusion** (Stability AI)
                
                Если вам нужно объединить/обработать изображения, потребуется другой подход или API.
                """)

# Отображение результатов
if 'generated_images' in st.session_state and st.session_state['generated_images']:
    st.divider()
    st.subheader("🖼️ Результаты")
    
    # Отображение в колонках
    num_cols = min(len(st.session_state['generated_images']), 3)
    cols = st.columns(num_cols)
    
    for idx, img in enumerate(st.session_state['generated_images']):
        with cols[idx % num_cols]:
            st.image(img, caption=f"Результат {idx + 1}", use_container_width=True)
            
            # Кнопка скачивания
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            byte_data = buf.getvalue()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gemini_result_{timestamp}_{idx + 1}.png"
            
            st.download_button(
                label="⬇️ Скачать",
                data=byte_data,
                file_name=filename,
                mime="image/png",
                key=f"download_{idx}",
                use_container_width=True
            )

# Футер
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; padding: 20px;'>
    Powered by Google Gemini 2.5 Flash | Streamlit
</div>
""", unsafe_allow_html=True)
