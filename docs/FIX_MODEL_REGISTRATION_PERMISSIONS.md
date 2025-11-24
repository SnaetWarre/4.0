# Fixing Model Registration Permission Issues

## Problem

The model registration component fails with the following error:

```
AuthorizationFailed: The client does not have authorization to perform action 
'Microsoft.MachineLearningServices/workspaces/models/versions/read' over scope
```

## Root Cause

The Azure Machine Learning compute cluster's **managed identity** lacks sufficient permissions to register models. The Azure ML Python SDK's `create_or_update` method requires **read permissions** on existing models to check for conflicts before creating new versions.

## Solution Options

### Option 1: Grant Compute Identity Proper RBAC Role (Recommended)

This is the cleanest and most secure solution.

#### Steps:

1. **Identify the Compute Identity**
   - Go to Azure Portal → Your ML Workspace → Compute → Select your compute cluster
   - Note the managed identity (or enable system-assigned managed identity if not enabled)

2. **Assign the Role**

   Using Azure CLI:
   ```bash
   # Get the compute identity's principal ID
   COMPUTE_IDENTITY=$(az ml compute show \
     --name warre-cluster \
     --workspace-name mlops-clean-ws \
     --resource-group mlops-clean-rg \
     --query identity.principal_id -o tsv)

   # Get the workspace ID
   WORKSPACE_ID=$(az ml workspace show \
     --name mlops-clean-ws \
     --resource-group mlops-clean-rg \
     --query id -o tsv)

   # Assign the AzureML Data Scientist role
   az role assignment create \
     --assignee $COMPUTE_IDENTITY \
     --role "AzureML Data Scientist" \
     --scope $WORKSPACE_ID
   ```

   Using Azure Portal:
   - Navigate to: ML Workspace → Access Control (IAM) → Add role assignment
   - Role: **AzureML Data Scientist** or **Azure Machine Learning Workspace Contributor**
   - Assign access to: **Managed Identity**
   - Members: Select your compute cluster's managed identity
   - Click **Review + assign**

3. **Wait for Propagation**
   - RBAC changes can take 5-10 minutes to propagate
   - You may need to restart your compute cluster

### Option 2: Use Service Principal with Proper Permissions

Instead of relying on the compute's managed identity, pass credentials explicitly.

1. **Create/Update GitHub Secret** with service principal that has proper permissions:
   ```json
   {
     "clientId": "xxx",
     "clientSecret": "xxx",
     "tenantId": "xxx",
     "subscriptionId": "xxx"
   }
   ```

2. **Ensure the service principal has the "AzureML Data Scientist" role** on the workspace

3. **Modify the component** to use the service principal instead of DefaultAzureCredential

### Option 3: Custom Role with Minimal Permissions

If you want fine-grained control:

```bash
# Create custom role definition
cat > custom-role.json <<EOF
{
  "Name": "ML Model Registrar",
  "Description": "Can register and read ML models",
  "Actions": [
    "Microsoft.MachineLearningServices/workspaces/models/read",
    "Microsoft.MachineLearningServices/workspaces/models/write",
    "Microsoft.MachineLearningServices/workspaces/models/versions/read",
    "Microsoft.MachineLearningServices/workspaces/models/versions/write"
  ],
  "AssignableScopes": [
    "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/mlops-clean-rg/providers/Microsoft.MachineLearningServices/workspaces/mlops-clean-ws"
  ]
}
EOF

# Create the role
az role definition create --role-definition custom-role.json

# Assign it to the compute identity
az role assignment create \
  --assignee $COMPUTE_IDENTITY \
  --role "ML Model Registrar" \
  --scope $WORKSPACE_ID
```

## Verification

After applying the fix, verify permissions:

```bash
# Check role assignments for the compute identity
az role assignment list \
  --assignee $COMPUTE_IDENTITY \
  --scope $WORKSPACE_ID \
  --output table
```

## Alternative: Modify Pipeline to Skip Credential Passthrough

If you cannot modify RBAC permissions, you can modify the pipeline to NOT use credential passthrough and instead use the pipeline's service principal:

In your component YAML, ensure:
```yaml
# Remove or set to false
resources:
  instance_count: 1
# Do NOT enable credential_passthrough
```

Then authenticate using environment variables passed from the pipeline.

## References

- [Azure ML RBAC Documentation](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-assign-roles)
- [Managed Identity for Compute](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-identity-based-service-authentication)
- [Built-in Roles for Azure ML](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#azureml-data-scientist)