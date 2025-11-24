# Answers for MLOps Automation Assignment

## QUESTION 1 - Check latest versions

In the assignment you checked which versions were the latest, make sure to also update the versions in your pipeline here.

**ANSWER 1 - Check latest versions**

- `azcli` — Current version: `2.64.0`
- `Azure/CLI` — Current version: `v2.1.0` (Latest major version v2)
- `actions/checkout` — Current version: `v4`
- `actions/upload-artifact` — Current version: `v4.3.3`
- `actions/download-artifact` — Current version: `v4.1.7`
- `docker/metadata-action` — Current version: `v5.5.1`
- `docker/login-action` — Current version: `v3.2.0`
- `docker/build-push-action` — Current version: `v5.3.0`

All versions have been verified and updated in the pipeline to use the latest stable releases.

---

## QUESTION 2 - Robust Pipelines: Compute - *Extra*

*‼️ Answer this question when you've gone through the complete pipeline*

Provide a better solution using checks and if-statements.

**ANSWER 2 - Robust Pipelines: Compute - *Extra***

```yaml
      - name: Azure -- Start Compute
        uses: Azure/CLI@v2.1.0
        env:
          AZURE_CONFIG_DIR: ${{ env.AZURE_CONFIG_DIR }}
        with:
          azcliversion: 2.64.0
          inlineScript: |
            export AZURE_CONFIG_DIR="$AZURE_CONFIG_DIR"
            CREDS='${{ secrets.AZURE_CREDENTIALS }}'
            CLIENT_ID=$(python3 -c "import sys, json; print(json.load(sys.stdin)['clientId'])" <<< "$CREDS")
            CLIENT_SECRET=$(python3 -c "import sys, json; print(json.load(sys.stdin)['clientSecret'])" <<< "$CREDS")
            TENANT_ID=$(python3 -c "import sys, json; print(json.load(sys.stdin)['tenantId'])" <<< "$CREDS")
            SUB_ID=$(python3 -c "import sys, json; print(json.load(sys.stdin)['subscriptionId'])" <<< "$CREDS")
            az login --service-principal -u "$CLIENT_ID" -p "$CLIENT_SECRET" --tenant "$TENANT_ID" --output none
            az account set --subscription "$SUB_ID"
            az extension add --name ml
            az configure --defaults group=$GROUP workspace=$WORKSPACE location=$LOCATION
            
            # Check if compute exists before trying to start it
            if az ml compute show --name warre-cluster &> /dev/null; then
              STATE=$(az ml compute show --name warre-cluster --query "provisioning_state" -o tsv)
              echo "Compute exists with state: $STATE"
              
              if [ "$STATE" != "Succeeded" ]; then
                echo "Compute is not in Succeeded state. Current state: $STATE"
                echo "Waiting for compute to be ready..."
                sleep 30
              fi
              
              # Check if compute is already running
              CURRENT_STATE=$(az ml compute show --name warre-cluster --query "provisioning_state" -o tsv)
              if [ "$CURRENT_STATE" == "Succeeded" ]; then
                echo "Starting compute cluster..."
                az ml compute start --name warre-cluster || echo "Compute may already be starting or running"
              fi
            else
              echo "Compute cluster does not exist. It will be created in the next step."
            fi
        continue-on-error: true
```

This improved version:
1. Checks if the compute exists before attempting operations
2. Verifies the provisioning state before starting
3. Handles edge cases where compute might be in transition
4. Provides clear logging for debugging
5. Uses `continue-on-error: true` to not fail the entire pipeline if compute is already running

---

## QUESTION 3 - Loop over components

*‼️ Answer this question when you've gone through the complete pipeline*

Find a way to loop over the components and environments in a nice pattern so we don't have to repeat ourselves.

**ANSWER 3 - Loop over components**

