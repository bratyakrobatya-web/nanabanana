import streamlit as st
import replicate
from PIL import Image
import io
from datetime import datetime
import requests
import base64

# Page configuration
st.set_page_config(
    page_title="Nano Banana Image Generator",
    page_icon="🍌",
    layout="wide"
)

# Function to load font as base64
def load_font_as_base64(font_path):
    with open(font_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# Load custom font
font_base64 = load_font_as_base64("ArexaDemo-Regular.otf")

# Dark metallic style with white text
st.markdown(f"""
<style>
    /* Main app styling */
    .stApp {{
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 50%, #1a1a1a 100%);
        background-attachment: fixed;
    }}

    /* Metallic background for containers */
    .stApp > div {{
        background: transparent;
    }}

    /* Default white text color */
    h1, h2, h3, h4, h5, h6, p, div, span, label, .stMarkdown, .stText {{
        color: #ffffff !important;
    }}

    /* Headers styling */
    h1 {{
        font-size: 3.625rem !important;
        font-weight: bold !important;
        color: #ffffff !important;
    }}

    h2 {{
        font-size: 2.125rem !important;
        color: #e0e0e0 !important;
    }}

    h3 {{
        color: #e0e0e0 !important;
        font-size: 1.625rem !important;
    }}

    /* Regular text */
    p, div, span, label {{
        font-size: calc(1rem + 2px) !important;
        color: #ffffff !important;
    }}

    /* Sidebar styling */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #252525 0%, #1a1a1a 100%);
        border-right: 2px solid #404040;
    }}

    /* Button styling */
    .stButton > button {{
        background: linear-gradient(135deg, #4a4a4a 0%, #2a2a2a 100%);
        color: #ffffff !important;
        border: 2px solid #606060;
        border-radius: 8px;
        font-weight: bold;
        font-size: calc(1rem + 2px) !important;
        transition: all 0.3s ease;
    }}

    .stButton > button:hover {{
        background: linear-gradient(135deg, #5a5a5a 0%, #3a3a3a 100%);
        border-color: #808080;
        box-shadow: 0 4px 8px rgba(255,255,255,0.1);
    }}

    /* Primary button */
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #6a6a6a 0%, #4a4a4a 100%);
        border: 2px solid #909090;
    }}

    .stButton > button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #7a7a7a 0%, #5a5a5a 100%);
        box-shadow: 0 6px 12px rgba(255,255,255,0.2);
    }}

    /* Text input and textarea styling */
    .stTextArea textarea, .stTextInput input {{
        background-color: #2a2a2a !important;
        color: #ffffff !important;
        border: 2px solid #404040 !important;
        border-radius: 6px;
        font-size: calc(1rem + 2px) !important;
    }}

    /* White placeholder text */
    .stTextArea textarea::placeholder {{
        color: #ffffff !important;
        opacity: 0.7;
    }}

    /* File uploader - black background with red dashed border */
    section[data-testid="stFileUploader"] > div {{
        background-color: #000000 !important;
        border: 3px dashed #ff0000 !important;
        border-radius: 8px;
        padding: 20px;
    }}

    section[data-testid="stFileUploader"] label {{
        color: #ffffff !important;
        font-size: calc(1rem + 2px) !important;
    }}

    section[data-testid="stFileUploader"] small {{
        color: #cccccc !important;
        font-size: calc(0.875rem + 2px) !important;
    }}

    /* Metrics styling */
    div[data-testid="stMetricValue"] {{
        color: #ffffff !important;
        font-size: calc(2rem + 2px) !important;
    }}

    div[data-testid="stMetricLabel"] {{
        color: #e0e0e0 !important;
        font-size: calc(0.875rem + 2px) !important;
    }}

    /* Alert blocks styling */
    .stAlert {{
        background-color: #2a2a2a !important;
        border: 1px solid #404040 !important;
        color: #e0e0e0 !important;
    }}

    /* Dividers */
    hr {{
        border-color: #404040 !important;
    }}

    /* Logo styling */
    .logo-container {{
        text-align: center;
        margin-bottom: 20px;
    }}

    .logo-container img {{
        max-width: 200px;
        border: 2px solid #404040;
        border-radius: 8px;
    }}
</style>
""", unsafe_allow_html=True)

# Function to fix image orientation and convert to 9:16
def fix_image_orientation_and_resize(image):
    """Fixes image orientation based on EXIF and converts to 9:16 format"""
    try:
        # Fix orientation based on EXIF data
        from PIL import ImageOps
        image = ImageOps.exif_transpose(image)

        # Target aspect ratio 9:16 (vertical format)
        target_ratio = 9 / 16
        width, height = image.size
        current_ratio = width / height

        # If image is horizontal or square, crop/resize
        if current_ratio > target_ratio:
            # Image too wide, crop sides
            new_width = int(height * target_ratio)
            left = (width - new_width) // 2
            image = image.crop((left, 0, left + new_width, height))
        elif current_ratio < target_ratio:
            # Image too tall, crop top and bottom
            new_height = int(width / target_ratio)
            top = (height - new_height) // 2
            image = image.crop((0, top, width, top + new_height))

        # Resize to standard 9:16 resolution
        # Using 1080x1920 as base size for vertical format
        target_width = 1080
        target_height = 1920
        image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)

        return image
    except Exception as e:
        st.warning(f"Failed to process image: {e}")
        return image

