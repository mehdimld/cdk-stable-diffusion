#!/usr/bin/env bash

set -e
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
REGION='eu-west-1'
MODEL_DATA_BUCKET_NAME="stable-diffusion-ml-model-bucket"
MODEL_DATA_ARCHIVE_NAME="sdv1-4_model.tar.gz"

cd ../

cp -r stable-diffusion-custom-inference/code stable-diffusion-v1-4

cd stable-diffusion-v1-4
rm model.tar.gz 2> /dev/null || true
tar cvf model.tar.gz --use-compress-program=pigz ./*
aws s3 cp model.tar.gz "s3://${MODEL_DATA_BUCKET_NAME}.${ACCOUNT_ID}.${REGION}/${MODEL_DATA_ARCHIVE_NAME}"
rm model.tar.gz

cd ../stable-diffusion-custom-inference
