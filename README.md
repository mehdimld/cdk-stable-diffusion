# Speech-to-Image Using Stable Diffusion on AWS

## Description
This project aims to deploy aws resources via cdk to have a speech-to-image application on your aws account. In order to do so the following resources are provisionned : 
- A bucket where you can upload your .mp3 files. (audio-files-input-bucket)
- A lambda function that can start transcribtion jobs from Amazon Transcribe as soon as a file is created in the audiofiles-input-bucket
- A bucket where the transcribtion lambda put the output of the job (a json file containing the transcribed text)
- A bucket where the Stable Diffusion Model is uploaded.
- A SageMaker model built on top of the Stable Diffusion Model artifacts uploaded. 
- A SageMaker Endpoint with an g4dn.xlarge underlying instance size that hosts the SageMaker model
- A lambda that is triggered by a json object creation in the transcribed-output-bucket. This lambda is able to invoke the previously deployed SageMaker endpoint and pass the transcribtion as input of the Stable Diffusion Model. 

## How to use this repo : 

### Requirements:
- pip & Python3 installed
### Steps to follow : 
- First step is to clone this repo.
- You'll need to upload the Stable Diffusion model from HuggingFace Hub (https://huggingface.co/CompVis/stable-diffusion-v1-4). 
For that create a free account on their website, get a token and back to your local repo execute the following commands: 

```
git lfs install
git clone https://huggingface.co/CompVis/stable-diffusion-v1-4 > stable-diffusion-v1-4
```

- (Create a venv and install the requirements, not sure if it's needed with cdk bootstrap, have to check!). For that run the following commands : 
```
cd infra
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
- Now you can go on with the cdk steps. Run the following commands: 
```
cd infra
cdk bootstrap
cdk deploy InfraStack
sh ../stable-diffusion-custom-inference/upload-model.sh
cdk deploy HuggingFaceModelEndpoint
```

Some info related to these commands: 
- cdk deploy InfraStack will deploy transcribe pipelines, all the required s3 bucket (model hosting, input audiofiles, output transcribed json, output generated html file.)
- The script upload-model.sh uploads the model you got from HuggingFace to the freshly deployed s3 bucket. Be aware that you're uploading 4.3 GB of data so it may takes some times. 
- cdk deploy HuggingFaceModelEndpoint will deploy: a SageMaker HuggingFace Model and deploy it to a dedicated SageMaker Endpoint. Be aware that this deployment take about 7 minutes. 

Your infrastructure is now ready you can start to play with it : 
- Upload any .mp3 file to the input-audiofiles-bucket
- Wait for 1-2 minutes and you'll see the output of your speech-to-image generator in the bucket named output-images-bucket. 
    
## Next Steps : 
- Adding a frontend. 
- Exploring Serverless endpoint ? For now not possible because of GPU Inference. 
- Custom resources for the s3 bucket that hosts model data ? 
- The diffusers may soon be accessible in SageMaker directly from the HuggingFace Hub. So that you can create HuggingFaceModel object with the sagemaker sdk just by providing the HF_TASK, HF_MODEL_ID and your HF_TOKEN. When available we would no longer need to create the model from data uploaded to s3.

## Other information: 
- The default region for deploying the aws resources in these repo is eu-west-1. Be aware that the default quota for gd4n.xlarge instances are not the same across regions, so it may requires you to request the support for a quota increase in sagemaker endpoint instance of size gd4n.xlarge 
