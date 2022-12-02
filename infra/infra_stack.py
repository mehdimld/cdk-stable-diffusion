from aws_cdk import (
    aws_lambda as _lambda,
    aws_s3 as _s3,
    aws_iam as _iam,
    aws_lambda_event_sources as _lambda_event_sources,
    Duration as _Duration,
    Stack,
    aws_s3_deployment as _s3deploy,
    RemovalPolicy
)

from constructs import Construct
from resources import INPUT_AUDIO_FILES_BUCKET_NAME, OUTPUT_TRANSCRIBED_BUCKET_NAME, OUTPUT_IMAGES_BUCKET_NAME, MODEL_DATA_BUCKET_NAME, INFERENCE_SAGEMAKER_ENDPOINT_NAME

class InfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define the transcribe lambda ressource
        transcribe_audio = _lambda.Function(self, 'TranscribeAudio',
                                            function_name="TranscribeAudioStableDiffusionLambda",
                                            runtime=_lambda.Runtime.PYTHON_3_7,
                                            code=_lambda.Code.from_asset(
                                                './lambda/transcribe'),
                                            handler='transcribe.lambda_handler', 
                                            environment={"OutputBucketName": OUTPUT_TRANSCRIBED_BUCKET_NAME})

        # Define the Input S3 bucket ressource
        StableDiffusionAudioFileBucket = _s3.Bucket(self, "StableDiffusionAudioFileBucket",
                                                    bucket_name=INPUT_AUDIO_FILES_BUCKET_NAME,
                                                    block_public_access=_s3.BlockPublicAccess.BLOCK_ALL,
                                                    auto_delete_objects=True,
                                                    removal_policy=RemovalPolicy.DESTROY)
        
        StableDiffusionTranscribedFileBucket = _s3.Bucket(self, "StableDiffusionTranscribedFileBucket",
                                                    bucket_name=OUTPUT_TRANSCRIBED_BUCKET_NAME,
                                                    block_public_access=_s3.BlockPublicAccess.BLOCK_ALL,
                                                    auto_delete_objects=True,
                                                    removal_policy=RemovalPolicy.DESTROY)
        # Give lambda that launches transcribe permissions to read/write on the Input S3 bucket
        transcribe_audio.add_to_role_policy(_iam.PolicyStatement(
            effect=_iam.Effect.ALLOW,
            actions=[
                's3:PutObject',
                's3:GetObject',
            ],
            resources=[
                'arn:aws:s3:::{}/*'.format(INPUT_AUDIO_FILES_BUCKET_NAME),
                'arn:aws:s3:::{}/*'.format(OUTPUT_TRANSCRIBED_BUCKET_NAME)  
            ],
        ))

        # Give lambda lambda that launches transcribe permission to launch a transcoription job on Amazon Transcribe
        transcribe_audio.add_to_role_policy(_iam.PolicyStatement(
            effect=_iam.Effect.ALLOW,
            actions=[
                'transcribe:StartTranscriptionJob',
            ],
            resources=[
                '*',
            ],
        ))

        # Create a trigger on adding files on the input S3 bucket in the input audiofiles folder
        s3PutEventSource = _lambda_event_sources.S3EventSource(StableDiffusionAudioFileBucket,
                                                               events=[
                                                                   _s3.EventType.OBJECT_CREATED_PUT],
                                                               )

        # Attach the trigger to the lambda that launches transcribe
        transcribe_audio.add_event_source(s3PutEventSource)

        # Create s3 bucket to upload the model.
        stableDiffusionModelBucket = _s3.Bucket(self, "stableDiffusionModelBucket",
                                                bucket_name=MODEL_DATA_BUCKET_NAME,
                                                access_control=_s3.BucketAccessControl.BUCKET_OWNER_FULL_CONTROL,
                                                encryption=_s3.BucketEncryption.S3_MANAGED,
                                                block_public_access=_s3.BlockPublicAccess.BLOCK_ALL,
                                                auto_delete_objects=True,
                                                removal_policy=RemovalPolicy.DESTROY)

        # Create s3 bucket for output images
        stableDiffusionOutputImagesBucket = _s3.Bucket(self, "stableDiffusionOutputImagesBucket",
                                                       bucket_name=OUTPUT_IMAGES_BUCKET_NAME,
                                                       access_control=_s3.BucketAccessControl.BUCKET_OWNER_FULL_CONTROL,
                                                       encryption=_s3.BucketEncryption.S3_MANAGED,
                                                       block_public_access=_s3.BlockPublicAccess.BLOCK_ALL,
                                                       auto_delete_objects=True,
                                                       removal_policy=RemovalPolicy.DESTROY)
        
        stableDiffusionPredictionLambda = _lambda.DockerImageFunction(self, "stableDiffusionPredictionLambda",
                                                                      function_name="stableDiffusionPredictionLambda",
                                                                      code=_lambda.DockerImageCode.from_image_asset(
                                                                          ("./lambda/endpoint-invoke")),
                                                                      architecture=_lambda.Architecture.ARM_64,
                                                                      timeout=_Duration.seconds(
                                                                          60),
                                                                      environment={"endpoint_name": INFERENCE_SAGEMAKER_ENDPOINT_NAME, 
                                                                                    "output_bucket_name": OUTPUT_IMAGES_BUCKET_NAME})

        # Attach Policy to Lambda to Put object on the output bucket
        stableDiffusionPredictionLambda.add_to_role_policy(_iam.PolicyStatement(
            effect=_iam.Effect.ALLOW,
            actions=[
                's3:PutObject',
            ],
            resources=[
                'arn:aws:s3:::{}/*'.format(OUTPUT_IMAGES_BUCKET_NAME),
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
                'arn:aws:s3:::{}/*'.format(OUTPUT_TRANSCRIBED_BUCKET_NAME),
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
        textInputCreationEvent = _lambda_event_sources.S3EventSource(StableDiffusionTranscribedFileBucket,
                                                                     events=[
                                                                         _s3.EventType.OBJECT_CREATED_PUT],
                                                                     filters=[_s3.NotificationKeyFilter(
                                                                         suffix=".json")]
                                                                     )
        # Attach the trigger to the lambda
        stableDiffusionPredictionLambda.add_event_source(
            textInputCreationEvent)

        # Make sure the lambda function is able to access to Sagemaker endpoint.
