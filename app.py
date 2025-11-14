import streamlit as st
import replicate
from PIL import Image
import io
from datetime import datetime
import requests

# Page configuration
st.set_page_config(
    page_title="CAT REFACER",
    page_icon="🐱",
    layout="wide"
)

# Light theme with Source Sans Pro font
st.markdown("""
<style>
    /* Import Source Sans Pro font */
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@300;400;600;700&display=swap');

    /* Main app styling - LIGHT THEME */
    .stApp {
        background: linear-gradient(135deg, #f5f5f5 0%, #ffffff 50%, #f5f5f5 100%);
        background-attachment: fixed;
        font-family: 'Source Sans Pro', sans-serif !important;
    }

    /* All text elements use Source Sans Pro */
    * {
        font-family: 'Source Sans Pro', sans-serif !important;
    }

    /* Headers styling */
    h1 {
        font-size: 3.625rem !important;
        font-weight: 700 !important;
        color: #1a1a1a !important;
    }

    h2 {
        font-size: 2.125rem !important;
        color: #2d2d2d !important;
        font-weight: 600 !important;
    }

    h3 {
        color: #404040 !important;
        font-size: 1.625rem !important;
        font-weight: 600 !important;
    }

    /* Regular text */
    p, div, span, label {
        font-size: calc(1rem + 2px) !important;
        color: #1a1a1a !important;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8f8f8 100%);
        border-right: 2px solid #e0e0e0;
    }

    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
        color: #ffffff !important;
        border: 2px solid #357abd;
        border-radius: 8px;
        font-weight: 600;
        font-size: calc(1rem + 2px) !important;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #5a9def 0%, #4a90e2 100%);
        border-color: #4a90e2;
        box-shadow: 0 4px 8px rgba(74, 144, 226, 0.3);
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
        border: 2px solid #357abd;
    }

    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #5a9def 0%, #4a90e2 100%);
        box-shadow: 0 6px 12px rgba(74, 144, 226, 0.4);
    }

    /* Text input and textarea styling */
    .stTextArea textarea, .stTextInput input {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        border: 2px solid #d0d0d0 !important;
        border-radius: 6px;
        font-size: calc(1rem + 2px) !important;
    }

    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #4a90e2 !important;
    }

    /* Placeholder text */
    .stTextArea textarea::placeholder {
        color: #888888 !important;
        opacity: 0.7;
    }

    /* File uploader */
    section[data-testid="stFileUploader"] > div {
        background-color: #f9f9f9 !important;
        border: 3px dashed #4a90e2 !important;
        border-radius: 8px;
        padding: 20px;
    }

    section[data-testid="stFileUploader"] label {
        color: #1a1a1a !important;
        font-size: calc(1rem + 2px) !important;
        font-weight: 600 !important;
    }

    section[data-testid="stFileUploader"] small {
        color: #666666 !important;
        font-size: calc(0.875rem + 2px) !important;
    }

    /* Metrics styling */
    div[data-testid="stMetricValue"] {
        color: #1a1a1a !important;
        font-size: calc(2rem + 2px) !important;
        font-weight: 700 !important;
    }

    div[data-testid="stMetricLabel"] {
        color: #404040 !important;
        font-size: calc(0.875rem + 2px) !important;
        font-weight: 600 !important;
    }

    /* Alert blocks styling */
    .stAlert {
        background-color: #f0f7ff !important;
        border: 1px solid #4a90e2 !important;
        color: #1a1a1a !important;
    }

    /* Dividers */
    hr {
        border-color: #e0e0e0 !important;
    }

    /* Logo in header */
    .header-logo {
        position: fixed;
        top: 1rem;
        left: 1rem;
        z-index: 999;
        max-width: 120px;
    }

    .header-logo img {
        width: 100%;
        height: auto;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f5f5f5;
        border-radius: 4px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Function to fix image orientation
def fix_image_orientation(image):
    """Fixes image orientation based on EXIF data"""
    try:
        from PIL import ImageOps
        return ImageOps.exif_transpose(image)
    except Exception as e:
        return image

# Function to crop image to 9:16 with custom position
def crop_to_9_16(image, crop_position='center'):
    """Crops image to 9:16 format with adjustable position"""
    target_ratio = 9 / 16
    width, height = image.size
    current_ratio = width / height

    if current_ratio > target_ratio:
        # Image too wide, crop sides
        new_width = int(height * target_ratio)
        if crop_position == 'left':
            left = 0
        elif crop_position == 'right':
            left = width - new_width
        else:  # center
            left = (width - new_width) // 2
        image = image.crop((left, 0, left + new_width, height))
    elif current_ratio < target_ratio:
        # Image too tall, crop top and bottom
        new_height = int(width / target_ratio)
        if crop_position == 'top':
            top = 0
        elif crop_position == 'bottom':
            top = height - new_height
        else:  # center
            top = (height - new_height) // 2
        image = image.crop((0, top, width, top + new_height))

    return image

# Function to resize to final dimensions
def resize_to_final(image):
    """Resizes image to 1080x1920"""
    return image.resize((1080, 1920), Image.Resampling.LANCZOS)

# Combined function for backward compatibility
def fix_image_orientation_and_resize(image, crop_position='center'):
    """Fixes orientation, crops to 9:16, and resizes"""
    image = fix_image_orientation(image)
    image = crop_to_9_16(image, crop_position)
    image = resize_to_final(image)
    return image

# Initialize Replicate API
try:
    replicate_client = replicate.Client(api_token=st.secrets["REPLICATE_API_TOKEN"])
except Exception as e:
    st.error("⚠️ Error connecting to Replicate API. Check your token in secrets.toml")
    st.stop()

# Title
st.title("🐱 CAT REFACER")
st.markdown("### AI-Powered 9:16 Image Generator")
st.markdown("Upload up to 2 reference images and describe your desired result. All images will be automatically converted to vertical 9:16 format with adjustable crop preview.")

# Sidebar
with st.sidebar:
    # Logo at the top of sidebar
    try:
        import base64
        with open('logi.png', 'rb') as f:
            logo_data = base64.b64encode(f.read()).decode()
        st.markdown(f"""
        <div style='text-align: center; margin-bottom: 20px;'>
            <img src="data:image/png;base64,{logo_data}" alt="Logo" style="max-width: 150px; width: 100%;">
        </div>
        """, unsafe_allow_html=True)
    except:
        pass  # Logo not found

# Main area - image upload
st.subheader("📤 Upload Reference Images")

col1, col2 = st.columns(2)

# Initialize image variables
image_1 = None
image_2 = None
uploaded_file_1 = None
uploaded_file_2 = None

with col1:
    st.markdown("#### Image 1 (Required)")
    uploaded_file_1 = st.file_uploader(
        "Choose first image",
        type=['png', 'jpg', 'jpeg', 'webp'],
        help="Upload first reference image - will be converted to 9:16 format",
        key="uploader_1",
        label_visibility="collapsed"
    )
    if uploaded_file_1 is not None:
        try:
            image_1 = Image.open(uploaded_file_1)
            image_1 = fix_image_orientation(image_1)

            # Crop position selector
            st.markdown("**Crop Position:**")
            width, height = image_1.size
            target_ratio = 9 / 16
            current_ratio = width / height

            if current_ratio > target_ratio:
                crop_pos_1 = st.radio(
                    "Horizontal crop alignment",
                    options=['left', 'center', 'right'],
                    index=1,
                    key="crop_pos_1",
                    horizontal=True
                )
            elif current_ratio < target_ratio:
                crop_pos_1 = st.radio(
                    "Vertical crop alignment",
                    options=['top', 'center', 'bottom'],
                    index=1,
                    key="crop_pos_1",
                    horizontal=True
                )
            else:
                crop_pos_1 = 'center'

            # Apply crop and show preview
            cropped_1 = crop_to_9_16(image_1.copy(), crop_pos_1)
            st.image(cropped_1, caption="Crop Preview (9:16)", use_column_width=True)

            # Save processed image
            final_image_1 = resize_to_final(cropped_1)
            buf = io.BytesIO()
            final_image_1.save(buf, format='PNG')
            buf.seek(0)
            st.session_state['image_1'] = buf

        except Exception as e:
            st.error(f"Error loading image 1: {e}")

with col2:
    st.markdown("#### Image 2 (Optional)")
    uploaded_file_2 = st.file_uploader(
        "Choose second image",
        type=['png', 'jpg', 'jpeg', 'webp'],
        help="Upload second reference image - will be converted to 9:16 format",
        key="uploader_2",
        label_visibility="collapsed"
    )
    if uploaded_file_2 is not None:
        try:
            image_2 = Image.open(uploaded_file_2)
            image_2 = fix_image_orientation(image_2)

            # Crop position selector
            st.markdown("**Crop Position:**")
            width, height = image_2.size
            target_ratio = 9 / 16
            current_ratio = width / height

            if current_ratio > target_ratio:
                crop_pos_2 = st.radio(
                    "Horizontal crop alignment",
                    options=['left', 'center', 'right'],
                    index=1,
                    key="crop_pos_2",
                    horizontal=True
                )
            elif current_ratio < target_ratio:
                crop_pos_2 = st.radio(
                    "Vertical crop alignment",
                    options=['top', 'center', 'bottom'],
                    index=1,
                    key="crop_pos_2",
                    horizontal=True
                )
            else:
                crop_pos_2 = 'center'

            # Apply crop and show preview
            cropped_2 = crop_to_9_16(image_2.copy(), crop_pos_2)
            st.image(cropped_2, caption="Crop Preview (9:16)", use_column_width=True)

            # Save processed image
            final_image_2 = resize_to_final(cropped_2)
            buf = io.BytesIO()
            final_image_2.save(buf, format='PNG')
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

    1. **Upload References**: Upload 1-2 images
    2. **Adjust Crop**: Use the interactive crop position controls to preview and adjust how your image will be cropped to 9:16 format
    3. **EXIF Fix**: Orientation is automatically corrected based on image metadata
    4. **Write Prompt**: Describe the desired transformation or style
    5. **AI Generation**: Nano Banana model processes your request via Replicate API
    6. **Download**: Receive up to 3 new images in perfect 9:16 format

    ### App Features:
    - **Interactive Crop Preview**: See exactly how your image will be cropped before generation
    - **9:16 Format**: Perfect for Instagram Stories, TikTok, and vertical social media
    - **EXIF Auto-Correction**: No more sideways or upside-down images
    - **Light Theme**: Clean, modern interface with Source Sans Pro font
    - **AI-Powered**: Advanced image-to-image transformation

    ### Model: google/nano-banana
    - Fast image generation
    - High-quality image-to-image transformations
    - Works via Replicate API
    """)

