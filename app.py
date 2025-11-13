import streamlit as st
import replicate
from PIL import Image
import io
from datetime import datetime
import requests
import base64

# Настройка страницы
st.set_page_config(
    page_title="Nano Banana Image Generator",
    page_icon="🍌",
    layout="wide"
)

# Функция для загрузки шрифта в base64
def load_font_as_base64(font_path):
    with open(font_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# Загружаем кастомный шрифт
font_base64 = load_font_as_base64("ArexaDemo-Regular.otf")

# Темный металлический стиль
st.markdown(f"""
<style>
    @font-face {{
        font-family: 'ArexaDemo';
        src: url(data:font/otf;base64,{font_base64}) format('opentype');
    }}

    /* Основной стиль приложения */
    .stApp {{
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 50%, #1a1a1a 100%);
        background-attachment: fixed;
    }}

    /* Металлический фон для контейнеров */
    .stApp > div {{
        background: transparent;
    }}

    /* Применяем шрифт ко всем текстовым элементам */
    h1, h2, h3, h4, h5, h6, p, div, span, label, .stMarkdown, .stText {{
        font-family: 'ArexaDemo', sans-serif !important;
        color: #e0e0e0 !important;
    }}

    /* Заголовки с металлическим эффектом */
    h1 {{
        background: linear-gradient(180deg, #ffffff 0%, #c0c0c0 50%, #808080 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3.5rem !important;
        font-weight: bold !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
    }}

    h2 {{
        background: linear-gradient(180deg, #f0f0f0 0%, #b0b0b0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2rem !important;
    }}

    h3 {{
        color: #c0c0c0 !important;
        font-size: 1.5rem !important;
    }}

    /* Стиль для боковой панели */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #252525 0%, #1a1a1a 100%);
        border-right: 2px solid #404040;
    }}

    /* Стиль для кнопок */
    .stButton > button {{
        font-family: 'ArexaDemo', sans-serif !important;
        background: linear-gradient(135deg, #4a4a4a 0%, #2a2a2a 100%);
        color: #ffffff !important;
        border: 2px solid #606060;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
    }}

    .stButton > button:hover {{
        background: linear-gradient(135deg, #5a5a5a 0%, #3a3a3a 100%);
        border-color: #808080;
        box-shadow: 0 4px 8px rgba(255,255,255,0.1);
    }}

    /* Основная кнопка */
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #6a6a6a 0%, #4a4a4a 100%);
        border: 2px solid #909090;
    }}

    .stButton > button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #7a7a7a 0%, #5a5a5a 100%);
        box-shadow: 0 6px 12px rgba(255,255,255,0.2);
    }}

    /* Текстовые поля */
    .stTextArea textarea, .stTextInput input {{
        font-family: 'ArexaDemo', sans-serif !important;
        background-color: #2a2a2a !important;
        color: #ffffff !important;
        border: 2px solid #404040 !important;
        border-radius: 6px;
    }}

    /* Стиль для метрик */
    div[data-testid="stMetricValue"] {{
        color: #c0c0c0 !important;
    }}

    /* Информационные блоки */
    .stAlert {{
        background-color: #2a2a2a !important;
        border: 1px solid #404040 !important;
        color: #e0e0e0 !important;
    }}

    /* Разделители */
    hr {{
        border-color: #404040 !important;
    }}
</style>
""", unsafe_allow_html=True)

# Функция для исправления ориентации изображения и преобразования в 9:16
def fix_image_orientation_and_resize(image):
    """Исправляет ориентацию изображения на основе EXIF и преобразует в формат 9:16"""
    try:
        # Исправляем ориентацию на основе EXIF данных
        from PIL import ImageOps
        image = ImageOps.exif_transpose(image)

        # Целевое соотношение сторон 9:16 (вертикальный формат)
        target_ratio = 9 / 16
        width, height = image.size
        current_ratio = width / height

        # Если изображение горизонтальное или квадратное, обрезаем/изменяем размер
        if current_ratio > target_ratio:
            # Изображение слишком широкое, обрезаем по бокам
            new_width = int(height * target_ratio)
            left = (width - new_width) // 2
            image = image.crop((left, 0, left + new_width, height))
        elif current_ratio < target_ratio:
            # Изображение слишком высокое, обрезаем сверху и снизу
            new_height = int(width / target_ratio)
            top = (height - new_height) // 2
            image = image.crop((0, top, width, top + new_height))

        # Изменяем размер до стандартного разрешения 9:16
        # Используем 1080x1920 как базовый размер для вертикального формата
        target_width = 1080
        target_height = 1920
        image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)

        return image
    except Exception as e:
        st.warning(f"Не удалось обработать изображение: {e}")
        return image

