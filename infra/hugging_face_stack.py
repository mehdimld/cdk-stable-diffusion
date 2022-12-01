from aws_cdk import (
    aws_logs as logs,
    aws_lambda as _lambda,
    aws_iam as _iam,
    Duration as _Duration,
    CustomResource,
    Stack,
    Environment, 
    BundlingOptions,
    CfnOutput,
)
import os
import uuid
from sagemaker.huggingface.model import HuggingFaceModel
from sagemaker.huggingface.model import HuggingFacePredictor

from sagemaker import Session, get_execution_role
import boto3
from aws_cdk.custom_resources import (
    Provider
)

from constructs import Construct

class HuggingFaceModelEndpoint(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        iam_sagemaker_actions = [
            "sagemaker:*",
            "ecr:GetDownloadUrlForLayer",
            "ecr:BatchGetImage",
            "ecr:BatchCheckLayerAvailability",
            "ecr:GetAuthorizationToken",
            "cloudwatch:PutMetricData",
            "cloudwatch:GetMetricData",
            "cloudwatch:GetMetricStatistics",
            "cloudwatch:ListMetrics",
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:DescribeLogStreams",
            "logs:PutLogEvents",
            "logs:GetLogEvents",
            "s3:CreateBucket",
            "s3:ListBucket",
            "s3:GetBucketLocation",
            "s3:GetObject",
            "s3:PutObject",
            "iam:GetRole",
            "iam:PassRole",
        ]
        
        execution_role = _iam.Role(self, "hf_sagemaker_execution_role", assumed_by=_iam.ServicePrincipal("sagemaker.amazonaws.com"))
        execution_role.add_to_policy(_iam.PolicyStatement(resources=["*"], actions=iam_sagemaker_actions))
        
        lambda_role = _iam.Role(self, "cr_lambda_hf_execution_role", assumed_by=_iam.ServicePrincipal("lambda.amazonaws.com"))
        lambda_role.add_to_policy(_iam.PolicyStatement(resources=["*"], actions=iam_sagemaker_actions))

        huggingface_model_endpoint_handler = _lambda.DockerImageFunction(self, "HuggingFaceModelEndpointCustomResourceHandler",
                                                                      function_name="hugging_face_model_endpoint_management",
                                                                      code=_lambda.DockerImageCode.from_image_asset(
                                                                          ("./lambda/endpoint-deployment")),
                                                                      architecture=_lambda.Architecture.ARM_64, 
                                                                      description="""This Lambda function is a cloudformation custom resource provider for HuggingFace Model and Endpoint as 
                                                                      Cfn currently does not support the CreateStudioLifecycleConfig parameter""", 
                                                                      timeout=_Duration.seconds(10*60),
                                                                      role=lambda_role,
                                                                      )

        huggingface_model_endpoint_provider = Provider(self, "HuggingFaceModelEndpointProvider", 
                                              on_event_handler= huggingface_model_endpoint_handler)
        huggingface_model_endpoint = CustomResource(self, "HuggingFaceModelEndpoint", 
                                                     service_token=huggingface_model_endpoint_provider.service_token,
                                                     resource_type='Custom::HuggingFaceModelEndpoint', 
                                                     properties={
                                                        'EndpointName' : 'huggingface-pytorch-inference',
                                                        'ModelData' : f"s3://stable-diffusion-ml-model-bucket/sdv1-4_model.tar.gz",
                                                        "Role" : execution_role.role_arn
                                                     })
        CfnOutput(self, "HFEndPointName", value=huggingface_model_endpoint.get_att("EndpointName").to_string(), export_name='HFEndpointName')
