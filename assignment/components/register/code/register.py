import argparse
import json
import os

from azure.ai.ml import MLClient
from azure.ai.ml.constants import AssetTypes
from azure.ai.ml.entities import Model
from azure.identity import DefaultAzureCredential


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model_name", type=str, required=True, help="Name for the registered model"
    )
    parser.add_argument(
        "--model_path", type=str, required=True, help="Path to the model folder"
    )
    parser.add_argument(
        "--model_type",
        type=str,
        default="custom_model",
        help="Type of model (custom_model, mlflow_model, triton_model)",
    )
    parser.add_argument(
        "--registration_details",
        type=str,
        required=True,
        help="Output folder for registration details",
    )
    args = parser.parse_args()

    print(f"Registering model: {args.model_name}")
    print(f"Model path: {args.model_path}")
    print(f"Model type: {args.model_type}")

    # Get Azure ML workspace details from environment variables
    subscription_id = os.environ.get("AZUREML_ARM_SUBSCRIPTION")
    resource_group = os.environ.get("AZUREML_ARM_RESOURCEGROUP")
    workspace_name = os.environ.get("AZUREML_ARM_WORKSPACE_NAME")

    print(f"Connecting to workspace: {workspace_name}")
    print(f"Resource group: {resource_group}")
    print(f"Subscription: {subscription_id}")

    # Create ML client using default credentials
    ml_client = MLClient(
        DefaultAzureCredential(),
        subscription_id=subscription_id,
        resource_group_name=resource_group,
        workspace_name=workspace_name,
    )

    # Map model type string to AssetTypes
    model_type_map = {
        "custom_model": AssetTypes.CUSTOM_MODEL,
        "mlflow_model": AssetTypes.MLFLOW_MODEL,
        "triton_model": AssetTypes.TRITON_MODEL,
    }

    asset_type = model_type_map.get(args.model_type, AssetTypes.CUSTOM_MODEL)

    # Create model entity
    model = Model(
        path=args.model_path,
        name=args.model_name,
        type=asset_type,
        description=f"Model registered via custom registration component",
    )

    print("Registering model...")
    registered_model = ml_client.models.create_or_update(model)

    print(f"Model registered successfully!")
    print(f"Model name: {registered_model.name}")
    print(f"Model version: {registered_model.version}")
    print(f"Model ID: {registered_model.id}")

    # Save registration details to output folder
    os.makedirs(args.registration_details, exist_ok=True)

    registration_info = {
        "name": registered_model.name,
        "version": str(registered_model.version),
        "id": registered_model.id,
        "type": args.model_type,
    }

    output_file = os.path.join(args.registration_details, "registration_details.json")
    with open(output_file, "w") as f:
        json.dump(registration_info, f, indent=2)

    print(f"Registration details saved to: {output_file}")


if __name__ == "__main__":
    main()