# ============================================================================
# WAN VIDEO GENERATION SECTION
# ============================================================================
st.divider()
st.header("🎬 Image-to-Video Generation")
st.markdown("Transform your static images into dynamic videos using AI-powered motion.")

wan_col1, wan_col2 = st.columns([1, 1])

with wan_col1:
    st.subheader("📷 Input Image")

    wan_image_source = st.radio(
        "Choose image source:",
        options=["Upload new image", "Use generated image from above"],
        key="wan_image_source"
    )

    wan_input_image = None

    if wan_image_source == "Upload new image":
        wan_uploaded = st.file_uploader(
            "Upload image for video generation",
            type=['png', 'jpg', 'jpeg', 'webp'],
            key="wan_uploader"
        )
        if wan_uploaded is not None:
            wan_input_image = Image.open(wan_uploaded)
            st.image(wan_input_image, caption="Input for video", use_column_width=True)

            # Save to session state
            buf = io.BytesIO()
            wan_input_image.save(buf, format='PNG')
            buf.seek(0)
            st.session_state['wan_input_image'] = buf
    else:
        if 'generated_images' in st.session_state and st.session_state['generated_images']:
            selected_idx = st.selectbox(
                "Select generated image:",
                options=range(len(st.session_state['generated_images'])),
                format_func=lambda x: f"Result {x + 1}"
            )
            wan_input_image = st.session_state['generated_images'][selected_idx]
            st.image(wan_input_image, caption=f"Result {selected_idx + 1}", use_column_width=True)

            # Save to session state
            buf = io.BytesIO()
            wan_input_image.save(buf, format='PNG')
            buf.seek(0)
            st.session_state['wan_input_image'] = buf
        else:
            st.info("No generated images available. Please generate images first or upload a new one.")