```yaml
      - name: Azure -- Environment Setup
        uses: Azure/CLI@v2.1.0
        env:
          AZURE_CONFIG_DIR: ${{ env.AZURE_CONFIG_DIR }}
        with:
          azcliversion: 2.64.0
          inlineScript: |
            export AZURE_CONFIG_DIR="$AZURE_CONFIG_DIR"
            CREDS='${{ secrets.AZURE_CREDENTIALS }}'
            CLIENT_ID=$(python3 -c "import sys, json; print(json.load(sys.stdin)['clientId'])" <<< "$CREDS")
            CLIENT_SECRET=$(python3 -c "import sys, json; print(json.load(sys.stdin)['clientSecret'])" <<< "$CREDS")
            TENANT_ID=$(python3 -c "import sys, json; print(json.load(sys.stdin)['tenantId'])" <<< "$CREDS")
            SUB_ID=$(python3 -c "import sys, json; print(json.load(sys.stdin)['subscriptionId'])" <<< "$CREDS")
            az login --service-principal -u "$CLIENT_ID" -p "$CLIENT_SECRET" --tenant "$TENANT_ID" --output none
            az account set --subscription "$SUB_ID"
            az extension add --name ml
            az configure --defaults group=$GROUP workspace=$WORKSPACE location=$LOCATION
            
            # Loop through all environment YAML files
            for file in ./assignment/environment/*.yaml; do
              if [[ -f "$file" ]]; then
                echo "Creating environment from $file"
                az ml environment create --file "$file" || echo "Environment may already exist"
              fi
            done

      - name: Azure -- Component Setup
        uses: Azure/CLI@v2.1.0
        env:
          AZURE_CONFIG_DIR: ${{ env.AZURE_CONFIG_DIR }}
        with:
          azcliversion: 2.64.0
          inlineScript: |
            export AZURE_CONFIG_DIR="$AZURE_CONFIG_DIR"
            CREDS='${{ secrets.AZURE_CREDENTIALS }}'
            CLIENT_ID=$(python3 -c "import sys, json; print(json.load(sys.stdin)['clientId'])" <<< "$CREDS")
            CLIENT_SECRET=$(python3 -c "import sys, json; print(json.load(sys.stdin)['clientSecret'])" <<< "$CREDS")
            TENANT_ID=$(python3 -c "import sys, json; print(json.load(sys.stdin)['tenantId'])" <<< "$CREDS")
            SUB_ID=$(python3 -c "import sys, json; print(json.load(sys.stdin)['subscriptionId'])" <<< "$CREDS")
            az login --service-principal -u "$CLIENT_ID" -p "$CLIENT_SECRET" --tenant "$TENANT_ID" --output none
            az account set --subscription "$SUB_ID"
            az extension add --name ml
            az configure --defaults group=$GROUP workspace=$WORKSPACE location=$LOCATION
            COMPONENT_VERSION="${COMPONENT_VERSION:-0.1.${GITHUB_RUN_NUMBER}}"
            echo "Publishing components with version: $COMPONENT_VERSION"
            
            # Loop through components (only actual component YAML files, not conda.yaml or environment.yaml)
            for dir in ./assignment/components/*/; do
              for file in "$dir"*.yaml; do
                # Skip conda.yaml and environment.yaml files - only process component definition files
                basename_file=$(basename "$file")
                if [[ "$basename_file" != "conda.yaml" ]] && [[ "$basename_file" != "environment.yaml" ]] && [[ -f "$file" ]]; then
                  echo "Creating component from $file (version $COMPONENT_VERSION)"
                  az ml component create --file "$file" --set version="$COMPONENT_VERSION"
                else
                  echo "Skipping $file (not a component definition)"
                fi
              done
            done
```

This approach:
1. Uses bash loops to iterate over files dynamically
2. Filters out non-component files (conda.yaml, environment.yaml)
3. Applies versioning automatically to all components
4. Provides clear logging for each file being processed
5. Handles errors gracefully with `|| echo` fallbacks

---

## QUESTION 3 (Second) - Download AI Model Pipeline

1. Download the AI model using the `az ml` command like you did in the assignment
2. What is the purpose of the `needs: azure-pipeline` ?
3. What's the point of the `actions/upload-artifact@v4.3.3` ?

