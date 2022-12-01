from aws_cdk import (
    aws_lambda as _lambda,
    aws_s3 as _s3,
    aws_iam as _iam,
    aws_s3_notifications as _s3_n,
    aws_lambda_event_sources as _lambda_event_sources,
    aws_sagemaker as _sagemaker,
    Duration as _Duration,
    Stack,
    Environment,
    Fn,
    aws_s3_deployment as _s3deploy, 
    RemovalPolicy

)
from constructs import Construct


class InfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define the transcribe lambda ressource
        transcribe_audio = _lambda.Function(self, 'TranscribeAudio',
                                            function_name="TranscribeAudioStableDiffusionLambda",
                                            runtime=_lambda.Runtime.PYTHON_3_7,
                                            code=_lambda.Code.from_asset(
                                                './lambda/transcribe'),
                                            handler='transcribe.lambda_handler')

        # Define the S3 bucker ressource
        StableDiffusionAudioFileBucket = _s3.Bucket(self, "StableDiffusionAudioFileBucket",
                                                    bucket_name="stable-diffusion-audiofiles-bucket",
                                                    block_public_access=_s3.BlockPublicAccess.BLOCK_ALL, 
                                                    auto_delete_objects=True, 
                                                    removal_policy=RemovalPolicy.DESTROY)

        # Give lambda permissions to read/write on the S3 bucket
        transcribe_audio.add_to_role_policy(_iam.PolicyStatement(
            effect=_iam.Effect.ALLOW,
            actions=[
                's3:PutObject',
                's3:GetObject',
            ],
            resources=[
                'arn:aws:s3:::stable-diffusion-audiofiles-bucket/*',
            ],
        ))

        # Give lambda permission to launch a transcription job on Amazon Transcribe
        transcribe_audio.add_to_role_policy(_iam.PolicyStatement(
            effect=_iam.Effect.ALLOW,
            actions=[
                'transcribe:StartTranscriptionJob',
            ],
            resources=[
                '*',
            ],
        ))

        # Create a trigger on adding files on the S3 bucket in the input audiofiles folder
        s3PutEventSource = _lambda_event_sources.S3EventSource(StableDiffusionAudioFileBucket,
                                                               events=[
                                                                   _s3.EventType.OBJECT_CREATED_PUT],
                                                               filters=[_s3.NotificationKeyFilter(
                                                                   prefix="input-audiofiles/")]
                                                               )

        # Attach the trigger to the lambda
        transcribe_audio.add_event_source(s3PutEventSource)

        # Create s3 bucket to upload the model.
        stableDiffusionModelBucket = _s3.Bucket(self, "stableDiffusionModelBucket",
                                                bucket_name="stable-diffusion-ml-model-bucket",
                                                access_control=_s3.BucketAccessControl.BUCKET_OWNER_FULL_CONTROL,
                                                encryption=_s3.BucketEncryption.S3_MANAGED,
                                                block_public_access=_s3.BlockPublicAccess.BLOCK_ALL, 
                                                auto_delete_objects=True, 
                                                removal_policy=RemovalPolicy.DESTROY)

        # Create s3 bucket for output images
        stableDiffusionOutputImagesBucket = _s3.Bucket(self, "stableDiffusionOutputImagesBucket",
                                                       bucket_name="stable-diffusion-output-bucket",
                                                       access_control=_s3.BucketAccessControl.BUCKET_OWNER_FULL_CONTROL,
                                                       encryption=_s3.BucketEncryption.S3_MANAGED,
                                                       block_public_access=_s3.BlockPublicAccess.BLOCK_ALL, 
                                                       auto_delete_objects=True, 
                                                       removal_policy=RemovalPolicy.DESTROY)
        # Create lambda function
        ENDPOINT_NAME = 'huggingface-pytorch-inference' #Fn.import_value("HFEndpointName")
        stableDiffusionPredictionLambda = _lambda.DockerImageFunction(self, "stableDiffusionPredictionLambda",
                                                                      function_name="stableDiffusionPredictionLambda",
                                                                      code=_lambda.DockerImageCode.from_image_asset(
                                                                          ("./lambda/endpoint-invoke")),
                                                                      architecture=_lambda.Architecture.ARM_64, 
                                                                      timeout=_Duration.seconds(60), 
                                                                      environment={"endpoint_name": ENDPOINT_NAME})

        # Attach Policy to Lambda to Put object on the output bucket
        stableDiffusionPredictionLambda.add_to_role_policy(_iam.PolicyStatement(
            effect=_iam.Effect.ALLOW,
            actions=[
                's3:PutObject',
            ],
            resources=[
                'arn:aws:s3:::stable-diffusion-output-bucket/*',
            ],
        ))

        # Attach Policy to Lambda to Get object from the text input bucket
        stableDiffusionPredictionLambda.add_to_role_policy(_iam.PolicyStatement(
            effect=_iam.Effect.ALLOW,
            actions=[
                's3:PutObject',
                's3:GetObject',
            ],
            resources=[
                'arn:aws:s3:::stable-diffusion-audiofiles-bucket/*',
            ],
        ))
        stableDiffusionPredictionLambda.add_to_role_policy(_iam.PolicyStatement(
            effect=_iam.Effect.ALLOW,
            actions=[
                "sagemaker:*",
                "iam:PassRole",
                "iam:GetRole"],
            resources=[
                '*',
            ],
        ))   
        # Create the event from S3 audio bucket output prefix
        textInputCreationEvent = _lambda_event_sources.S3EventSource(StableDiffusionAudioFileBucket,
                                                                     events=[
                                                                         _s3.EventType.OBJECT_CREATED_PUT],
                                                                     filters=[_s3.NotificationKeyFilter(
                                                                         prefix="output-textfiles/")]
                                                                     )
        # Attach the trigger to the lambda
        stableDiffusionPredictionLambda.add_event_source(
            textInputCreationEvent)

        # Make sure the lambda function is able to access to Sagemaker endpoint.