with wan_col2:
    st.subheader("✍️ Motion Prompt")

    # WAN prompt examples
    with st.expander("📝 Motion Prompt Examples"):
        wan_examples = [
            "The camera slowly zooms in, capturing gentle movements and atmospheric details",
            "Smooth pan from left to right, revealing the scene gradually",
            "Subtle movements - hair flowing in the wind, leaves rustling",
            "Dynamic camera push-in with dramatic lighting changes",
            "Circular camera movement around the subject with soft focus"
        ]
        for idx, example in enumerate(wan_examples):
            if st.button(example, key=f"wan_example_{idx}"):
                st.session_state['wan_prompt_value'] = example
                st.rerun()

    # Get default value from session state if available
    default_wan_prompt = st.session_state.get('wan_prompt_value', '')

    wan_prompt = st.text_area(
        "Describe the desired motion:",
        value=default_wan_prompt,
        placeholder="Example: Close-up shot of an elderly sailor wearing a yellow raincoat, seated on the deck of a catamaran, slowly puffing on a pipe...",
        height=150,
        key="wan_prompt",
        help="Describe the motion, camera movement, and atmosphere you want in the video"
    )

# Generate video button
wan_generate_button = st.button(
    "🎥 Generate Video",
    type="primary",
    use_container_width=True,
    disabled=(wan_input_image is None),
    key="wan_generate"
)