**ANSWER 3 - Download AI Model Pipeline**

1. **Command to download the model:**
```bash
VERSION=$(az ml model list -n animal-classification --query "[0].version" -o tsv)
az ml model download --name animal-classification --version $VERSION --download-path ./assignment/inference/model
```

2. **Purpose of `needs: azure-pipeline`:**
   
   The `needs` keyword creates a dependency chain between jobs in GitHub Actions. It ensures that the `download` job only starts after the `azure-pipeline` job has successfully completed. This is critical because:
   - The model must be trained and registered first (in `azure-pipeline`)
   - Only after successful registration can we download it
   - If the training fails, there's no point in trying to download a non-existent model
   - It creates a clear workflow: Train → Download → Deploy

3. **Purpose of `actions/upload-artifact@v4.3.3`:**
   
   This action persists files between jobs in a GitHub Actions workflow. Specifically:
   - Each job runs in a fresh, isolated environment
   - Files created in one job are lost when that job completes
   - `upload-artifact` saves files (the inference code + model) to GitHub's artifact storage
   - The `deploy` job (running on a different/self-hosted runner) can then `download-artifact` to get these files
   - Without this, the deploy job wouldn't have access to the model or inference code
   - It acts as a "handoff" mechanism between jobs running on different machines

---

## QUESTION 5 - Deploy to Kubernetes

1. Paste the YAML file for your Kubernetes deployments
2. Paste the GitHub Actions pipeline step with the `kubectl` commands

**ANSWER 5 - Deploy to Kubernetes**

**Kubernetes Deployment YAML (`assignment/kubernetes/deployment.yaml`):**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: animal-classification-deployment
  labels:
    app: animal-classification
spec:
  replicas: 1
  selector:
    matchLabels:
      app: animal-classification
  template:
    metadata:
      labels:
        app: animal-classification
    spec:
      containers:
        - name: animal-classification
          image: ghcr.io/snaetwarre/mlops-animals-api:master
          ports:
            - containerPort: 8000
          env:
            - name: MODEL_PATH
              value: /app/model/animal-classification/INPUT_model_path/animal-cnn/model.keras
---
apiVersion: v1
kind: Service
metadata:
  name: animal-classification-service
spec:
  type: LoadBalancer
  selector:
    app: animal-classification
  ports:
    - port: 80
      targetPort: 8000