# Инициализация Replicate API
try:
    replicate_client = replicate.Client(api_token=st.secrets["REPLICATE_API_TOKEN"])
except Exception as e:
    st.error("⚠️ Ошибка подключения к Replicate API. Проверьте токен в secrets.toml")
    st.stop()

# Заголовок
st.title("🍌 Nano Banana - Image Generator")
st.markdown("### Генератор изображений в формате 9:16")
st.markdown("Загрузите до 2-х референсных изображений и опишите желаемый результат. Все изображения будут автоматически преобразованы в вертикальный формат 9:16.")

# Боковая панель с настройками
with st.sidebar:
    st.header("⚙️ Настройки генерации")
    
    st.info("**Модель:** google/nano-banana")
    
    st.divider()
    
    st.markdown("### 💡 Советы:")
    st.markdown("""
    - Загрузите 1-2 референсных изображения
    - Все изображения автоматически конвертируются в 9:16
    - Ориентация изображений корректируется автоматически
    - Опишите желаемые изменения детально
    - Укажите конкретный стиль
    - Максимум 3 результата за раз
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
        help="Загрузите первое референсное изображение - будет преобразовано в формат 9:16",
        key="uploader_1"
    )
    if uploaded_file_1 is not None:
        try:
            image_1 = Image.open(uploaded_file_1)
            # Применяем исправление ориентации и изменение размера
            image_1 = fix_image_orientation_and_resize(image_1)
            st.image(image_1, caption="Референс 1 (9:16)", width=300)
            # Сохраняем обработанное изображение в session_state
            buf = io.BytesIO()
            image_1.save(buf, format='PNG')
            buf.seek(0)
            st.session_state['image_1'] = buf
        except Exception as e:
            st.error(f"Ошибка загрузки изображения 1: {e}")

with col2:
    uploaded_file_2 = st.file_uploader(
        "Изображение 2 (опционально)",
        type=['png', 'jpg', 'jpeg', 'webp'],
        help="Загрузите второе референсное изображение - будет преобразовано в формат 9:16",
        key="uploader_2"
    )
    if uploaded_file_2 is not None:
        try:
            image_2 = Image.open(uploaded_file_2)
            # Применяем исправление ориентации и изменение размера
            image_2 = fix_image_orientation_and_resize(image_2)
            st.image(image_2, caption="Референс 2 (9:16)", width=300)
            # Сохраняем обработанное изображение в session_state
            buf = io.BytesIO()
            image_2.save(buf, format='PNG')
            buf.seek(0)
            st.session_state['image_2'] = buf
        except Exception as e:
            st.error(f"Ошибка загрузки изображения 2: {e}")

# Промпт
st.subheader("✍️ Опишите желаемый результат")

prompt = st.text_area(
    "Промпт для генерации:",
    placeholder="Например: Make the sheets in the style of the logo. Make the scene natural.",
    height=120,
    help="Опишите максимально детально, что должно получиться"
)

# Примеры промптов
with st.expander("📝 Примеры промптов"):
    examples = [
        "Make the sheets in the style of the logo. Make the scene natural.",
        "Combine these images in cyberpunk style with neon lighting",
        "Apply the style of the first image to the second one",
        "Create a photorealistic composition with dramatic lighting",
        "Merge these images in vintage 1970s photography style"
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
    "🚀 Сгенерировать изображение",
    type="primary",
    use_container_width=True,
    disabled=(image_1 is None)
)

# Обработка генерации
if generate_button:
    if not prompt or len(prompt.strip()) < 5:
        st.warning("⚠️ Пожалуйста, введите описание (минимум 5 символов)")
    elif image_1 is None:
        st.warning("⚠️ Загрузите хотя бы одно изображение")
    else:
        with st.spinner("🎨 Генерирую изображение... Это может занять 20-40 секунд..."):
            try:
                # Подготовка входных данных для Replicate
                input_data = {
                    "prompt": prompt,
                    "image_input": []
                }
                
                # Добавляем изображения в массив
                if 'image_1' in st.session_state:
                    st.session_state['image_1'].seek(0)
                    input_data["image_input"].append(st.session_state['image_1'])
                
                if 'image_2' in st.session_state and image_2 is not None:
                    st.session_state['image_2'].seek(0)
                    input_data["image_input"].append(st.session_state['image_2'])
                
                # Запуск модели на Replicate
                output = replicate_client.run(
                    "google/nano-banana",
                    input=input_data
                )
                
                # Обработка результата
                # output может быть URL или список URL
                if output:
                    generated_images = []

                    # Если output это строка (один URL)
                    if isinstance(output, str):
                        output = [output]

                    # Ограничиваем до 3 изображений максимум
                    output = output[:3]

                    # Загружаем изображения по URL
                    for img_url in output:
                        try:
                            response = requests.get(img_url)
                            img = Image.open(io.BytesIO(response.content))
                            # Применяем обработку к сгенерированным изображениям
                            img = fix_image_orientation_and_resize(img)
                            generated_images.append(img)
                        except Exception as e:
                            st.warning(f"Не удалось загрузить изображение: {e}")

                    if generated_images:
                        st.session_state['generated_images'] = generated_images

                        # Счетчик
                        if 'generated_count' not in st.session_state:
                            st.session_state['generated_count'] = 0
                        st.session_state['generated_count'] += len(generated_images)

                        st.success(f"✅ Успешно сгенерировано {len(generated_images)} изображение(й) в формате 9:16!")
                    else:
                        st.error("❌ Не удалось получить изображения из ответа")
                else:
                    st.error("❌ Модель не вернула результат")
                    
            except Exception as e:
                error_message = str(e)
                st.error(f"❌ Ошибка генерации: {error_message}")
                
                st.info("""
                **Возможные причины ошибки:**
                - Проверьте правильность REPLICATE_API_TOKEN
                - Убедитесь что модель google/nano-banana доступна
                - Проверьте формат входных данных (schema модели)
                - Возможно исчерпан лимит API
                """)

# Отображение результатов
if 'generated_images' in st.session_state and st.session_state['generated_images']:
    st.divider()
    st.subheader("🖼️ Сгенерированные изображения")
    st.markdown("**Формат изображений: 9:16 (1080x1920)**")

    # Отображение в колонках (максимум 3)
    num_cols = min(len(st.session_state['generated_images']), 3)
    cols = st.columns(num_cols)

    for idx, img in enumerate(st.session_state['generated_images']):
        with cols[idx % num_cols]:
            # Отображаем изображение с фиксированной шириной для формата 9:16
            st.image(img, caption=f"Результат {idx + 1} (9:16)", width=300)

            # Кнопка скачивания
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            byte_data = buf.getvalue()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"nano_banana_9x16_{timestamp}_{idx + 1}.png"

            st.download_button(
                label="⬇️ Скачать PNG",
                data=byte_data,
                file_name=filename,
                mime="image/png",
                key=f"download_result_{idx}",
                use_container_width=True
            )

# Информационный блок
with st.expander("ℹ️ Как это работает"):
    st.markdown("""
    ### Процесс генерации:

    1. **Загрузка референсов**: Вы загружаете 1-2 изображения
    2. **Автоматическая обработка**: Изображения конвертируются в формат 9:16 (1080x1920)
    3. **Исправление ориентации**: EXIF данные учитываются для правильного поворота
    4. **Описание**: Указываете промпт с описанием желаемого результата
    5. **Генерация**: Модель Nano Banana обрабатывает запрос через Replicate API
    6. **Результат**: Получаете до 3 новых изображений в формате 9:16

    ### Особенности приложения:
    - **Формат 9:16**: Все изображения автоматически преобразуются в вертикальный формат
    - **Без переворота**: EXIF ориентация учитывается автоматически
    - **Темный стиль**: Металлический дизайн интерфейса
    - **Кастомный шрифт**: ArexaDemo для уникального визуала
    - **Ограничение**: Максимум 3 результата для оптимального просмотра

    ### Модель: google/nano-banana
    - Быстрая генерация изображений
    - Поддержка image-to-image трансформаций
    - Работает через Replicate API
    """)

# Футер
st.divider()
st.markdown("""
<div style='text-align: center; padding: 20px;'>
    <p style='color: #808080; font-family: ArexaDemo, sans-serif; font-size: 0.9rem;'>
        Powered by Google Nano Banana via Replicate | Streamlit
    </p>
    <p style='color: #606060; font-family: ArexaDemo, sans-serif; font-size: 0.8rem;'>
        Format: 9:16 | EXIF Auto-Correction | Metal Dark Theme
    </p>
</div>
""", unsafe_allow_html=True)
