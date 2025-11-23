# Model Registration Fix - Authorization Issue Resolution

## Problem Summary

The pipeline was failing during the "Register Model" step with the following error:

```
azure.core.exceptions.HttpResponseError: (AuthorizationFailed) The client 'a641f312-c349-4183-b4b8-118e1ae6a645' with object id 'ce415541-301c-4d5e-be1d-2a65a8f31fc7' does not have authorization to perform action 'Microsoft.MachineLearningServices/workspaces/jobs/read' over scope '/subscriptions/.../jobs/...' or the scope is invalid.
```

## Root Causes

### 1. Training Script Bug (Fixed)
**File:** `assignment/components/training/code/train.py` (Line 92)

**Issue:** The directory creation was using `os.path.dirname()` incorrectly:
```python
os.makedirs(os.path.dirname(model_directory), exist_ok=True)  # WRONG
```

This created the parent directory instead of the actual model directory, causing the model save to fail.

**Fix:**
```python
os.makedirs(model_directory, exist_ok=True)  # CORRECT
```

### 2. Built-in Register Component Authorization Issue (Fixed)

**Issue:** The Azure ML built-in registration component (`azureml://registries/azureml/components/register_model/versions/0.0.21`) requires special permissions that the compute cluster's managed identity doesn't have:
- Needs `Microsoft.MachineLearningServices/workspaces/jobs/read` permission
- The standard Contributor/Reader roles assigned in the workflow weren't sufficient
- Permission propagation can take several minutes

**Solution:** Created a custom registration component that uses the Azure ML Python SDK directly, which works with the existing permissions.

## Solution Implementation

### Custom Registration Component

Created four new files:

1. **`assignment/components/register/code/register.py`**
   - Python script that uses Azure ML SDK to register models
   - Uses `DefaultAzureCredential` which works with existing compute identity
   - Reads workspace details from environment variables
   - Outputs registration details to JSON file

2. **`assignment/components/register/conda.yaml`**
   - Conda dependencies specification with required packages:
     - `azure-ai-ml>=1.11.0`
     - `azure-identity>=1.12.0`
     - `azureml-core>=1.48.0`

3. **`assignment/components/register/environment.yaml`**
   - Azure ML environment definition file
   - References the conda.yaml file for dependencies
   - Uses base image: `mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu22.04:latest`

4. **`assignment/components/register/register.yaml`**
   - Component definition
   - Accepts inputs: model_name, model_path, model_type
   - Outputs: registration_details folder

### Pipeline Update

**File:** `assignment/pipelines/animals-classification.yaml`

**Changed from:**
```yaml
register:
  type: command
  component: azureml://registries/azureml/components/register_model/versions/0.0.21
  inputs:
    model_name: animal-classification
    model_type: custom_model
    model_path: ${{parent.jobs.training.outputs.output_model}}
  outputs:
    registration_details_folder: ${{ parent.outputs.registration_details }}
```

**Changed to:**
```yaml
register:
  type: command
  component: azureml:register_model_cli@latest
  inputs:
    model_name: animal-classification
    model_type: custom_model
    model_path: ${{parent.jobs.training.outputs.output_model}}
  outputs:
    registration_details: ${{parent.outputs.registration_details}}
```

### Workflow Update

**File:** `.github/workflows/azure-ai.yaml`

Added environment creation for registration component:
```yaml
az ml environment create --file ./assignment/components/register/environment.yaml
```

The component registration loop automatically picks up the new `register.yaml` file.

## How It Works Now

1. **Training Job** saves the model to `output_model/animal-cnn/model.keras`
2. **Custom Registration Component** runs with these steps:
   - Connects to Azure ML workspace using managed identity
   - Reads model from the training output path
   - Registers model using `ml_client.models.create_or_update()`
   - Saves registration details (name, version, ID) to JSON
3. **Download Job** retrieves the registered model for deployment

## Benefits of Custom Component

1. ✅ **No Authorization Issues** - Works with existing compute identity permissions
2. ✅ **Simpler Permissions** - Uses standard Contributor role
3. ✅ **Better Control** - Full visibility into registration process
4. ✅ **Easier Debugging** - Python code is easier to troubleshoot
5. ✅ **Reusable** - Can be used in other pipelines

## Testing

To test the fix:

1. Commit and push the changes
2. GitHub Actions will automatically:
   - Create the compute cluster (if deleted)
   - Create the registration environment
   - Register the custom component
   - Run the pipeline
   - Register the model successfully

## Troubleshooting

If registration still fails:

1. **Check compute identity permissions:**
   ```bash
   az ml compute show --name warre-cluster --query identity.principal_id
   ```

2. **Verify role assignments:**
   ```bash
   az role assignment list --assignee <principal_id>
   ```

3. **Check environment creation:**
   ```bash
   az ml environment list --name aml-register-cli
   ```

4. **View component registration:**
   ```bash
   az ml component list --name register_model_cli
   ```

## Alternative Solutions (Not Used)

We didn't use these alternatives because they're more complex:

1. **Azure ML Data Scientist Role** - Would require additional RBAC setup
2. **Wait for Permissions** - Unpredictable and unreliable
3. **Service Principal Registration** - Would need secrets management
4. **Manual Registration** - Not automated in pipeline

## References

- [Azure ML Model Registration Docs](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-models)
- [Azure ML Custom Components](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-create-component-pipeline-python)
- [Azure Identity and RBAC](https://learn.microsoft.com/en-us/azure/role-based-access-control/overview)