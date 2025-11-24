# Model Registration Authorization Fix

## 🚨 Problem

Your Azure ML pipeline is failing during the model registration step with this error:

```
AuthorizationFailed: The client 'a641f312-c349-4183-b4b8-118e1ae6a645' with object id 
'ce415541-301c-4d5e-be1d-2a65a8f31fc7' does not have authorization to perform action 
'Microsoft.MachineLearningServices/workspaces/models/versions/read' over scope 
'/subscriptions/.../mlops-clean-ws/models/animal-classification'
```

## 🔍 Root Cause

The compute cluster (`warre-cluster`) is using **credential passthrough**, which means it runs with its own **managed identity**. This managed identity currently lacks the necessary permissions to:

1. **Read** existing model versions (to check for conflicts)
2. **Write** new model versions

The Azure ML Python SDK's `create_or_update()` method requires **both read and write** permissions, even when creating new models.

## ✅ Quick Fix (Recommended)

Run the provided script to grant the necessary permissions:

```bash
cd 4.0
./fix_compute_permissions.sh
```

This script will:
- ✓ Verify your Azure CLI is authenticated
- ✓ Check that the workspace and compute exist
- ✓ Find the compute cluster's managed identity
- ✓ Grant the **"AzureML Data Scientist"** role to that identity
- ✓ Display next steps

**After running the script:**
1. Wait 5-10 minutes for RBAC permissions to propagate
2. Re-run your GitHub Actions workflow
3. The model registration should now succeed

## 🛠️ Manual Fix (Alternative)

If you prefer to fix this manually via Azure Portal:

### Step 1: Navigate to Workspace IAM
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to: **Resource Groups** → `mlops-clean-rg` → `mlops-clean-ws`
3. Click **Access Control (IAM)** in the left menu

### Step 2: Add Role Assignment
1. Click **+ Add** → **Add role assignment**
2. Select role: **AzureML Data Scientist**
3. Click **Next**
4. Select: **Managed Identity**
5. Click **+ Select members**
6. Filter by: **Machine Learning Compute**
7. Select: **warre-cluster**
8. Click **Select**
9. Click **Review + assign**

### Step 3: Wait for Propagation
- RBAC changes take **5-10 minutes** to propagate
- You may need to restart the compute cluster after assignment

## 📋 What This Role Grants

The **AzureML Data Scientist** role provides:

✓ Read access to workspace resources (datasets, models, environments)  
✓ Write access to create/update models and datasets  
✓ Run experiments and pipelines  
✓ Register models  
✗ Cannot modify workspace settings  
✗ Cannot manage compute resources  
✗ Cannot manage user access  

This is the **minimum recommended role** for production ML workloads.

## 🔐 Security Best Practices

### Why Use Managed Identity?

✅ **More Secure**: No secrets stored in code or configuration  
✅ **Automatic Rotation**: Azure handles credential lifecycle  
✅ **Audit Trail**: All actions are logged with the identity  
✅ **Least Privilege**: Grant only necessary permissions  

### Alternative: Service Principal

If you cannot use managed identity, you can use a service principal:

1. Ensure your `AZURE_CREDENTIALS` GitHub secret has a service principal with "AzureML Data Scientist" role
2. The pipeline already uses this for initial setup
3. The issue is that the **component** uses credential passthrough (compute's identity)

## 🧪 Verification

After applying the fix, verify the role assignment:

```bash
# Get workspace ID
WORKSPACE_ID=$(az ml workspace show \
  --name mlops-clean-ws \
  --resource-group mlops-clean-rg \
  --query id -o tsv)

# Get compute identity
COMPUTE_IDENTITY=$(az ml compute show \
  --name warre-cluster \
  --workspace-name mlops-clean-ws \
  --resource-group mlops-clean-rg \
  --query identity.principalId -o tsv)

# List role assignments
az role assignment list \
  --assignee $COMPUTE_IDENTITY \
  --scope $WORKSPACE_ID \
  --output table
```

Expected output should include:
```
Role                      Principal
------------------------  ---------
AzureML Data Scientist    warre-cluster
```

## 🐛 Troubleshooting

### Still Getting Authorization Error After 10 Minutes?

1. **Restart the compute cluster**:
   ```bash
   az ml compute stop --name warre-cluster \
     --workspace-name mlops-clean-ws \
     --resource-group mlops-clean-rg
   
   az ml compute start --name warre-cluster \
     --workspace-name mlops-clean-ws \
     --resource-group mlops-clean-rg
   ```

2. **Verify the compute has managed identity enabled**:
   - Portal → ML Workspace → Compute → warre-cluster → Identity
   - "System assigned managed identity" should be **On**

3. **Check for Azure Policy restrictions**:
   - Your organization might block role assignments
   - Contact your Azure administrator

### Error: "Compute cluster does not have a managed identity"

The compute was created without managed identity. You need to:

1. **Recreate the compute with managed identity**:
   ```bash
   az ml compute create --name warre-cluster \
     --type amlcompute \
     --size Standard_DS3_v2 \
     --min-instances 0 \
     --max-instances 4 \
     --identity-type SystemAssigned \
     --resource-group mlops-clean-rg \
     --workspace-name mlops-clean-ws
   ```

2. Or **enable it in Azure Portal**:
   - Portal → Compute → warre-cluster → Identity
   - Turn on "System assigned managed identity"

## 📚 Additional Resources

- [Azure ML RBAC Documentation](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-assign-roles)
- [Managed Identities for Compute](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-identity-based-service-authentication)
- [Built-in Azure ML Roles](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#azureml-data-scientist)
- [Detailed Fix Guide](./docs/FIX_MODEL_REGISTRATION_PERMISSIONS.md)

## 💡 Summary

**Issue**: Compute cluster lacks permissions to register models  
**Fix**: Grant "AzureML Data Scientist" role to compute's managed identity  
**Time**: 5-10 minutes for permissions to propagate  
**Command**: `./fix_compute_permissions.sh`  

---

**Need help?** Check the [detailed documentation](./docs/FIX_MODEL_REGISTRATION_PERMISSIONS.md) or contact your Azure administrator.