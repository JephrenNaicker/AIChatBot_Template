import streamlit as st
from controllers.image_controller import ImageController
from io import BytesIO
from config import IMAGE_STUDIO_CONFIG  # Import the config


async def image_studio_page():
    st.title("🎨 Image Studio")
    st.markdown("Generate images using Stable Diffusion")

    # Initialize controller in session state if not exists
    if 'image_controller' not in st.session_state:
        st.session_state.image_controller = ImageController()

    # API Configuration
    with st.expander("⚙️ API Configuration", expanded=True):
        api_url = st.text_input(
            "Stable Diffusion API URL",
            value=IMAGE_STUDIO_CONFIG["default_api_url"],
            help="URL of your Automatic1111 Stable Diffusion WebUI API"
        )
        if st.button("Update API Connection"):
            st.session_state.image_controller.set_api_url(api_url)
            st.success("API URL updated!")

    # Generation parameters
    col1, col2 = st.columns(2)

    with col1:
        prompt = st.text_area(
            "Prompt",
            height=100,
            placeholder="Describe what you want to generate...",
            help="Positive prompt for image generation"
        )

        negative_prompt = st.text_area(
            "Negative Prompt",
            value=IMAGE_STUDIO_CONFIG["default_negative_prompt"],  # Use default from config
            height=100,
            help="Negative prompt to exclude elements from the image"
        )

    with col2:
        steps = st.slider("Steps", min_value=1, max_value=150, value=20)
        cfg_scale = st.slider("CFG Scale", min_value=1.0, max_value=30.0, value=7.0)
        width = st.slider("Width", min_value=64, max_value=1024, value=512, step=64)
        height = st.slider("Height", min_value=64, max_value=1024, value=512, step=64)
        sampler = st.selectbox(
            "Sampler",
            options=st.session_state.image_controller.available_samplers,
            index=0
        )

    # Generate button
    if st.button("✨ Generate Image", type="primary", use_container_width=True):
        if not prompt:
            st.error("Please enter a prompt!")
        else:
            with st.spinner("Generating image..."):
                image, error = st.session_state.image_controller.generate_image(
                    prompt, negative_prompt, steps, cfg_scale, width, height, sampler
                )

                if error:
                    st.error(f"Generation failed: {error}")
                else:
                    st.session_state.generated_image = image
                    st.success("Image generated successfully!")

    # Display generated image
    if 'generated_image' in st.session_state and st.session_state.generated_image:
        st.image(st.session_state.generated_image, caption="Generated Image", use_column_width=True)

        # Download button
        buf = BytesIO()
        st.session_state.generated_image.save(buf, format="PNG")
        byte_im = buf.getvalue()

        st.download_button(
            label="Download Image",
            data=byte_im,
            file_name="generated_image.png",
            mime="image/png",
            use_container_width=True
        )