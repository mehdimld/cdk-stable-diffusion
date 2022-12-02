import io
import base64

import PIL
import torch
from diffusers import StableDiffusionPipeline


def model_fn(model_dir):
    # Load stable diffusion and move it to the GPU
    pipe = StableDiffusionPipeline.from_pretrained(model_dir, torch_dtype=torch.float16, revision="fp16")
    pipe = pipe.to("cuda")
    return pipe

def predict_fn(data, pipe):
    # get prompt & parameters
    prompt = data.pop("prompt", data)
    
    # Generate image thanks to pipe. Can set up HP here. 
    print(f'Starting inference with prompt: {prompt}')
    image: PIL.Image.Image = pipe(prompt).images[0]

    buffered = io.BytesIO()
    image.save(buffered, format='JPEG')
    return {'data': base64.b64encode(buffered.getvalue()).decode('utf-8'), 'prompt': prompt}
