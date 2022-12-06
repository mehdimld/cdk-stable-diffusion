#!/usr/bin/env python3
import os

import aws_cdk as cdk

from infra_stack import InfraStack
from hugging_face_stack import HuggingFaceModelEndpoint
from resources import REGION
app = cdk.App()
InfraStack(app, "InfraStack",env=cdk.Environment(region=REGION))
HuggingFaceModelEndpoint(app, "HuggingFaceModelEndpoint", env=cdk.Environment(region='eu-west-1'))

app.synth()
