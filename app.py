import streamlit as st
import replicate
from PIL import Image
import io
from datetime import datetime
import requests

# Настройка страницы
st.set_page_config(
    page_title="Nano Banana Image Generator",
    page_icon="🍌",
    layout="wide"
)

# Инициализация Replicate API
try:
    replicate_client = replicate.Client(api_token=st.secrets["REPLICATE_API_TOKEN"])
except Exception as e:
    st.error("⚠️ Ошибка подключения к Replicate API. Проверьте токен в secrets.toml")
    st.stop()

# Заголовок
st.title("🍌 Nano Banana - Image Generator")
st.markdown("Загрузите до 2-х изображений и опишите, что хотите получить")

# Боковая панель с настройками
with st.sidebar:
    st.header("⚙️ Настройки генерации")
    
    st.info("**Модель:** google/nano-banana")
    
    st.divider()
    
    st.markdown("### 💡 Советы:")
    st.markdown("""
    - Загрузите 1-2 referencer изображения
    - Опишите желаемые изменения детально
    - Укажите конкретный стиль
    - Будьте креативны с промптами
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
            st.image(image_1, caption="Референс 1", use_column_width=True)
            # Сохраняем в session_state для передачи в API
            st.session_state['image_1'] = uploaded_file_1
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
            st.image(image_2, caption="Референс 2", use_column_width=True)
            # Сохраняем в session_state для передачи в API
            st.session_state['image_2'] = uploaded_file_2
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
                    
                    # Загружаем изображения по URL
                    for img_url in output:
                        try:
                            response = requests.get(img_url)
                            img = Image.open(io.BytesIO(response.content))
                            generated_images.append(img)
                        except Exception as e:
                            st.warning(f"Не удалось загрузить изображение: {e}")
                    
                    if generated_images:
                        st.session_state['generated_images'] = generated_images
                        
                        # Счетчик
                        if 'generated_count' not in st.session_state:
                            st.session_state['generated_count'] = 0
                        st.session_state['generated_count'] += len(generated_images)
                        
                        st.success(f"✅ Успешно сгенерировано {len(generated_images)} изображение(й)!")
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
    
    # Отображение в колонках
    num_cols = min(len(st.session_state['generated_images']), 3)
    cols = st.columns(num_cols)
    
    for idx, img in enumerate(st.session_state['generated_images']):
        with cols[idx % num_cols]:
            st.image(img, caption=f"Результат {idx + 1}", use_column_width=True)
            
            # Кнопка скачивания
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            byte_data = buf.getvalue()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"nano_banana_{timestamp}_{idx + 1}.png"
            
            st.download_button(
                label="⬇️ Скачать",
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
    2. **Описание**: Указываете промпт с описанием желаемого результата
    3. **Генерация**: Модель Nano Banana обрабатывает запрос через Replicate API
    4. **Результат**: Получаете новое изображение на основе ваших референсов
    
    ### Модель: google/nano-banana
    - Быстрая генерация изображений
    - Поддержка image-to-image трансформаций
    - Работает через Replicate API
    """)

# Футер
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; padding: 20px;'>
    Powered by Google Nano Banana via Replicate | Streamlit
</div>
""", unsafe_allow_html=True)