# Initialize Replicate API
try:
    replicate_client = replicate.Client(api_token=st.secrets["REPLICATE_API_TOKEN"])
except Exception as e:
    st.error("⚠️ Error connecting to Replicate API. Check your token in secrets.toml")
    st.stop()

# Title
st.title("🍌 Nano Banana - Image Generator")
st.markdown("### 9:16 Image Generator")
st.markdown("Upload up to 2 reference images and describe your desired result. All images will be automatically converted to vertical 9:16 format.")

# Sidebar with logo
with st.sidebar:
    # Logo (if logo.avif exists)
    try:
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        st.image("logo.avif", use_column_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    except:
        pass  # Logo not found, continue without it

    st.divider()

    if 'generated_count' in st.session_state:
        st.metric("Images Created", st.session_state['generated_count'])

# Main area - image upload
st.subheader("📤 Upload Reference Images")

col1, col2 = st.columns(2)

# Initialize image variables
image_1 = None
image_2 = None
uploaded_file_1 = None
uploaded_file_2 = None

with col1:
    uploaded_file_1 = st.file_uploader(
        "Image 1 (required)",
        type=['png', 'jpg', 'jpeg', 'webp'],
        help="Upload first reference image - will be converted to 9:16 format",
        key="uploader_1"
    )
    if uploaded_file_1 is not None:
        try:
            image_1 = Image.open(uploaded_file_1)
            # Apply orientation fix and resize
            image_1 = fix_image_orientation_and_resize(image_1)
            st.image(image_1, caption="Reference 1 (9:16)", width=300)
            # Save processed image in session_state
            buf = io.BytesIO()
            image_1.save(buf, format='PNG')
            buf.seek(0)
            st.session_state['image_1'] = buf
        except Exception as e:
            st.error(f"Error loading image 1: {e}")

with col2:
    uploaded_file_2 = st.file_uploader(
        "Image 2 (optional)",
        type=['png', 'jpg', 'jpeg', 'webp'],
        help="Upload second reference image - will be converted to 9:16 format",
        key="uploader_2"
    )
    if uploaded_file_2 is not None:
        try:
            image_2 = Image.open(uploaded_file_2)
            # Apply orientation fix and resize
            image_2 = fix_image_orientation_and_resize(image_2)
            st.image(image_2, caption="Reference 2 (9:16)", width=300)
            # Save processed image in session_state
            buf = io.BytesIO()
            image_2.save(buf, format='PNG')
            buf.seek(0)
            st.session_state['image_2'] = buf
        except Exception as e:
            st.error(f"Error loading image 2: {e}")

# Prompt
st.subheader("✍️ Describe Your Desired Result")

prompt = st.text_area(
    "Generation Prompt:",
    placeholder="Example: Make the sheets in the style of the logo. Make the scene natural.",
    height=120,
    help="Describe in detail what you want to achieve"
)

# Prompt examples
with st.expander("📝 Prompt Examples"):
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

# Apply example prompt if selected
if 'prompt_text' in st.session_state and st.session_state['prompt_text']:
    prompt = st.session_state['prompt_text']

# Generate button
st.divider()
generate_button = st.button(
    "🚀 Generate Image",
    type="primary",
    use_container_width=True,
    disabled=(image_1 is None)
)

# Generation processing
if generate_button:
    if not prompt or len(prompt.strip()) < 5:
        st.warning("⚠️ Please enter a description (minimum 5 characters)")
    elif image_1 is None:
        st.warning("⚠️ Upload at least one image")
    else:
        with st.spinner("🎨 Generating image... This may take 20-40 seconds..."):
            try:
                # Prepare input data for Replicate
                input_data = {
                    "prompt": prompt,
                    "image_input": []
                }

                # Add images to array
                if 'image_1' in st.session_state:
                    st.session_state['image_1'].seek(0)
                    input_data["image_input"].append(st.session_state['image_1'])

                if 'image_2' in st.session_state and image_2 is not None:
                    st.session_state['image_2'].seek(0)
                    input_data["image_input"].append(st.session_state['image_2'])

                # Run model on Replicate
                output = replicate_client.run(
                    "google/nano-banana",
                    input=input_data
                )

                # Process result
                # output can be URL or list of URLs
                if output:
                    generated_images = []

                    # If output is a string (single URL)
                    if isinstance(output, str):
                        output = [output]

                    # Limit to 3 images maximum
                    output = output[:3]

                    # Load images from URLs
                    for img_url in output:
                        try:
                            response = requests.get(img_url)
                            img = Image.open(io.BytesIO(response.content))
                            # Apply processing to generated images
                            img = fix_image_orientation_and_resize(img)
                            generated_images.append(img)
                        except Exception as e:
                            st.warning(f"Failed to load image: {e}")

                    if generated_images:
                        st.session_state['generated_images'] = generated_images

                        # Counter
                        if 'generated_count' not in st.session_state:
                            st.session_state['generated_count'] = 0
                        st.session_state['generated_count'] += len(generated_images)

                        st.success(f"✅ Successfully generated {len(generated_images)} image(s) in 9:16 format!")
                    else:
                        st.error("❌ Failed to get images from response")
                else:
                    st.error("❌ Model returned no result")

            except Exception as e:
                error_message = str(e)
                st.error(f"❌ Generation error: {error_message}")

                st.info("""
                **Possible error causes:**
                - Check REPLICATE_API_TOKEN is correct
                - Ensure google/nano-banana model is available
                - Check input data format (model schema)
                - API limit may be exhausted
                """)

# Display results
if 'generated_images' in st.session_state and st.session_state['generated_images']:
    st.divider()
    st.subheader("🖼️ Generated Images")
    st.markdown("**Image Format: 9:16 (1080x1920)**")

    # Display in columns (maximum 3)
    num_cols = min(len(st.session_state['generated_images']), 3)
    cols = st.columns(num_cols)

    for idx, img in enumerate(st.session_state['generated_images']):
        with cols[idx % num_cols]:
            # Display image with fixed width for 9:16 format
            st.image(img, caption=f"Result {idx + 1} (9:16)", width=300)

            # Download button
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            byte_data = buf.getvalue()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"nano_banana_9x16_{timestamp}_{idx + 1}.png"

            st.download_button(
                label="⬇️ Download PNG",
                data=byte_data,
                file_name=filename,
                mime="image/png",
                key=f"download_result_{idx}",
                use_container_width=True
            )

# Information block
with st.expander("ℹ️ How It Works"):
    st.markdown("""
    ### Generation Process:

    1. **Upload References**: You upload 1-2 images
    2. **Automatic Processing**: Images are converted to 9:16 format (1080x1920)
    3. **Orientation Fix**: EXIF data is used for proper rotation
    4. **Description**: You specify a prompt describing the desired result
    5. **Generation**: Nano Banana model processes request via Replicate API
    6. **Result**: You receive up to 3 new images in 9:16 format

    ### App Features:
    - **9:16 Format**: All images automatically converted to vertical format
    - **No Flipping**: EXIF orientation handled automatically
    - **Dark Style**: Metallic interface design
    - **Custom Font**: ArexaDemo for unique visual appeal
    - **Limitation**: Maximum 3 results for optimal viewing

    ### Model: google/nano-banana
    - Fast image generation
    - Image-to-image transformation support
    - Works via Replicate API
    """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; padding: 20px;'>
    <p style='color: #ffffff; font-size: calc(0.9rem + 2px);'>
        Powered by Google Nano Banana via Replicate | Streamlit
    </p>
    <p style='color: #cccccc; font-size: calc(0.8rem + 2px);'>
        Format: 9:16 | EXIF Auto-Correction | Metal Dark Theme
    </p>
</div>
""", unsafe_allow_html=True)