if wan_generate_button:
    if not wan_prompt or len(wan_prompt.strip()) < 10:
        st.warning("⚠️ Please enter a motion description (minimum 10 characters)")
    elif wan_input_image is None:
        st.warning("⚠️ Please select or upload an image")
    else:
        with st.spinner("🎬 Generating video... This may take 60-120 seconds..."):
            try:
                # Prepare input for WAN
                st.session_state['wan_input_image'].seek(0)

                input_data = {
                    "image": st.session_state['wan_input_image'],
                    "prompt": wan_prompt
                }

                # Run WAN model
                output = replicate_client.run(
                    "wan-video/wan-2.2-i2v-fast",
                    input=input_data
                )

                if output:
                    # Handle different output types
                    if isinstance(output, str):
                        # Output is URL, download the video
                        video_response = requests.get(output)
                        video_data = video_response.content
                    else:
                        # Output is FileOutput object, read it
                        try:
                            video_data = output.read()
                        except AttributeError:
                            # Try to get URL from output
                            video_url = str(output)
                            video_response = requests.get(video_url)
                            video_data = video_response.content

                    st.session_state['wan_video'] = video_data

                    # Update counter
                    if 'video_count' not in st.session_state:
                        st.session_state['video_count'] = 0
                    st.session_state['video_count'] += 1

                    st.success("✅ Video generated successfully!")
                else:
                    st.error("❌ Failed to generate video")

            except Exception as e:
                st.error(f"❌ Video generation error: {str(e)}")
                st.info("""
                **Possible causes:**
                - Check REPLICATE_API_TOKEN
                - Ensure wan-video/wan-2.2-i2v-fast model is available
                - Check API limits
                """)

