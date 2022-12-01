# TechAssignment

## Description
- The lambda directory contains : 
    - a dockerfile with the base image, the packages to install, and the function handler
    - The lambda function which takes as input the event triggered by the file set to the s3 bucket.
    - The requirements
Its main role is to collect the text data of the file that has triggered it, pass them to the stable diffusion model built thanks to the sagemaker endpoint, predict images and store them in another s3 bucket.

## Temporary solution to push a new version of the lambda : 
You need to have docker and aws-cli installed with your credentials properly configured.
[This tutorial](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html) is helpful. As we've built everything in eu-west-3, below are the command we can use to deploy the new container lambda image: 
<pre><code>aws ecr get-login-password --region eu-west-3 | docker login --username AWS --password-stdin TheAWSAccountID.dkr.ecr.eu-west-3.amazonaws.com
docker build -t techassignment .
docker tag techassignment:latest TheAWSAccountID.dkr.ecr.eu-west-3.amazonaws.com/stablediffusion
docker push TheAWSAccountID.dkr.ecr.eu-west-3.amazonaws.com/stablediffusion</code></pre>
Then the docker container build locally is available on ECR and you can manually deploy a new version of the lambda throught : 
lambda >> image >> deploy new image >> select the latest image in the ecr repository named stablediffusion.

## Next steps :
- Adding the cdk stacks in the "infra" folder. The terraform part of [This tutorial](https://dev.to/aws-builders/your-own-stable-diffusion-endpoint-with-aws-sagemaker-1534) is super helpful as well as what is in the file aws-needed-resources.txt
- Adding the stable-diffusion model localy but not to the remote repository for file sizes and licensing reasons. 
- Adding the Sagemaker part : zip-model >> Create endpoint >> Use Endpoint (not sure if this one is really needed)
