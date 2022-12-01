#!/usr/bin/env python3
import os

import aws_cdk as cdk

from infra_stack import InfraStack
from cr_sagemaker_endpoint import HuggingFaceModelEndpoint

app = cdk.App()
InfraStack(app, "InfraStack",env=cdk.Environment(region='eu-west-1'))
HuggingFaceModelEndpoint(app, "HuggingFaceModelEndpoint", env=cdk.Environment(region='eu-west-1'))

app.synth()
