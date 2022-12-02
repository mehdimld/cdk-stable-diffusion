# Speech-to-Image Using Stable Diffusion on AWS

## Description
This project aims to deploy aws resources via cdk to have a speech-to-image application on your aws account. In order to do so the following resources are provisionned : 

## How to use this repo : 

### Requirements 

### Steps to follow : 

- First create a venv and install the requirements
- You'll need to upload the Stable Diffusion model form HuggingFace Hub (https://huggingface.co/CompVis/stable-diffusion-v1-4). For that create a free account on their website, get a token and follow the following steps: 
    git lfs install
    git clone https://huggingface.co/CompVis/stable-diffusion-v1-4
- Now you can go on with the cdk steps : 
    - cd to infra 
    - cdk bootstrap
    - cdk deploy InfraStack will deploy transcribe pipelines, all the required s3 bucket (model hosting, input audiofiles, output transcribed json, output generated html file.)
    - run the following command to upload the model you got from HuggingFace to the freshly deployed s3 bucket that hosts the : 
        - sh ../sagemaker/zip-model.sh
    - cdk deploy HuggingFaceModelEndpoint will deploy: a SageMaker HuggingFace Model and deploy it to a dedicated SageMaker Endpoint. Be aware that this deployment take about 7 minutes. 
- Your infra is not ready you can start to play with it : 
    - Go to the s3 bucket and in the input-audiofiles directory upload any .mp3 file 
    - Wait for 1-2 minutes and you'll see the output of your speech-to-image generator in the bucket named output-images-bucket. 

## Next Steps : 
- Remove zip-model.sh script and refacto to use aws-s3-assets
- Check if it works without the custom inference script
- Set up venv at the right place.
- Adding a frontend
- Serverless endpoint ?