```

**Key configuration points:**
- Uses the Docker image from GitHub Container Registry (GHCR)
- Exposes containerPort 8000 (FastAPI default)
- Sets MODEL_PATH environment variable to the correct model location inside the container
- Service maps external port 80 to internal port 8000
- LoadBalancer type makes it accessible from outside the cluster

**GitHub Actions Pipeline Step:**

```yaml
  deploy:
    needs: download
    runs-on: self-hosted
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Docker -- Gather Tags
        id: docker-meta-data
        uses: docker/metadata-action@v5.5.1
        with:
          images: |
            ghcr.io/${{ github.repository_owner }}/mlops-animals-api
          tags: |
            type=ref,event=branch
            type=sha

      - name: Docker -- Login to GHCR
        uses: docker/login-action@v3.2.0
        with:
          registry: ghcr.io
          username: ${{ github.repository_owner }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Docker -- Download API Code for Inference
        uses: actions/download-artifact@v4.1.7
        with:
          name: docker-config
          path: inference

      - name: Docker Build and push
        id: docker_build
        uses: docker/build-push-action@v5.3.0
        with:
          context: ./assignment/inference
          push: true
          tags: ${{ steps.docker-meta-data.outputs.tags }}

      - name: Prepare Kubernetes Config
        run: |
          mkdir -p $HOME/.kube
          printf '%s\n' "${{ secrets.KUBE_CONFIG }}" > $HOME/.kube/config
          chmod 600 $HOME/.kube/config

      - name: Kubernetes -- Deploy
        run: |
          kubectl apply -f ./assignment/kubernetes/deployment.yaml
```

**Why self-hosted runner?**
- Access to local Kubernetes cluster (k3d)
- Docker daemon available for building images
- kubectl configured with cluster access
- Avoids network complexity of accessing local cluster from GitHub's runners

---

## QUESTION 5b - Deploy to HuggingFace

1. Paste the GitHub Actions pipeline step with the HuggingFace adaptations.

**ANSWER 5b - Deploy to HuggingFace**

**Not implemented in this project.** 

However, if we were to implement HuggingFace deployment, the workflow would look like this:

```yaml
      - name: Push Model to Hugging Face Hub
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
        run: |
          pip install huggingface_hub
          
          # Login to Hugging Face
          huggingface-cli login --token $HF_TOKEN
          
          # Upload the model
          huggingface-cli upload ${{ github.repository_owner }}/animal-classification \
            ./assignment/inference/model \
            --repo-type model
          
      - name: Create Hugging Face Space for Inference
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
        run: |
          # Create a Spaces repo for the API
          huggingface-cli repo create animal-classification-api \
            --type space \
            --space_sdk gradio
          
          # Push inference code
          cd ./assignment/inference
          git init
          git remote add hf https://huggingface.co/spaces/${{ github.repository_owner }}/animal-classification-api
          git add .
          git commit -m "Deploy inference API"
          git push hf main
```

**Note:** This would require creating a `HF_TOKEN` secret in GitHub with a Hugging Face access token that has write permissions.

---

## QUESTION 6 - Final suggestions

Do you have more suggestions how we can add more functionalities into the GitHub Actions pipeline to create a better MLOps flow?

**ANSWER 6 - Final Suggestions**

1. **Secret Management with Azure Key Vault**: Instead of storing all credentials in GitHub Secrets, integrate with Azure Key Vault to centrally manage secrets. This provides better security, rotation policies, and audit logging.

2. **Automated Testing Pipeline**: Add comprehensive testing stages:
   - Unit tests for data preprocessing and model training code
   - Integration tests for the FastAPI endpoints
   - Model performance tests (accuracy threshold checks)
   - Load testing for the deployed API
   - A/B testing framework for comparing model versions

3. **Model Drift Detection**: Implement monitoring to detect when model performance degrades:
   - Log predictions and actual outcomes
   - Compare current model metrics against baseline
   - Trigger retraining workflow automatically when drift is detected
   - Send alerts to Slack/Teams when issues are found

4. **Pull Request Preview Deployments**: Create temporary environments for PR reviews:
   - Deploy PR changes to a staging Kubernetes namespace
   - Run automated tests against the PR deployment
   - Provide a preview URL for manual testing
   - Auto-cleanup after PR is merged or closed

5. **Model Registry and Versioning**: Enhance model management:
   - Tag models with git commit SHA for traceability
   - Store model metadata (training date, metrics, dataset version)
   - Implement model approval workflow before production deployment
   - Keep multiple model versions and enable easy rollback

6. **Responsible AI Integration**: Add Azure Responsible AI Dashboard:
   - Model explainability reports
   - Fairness assessment across different data groups
   - Error analysis to identify problematic scenarios
   - Generate compliance documentation automatically

7. **Infrastructure as Code (IaC)**: Use Terraform or Bicep to manage Azure resources:
   - Version control your infrastructure
   - Consistent environments (dev, staging, prod)
   - Automated disaster recovery
   - Cost tracking and optimization

8. **Monitoring and Observability**:
   - Integrate Application Insights for API telemetry
   - Set up Prometheus/Grafana for Kubernetes metrics
   - Create dashboards for model performance, API latency, and resource usage
   - Alert on SLA violations or anomalies

9. **Cost Optimization**:
   - Auto-stop compute clusters when not in use
   - Use spot instances for training when possible
   - Implement budget alerts in Azure
   - Track ML experiment costs per team/project

10. **Security Scanning**:
    - Scan Docker images for vulnerabilities (Trivy, Snyk)
    - Check dependencies for known CVEs
    - Validate Kubernetes manifests against security policies
    - Implement RBAC and network policies in Kubernetes

---

## What did you learn?

Fill in something that you learned during this lesson

> **Orchestrating Complex Multi-Stage Workflows**: I learned how to design and implement a complete MLOps pipeline that chains together multiple jobs across different environments (Azure ML, GitHub Actions, Kubernetes). The use of `needs` dependencies, artifact passing, and coordinating between cloud and self-hosted runners taught me the complexity of real-world CI/CD pipelines.

> **Azure ML Integration with GitHub Actions**: I gained hands-on experience with the Azure ML CLI and how to programmatically manage the entire ML lifecycle - from compute provisioning, environment setup, component registration, pipeline execution, and model registration - all from within GitHub Actions workflows.

> **Debugging Distributed Systems**: I learned practical debugging skills when things go wrong in CI/CD pipelines - from RBAC permission issues, Docker registry authentication, Kubernetes configuration problems, to environment variable management. The importance of proper logging, error handling, and understanding the execution context of each job became very clear.

> **Self-Hosted Runners Architecture**: I understood why and when to use self-hosted runners versus GitHub-hosted runners, particularly for deployment scenarios requiring access to local infrastructure (like k3d Kubernetes clusters) or when you need specific tools/configurations not available in GitHub's runners.

---

## Give three interesting exam questions

1. **Explain the complete data flow in this MLOps pipeline**: Starting from a code push to the repository, describe each stage of the pipeline, what happens in each job, how data is passed between jobs, and where the trained model ultimately ends up deployed. Include the purpose of artifacts and the role of different runner types (GitHub-hosted vs self-hosted).

2. **Azure ML RBAC and Permissions**: Why did the model registration fail initially with an "AuthorizationFailed" error, and what was the root cause? Explain the difference between the service principal used by GitHub Actions and the compute cluster's managed identity. What permissions are needed for each, and why can't they share the same credentials?

3. **Kubernetes Deployment Architecture**: Explain why the Kubernetes deployment initially failed with "InvalidImageName" and how template variable substitution works (or doesn't work) in different contexts. Additionally, describe why the MODEL_PATH environment variable was necessary and how the containerized application accesses the model file that was downloaded during the workflow.

**Bonus Question**: Design a rollback strategy: If the newly deployed model in Kubernetes starts performing poorly, describe the steps and commands you would use to rollback to the previous working version. Consider both the model version in Azure ML and the Docker image tag in GHCR.

---

## Notes on Implementation

**Key Challenges Solved:**

1. ✅ **Component Registration Loop**: Created a smart bash loop that filters out environment files (conda.yaml, environment.yaml) and only processes actual component definition files, with automatic versioning.

2. ✅ **Model Registration Permissions**: Fixed Azure ML RBAC by granting the compute cluster's managed identity the "AzureML Data Scientist" role, allowing it to both read and write models.

3. ✅ **Kubernetes Deployment Configuration**: 
   - Corrected the container port from 80 to 8000 (FastAPI default)
   - Set MODEL_PATH environment variable to the correct location
   - Fixed image name from template variable to actual registry path
   - Updated service to route port 80 to targetPort 8000

4. ✅ **GHCR Permissions**: Enabled "Read and write permissions" for GitHub Actions in repository settings to allow pushing Docker images to GitHub Container Registry.

5. ✅ **Self-Hosted Runner Setup**: Successfully configured and ran a self-hosted GitHub Actions runner to handle Docker builds and Kubernetes deployments requiring local cluster access.

**Final Architecture:**
- Azure ML: Training environment with compute cluster
- GitHub Container Registry: Docker image storage
- k3d Kubernetes: Local deployment target
- GitHub Actions: Orchestration layer
- Self-hosted runner: Deployment agent

**API Endpoints:**
- Base URL: `http://localhost:8888/` (via kubectl port-forward)
- Documentation: `http://localhost:8888/docs`
- Prediction: POST to `/predict` with image file

All components are working together successfully! 🎉