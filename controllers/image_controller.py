# controllers/image_controller.py (enhanced)
import requests
import io
from PIL import Image
import base64


class ImageController:
    def __init__(self, default_url="http://127.0.0.1:7860"):
        self.api_url = f"{default_url}/sdapi/v1/txt2img"
        self.available_samplers = ["Euler a", "Euler", "LMS", "Heun", "DPM2", "DPM2 a", "DPM++ 2S a",
                                   "DPM++ 2M", "DPM++ SDE", "DPM++ 2M SDE", "DPM fast", "DPM adaptive",
                                   "LMS Karras", "DPM2 Karras", "DPM2 a Karras", "DPM++ 2S a Karras",
                                   "DPM++ 2M Karras", "DPM++ SDE Karras", "DPM++ 2M SDE Karras", "DDIM", "PLMS"]
        self.available_models = []  # Will be populated from API

    def set_api_url(self, url):
        """Update the API URL for Stable Diffusion"""
        self.api_url = f"{url}/sdapi/v1/txt2img"

    def get_available_models(self):
        """Fetch available models from the API"""
        try:
            options_url = self.api_url.replace("/txt2img", "/options")
            response = requests.get(options_url)
            if response.status_code == 200:
                options = response.json()
                return [options.get("sd_model_checkpoint", "Default Model")]
        except:
            pass
        return ["Default Model"]

    def generate_image(self, prompt, negative_prompt="", steps=20, cfg_scale=7, width=512, height=512,
                       sampler="Euler a", model=None):
        """Generate an image using Stable Diffusion API"""
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "width": width,
            "height": height,
            "sampler_name": sampler
        }

        try:
            response = requests.post(url=self.api_url, json=payload)
            if response.status_code == 200:
                r = response.json()
                image_data = r['images'][0]
                image = Image.open(io.BytesIO(base64.b64decode(image_data.split(",", 1)[0])))
                return image, None
            else:
                return None, f"API Error: {response.status_code}"
        except Exception as e:
            return None, f"Connection Error: {str(e)}"

    def generate_avatar(self, character_name, appearance_desc, style="anime style"):
        """Generate avatar specifically for character with optimized settings"""
        # Optimized prompt for avatar generation
        prompt = f"headshot portrait of {character_name}, {appearance_desc}, {style}, beautiful detailed eyes, face focus, cute, masterpiece, best quality"

        # Negative prompt to avoid common issues
        negative_prompt = "ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, deformed, blurry, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck"

        # Avatar-optimized settings
        return self.generate_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            steps=25,
            cfg_scale=7,
            width=512,  # Good size for avatars
            height=512,
            sampler="DPM++ 2M Karras"  # Good for portraits
        )