# Display generated video
if 'wan_video' in st.session_state and st.session_state['wan_video']:
    st.divider()
    st.subheader("🎥 Generated Video")

    video_col1, video_col2 = st.columns([2, 1])

    with video_col1:
        st.video(st.session_state['wan_video'])

    with video_col2:
        st.markdown("### 📥 Download")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="⬇️ Download Video (MP4)",
            data=st.session_state['wan_video'],
            file_name=f"wan_video_{timestamp}.mp4",
            mime="video/mp4",
            use_container_width=True
        )

        if 'video_count' in st.session_state:
            st.metric("Videos Generated", st.session_state['video_count'])

# ============================================================================
# TTM MOTION CONTROL SECTION
# ============================================================================
st.divider()
st.header("🎯 TTM Motion Control")
st.markdown("Advanced motion control for video generation using Time-to-Move technique.")

with st.expander("ℹ️ About TTM (Time-to-Move)"):
    st.markdown("""
    ### What is TTM?

    **Time-to-Move** is a training-free motion control technique that can be integrated into any image-to-video model.

    ### Key Features:
    - **Dual-Clock Denoising**: Precise control over when different regions start moving
    - **Plug-and-Play**: Works with WAN 2.2, CogVideoX, and Stable Video Diffusion
    - **No Training Required**: Apply motion control without model retraining

    ### How It Works:
    TTM uses two hyperparameters:
    - **tweak-index** (0-10): Controls motion timing
    - **tstrong-index** (0-10): Controls motion strength

    ### GitHub Repository:
    [time-to-move/TTM](https://github.com/time-to-move/TTM)
    """)

ttm_col1, ttm_col2 = st.columns([1, 1])

with ttm_col1:
    st.subheader("⚙️ TTM Parameters")

    ttm_tweak = st.slider(
        "Tweak Index",
        min_value=0,
        max_value=10,
        value=3,
        help="Controls when motion begins (0-10)"
    )

    ttm_tstrong = st.slider(
        "Strong Index",
        min_value=0,
        max_value=10,
        value=7,
        help="Controls motion strength (0-10)"
    )

    st.info(f"""
    **Current Settings:**
    - Tweak Index: {ttm_tweak}
    - Strong Index: {ttm_tstrong}

    These parameters control the dual-clock denoising process for precise motion control.
    """)

with ttm_col2:
    st.subheader("📝 Implementation Notes")

    st.markdown("""
    ### Integration Status:

    TTM is a Python-based technique that requires:
    - PyTorch installation
    - GUI tools for cut-and-drag motion
    - Integration with video generation models

    ### Next Steps:
    To fully implement TTM, you would need to:
    1. Set up a Python backend service
    2. Install TTM dependencies
    3. Create motion masks using the GUI tool
    4. Process videos with TTM parameters

    ### Current Implementation:
    This section demonstrates the TTM parameter controls. Full implementation requires backend setup with the TTM repository.

    **GitHub**: [time-to-move/TTM](https://github.com/time-to-move/TTM)
    """)

st.info("""
💡 **Note**: Full TTM integration requires a Python backend with PyTorch.
The current interface demonstrates the parameter controls that would be used with TTM.
For production use, consider deploying TTM as a separate service and calling it via API.
""")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; padding: 20px;'>
    <p style='color: #1a1a1a; font-size: calc(0.9rem + 2px); font-weight: 600;'>
        🐱 CAT REFACER - Powered by Google Nano Banana & WAN Video via Replicate
    </p>
    <p style='color: #666666; font-size: calc(0.8rem + 2px);'>
        Image Generation: 9:16 Format | Video Generation: WAN 2.2 | Motion Control: TTM
    </p>
</div>
""", unsafe_allow_html=True)
