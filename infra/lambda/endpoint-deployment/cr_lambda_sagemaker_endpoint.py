from sagemaker.huggingface.model import HuggingFaceModel
from sagemaker.huggingface.model import HuggingFacePredictor


def clean_props(**props):
    data = {k: props[k] for k in props.keys() if k != "ServiceToken"}
    return data


def on_event(event, context):
    request_type = event["RequestType"]
    if request_type == "Create":
        return on_create(event)
    if request_type == "Update":
        return on_update(event)
    if request_type == "Delete":
        return on_delete(event)
    raise Exception("Invalid request type: %s" % request_type)

def on_create(event):
    props = clean_props(**event["ResourceProperties"])
    endpoint_name = props.get("EndpointName")
    model_data = props.get("ModelData")
    execution_role= props.get("Role")
    huggingface_model = HuggingFaceModel(
        model_data=model_data,
        role=execution_role,
        transformers_version="4.12",
        pytorch_version="1.9",
        py_version="py38",
    )

    endpoint = huggingface_model.deploy(
        initial_instance_count=1,
        instance_type="ml.g4dn.xlarge",
        endpoint_name=endpoint_name,
        )
    return {"Data": {'EndpointName':endpoint_name}}

def on_update(event):
    on_delete(event)
    return on_create(event)

def on_delete(event):
    props = clean_props(**event["ResourceProperties"])
    endpoint_name = props.get("EndpointName")    
    predictor = HuggingFacePredictor(endpoint_name=endpoint_name)
    predictor.delete_model()
    predictor.delete_endpoint()