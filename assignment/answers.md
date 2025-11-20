# Answers for MLOps Automation Assignment

## QUESTION 1 - Check latest versions

In the assignment ‣ you checked which versions were the latest, make sure to also update the versions in your pipeline here.

**ANSWER 1 - Check latest versions**

- `azcli` — Current version: `2.64.0`
- `Azure/CLI` — Current version: `v2.1.0` (Latest major version v2)

## QUESTION 2 - Robust Pipelines: Compute - *Extra*

*‼️ Answer this question when you’ve gone through the complete pipeline*

Provide a better solution using checks and if-statements.

**ANSWER 2 - Robust Pipelines: Compute - *Extra***

```yaml
      - name: Azure -- Start Compute
        uses: Azure/CLI@v2.1.0
        with:
          azcliversion: 2.64.0
          inlineScript: |
            az extension add --name ml -y
            az configure --defaults group=$GROUP workspace=$WORKSPACE location=$LOCATION
            
            # Check if compute is already running
            STATE=$(az ml compute show --name cli-created-machine --query state -o tsv)
            if [ "$STATE" != "Running" ]; then
              echo "Compute is not running. Starting..."
              az ml compute start --name cli-created-machine
            else
              echo "Compute is already running."
            fi
```

## QUESTION 3 - Loop over components

*‼️ Answer this question when you’ve gone through the complete pipeline*

Find a way to loop over the components and environments in a nice pattern so we don’t have to repeat ourselves.

**ANSWER 3 - Loop over components**

```yaml
      - name: Azure -- Component Setup
        uses: Azure/CLI@v2.1.0
        with:
          azcliversion: 2.64.0
          inlineScript: |
            az extension add --name ml
            az configure --defaults group=$GROUP workspace=$WORKSPACE location=$LOCATION
            
            # Loop through all yaml files in components/dataprep and components/training
            for file in ./components/*/*.yaml; do
              echo "Creating component from $file"
              az ml component create --file "$file"
            done
```

## QUESTION 3 (Second) - Download AI Model Pipeline

1. Download the AI model using the `az ml` command like you did in ‣
2. What is the purpose of the `needs: azure-pipeline` ?
3. What’s the point of the `actions/upload-artifact@v4.3.3` ?

**ANSWER 3 - Download AI Model Pipeline**

1. Command: `az ml model download --name animal-classification --version $VERSION --target-dir ./inference/model --overwrite`
2. `needs`: The `needs` keyword ensures that the `download` job only starts after the `azure-pipeline` job has successfully completed. This creates a dependency, ensuring the model is trained and registered before we try to download it.
3. `upload-artifact`: This action is used to persist files (artifacts) after a job completes. In this case, it uploads the inference code and the downloaded model so they can be shared with the `deploy` job, which runs on a different runner (likely self-hosted).

## QUESTION 5 - Deploy to Kubernetes

1. Paste the YAML file for your Kubernetes deployments
2. Paste the GitHub Actions pipeline step with the `kubectl` commands

**ANSWER 5 - Deploy to Kubernetes**

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
        image: ghcr.io/${{ github.repository_owner }}/mlops-animals-api:latest
        ports:
        - containerPort: 80
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
    targetPort: 80
```

```yaml
      - name: Kubernetes -- Deploy
        uses: actions-hub/kubectl@master
        env:
          KUBE_CONFIG: ${{ secrets.KUBE_CONFIG }}
        with:
          args: apply -f ./kubernetes/deployment.yaml
```

## QUESTION 5b - Deploy to HuggingFace

1. Paste the GitHub Actions pipeline step with the HuggingFace adaptations.

**ANSWER 5b - Deploy to HuggingFace**

```yaml
      - name: Push to Hugging Face Hub
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
        run: |
          pip install huggingface_hub
          huggingface-cli login --token $HF_TOKEN
          huggingface-cli upload ${{ github.repository_owner }}/animal-classification ./inference/model .
```

## QUESTION 6 - Final suggestions

Do you have more suggestions how we can add more functionalities into the GitHub Actions pipeline to create a better MLOps flow?

**ANSWER 6 - Final Suggestions**

1. **Secret Management**: Use Azure Key Vault to manage secrets instead of GitHub Secrets for better security and centralization.
2. **Linting and Formatting**: Add a step to lint the Python code (flake8, pylint) and format it (black) before running the pipeline to ensure code quality.
3. **Unit Tests**: Run unit tests for the data preparation and training scripts before submitting the Azure ML job.
4. **Pull Request Triggers**: Configure the pipeline to run a smaller subset of tests or a dry-run on Pull Requests to catch issues before merging to main.
5. **Model Evaluation Gate**: Add a manual approval step before deployment if the model metrics don't meet a certain threshold, or automate the comparison with the production model.

## What did you learn?

Fill in something that you learned during this lesson

> I learned how to chain multiple GitHub Actions jobs using `needs` and pass data between them using artifacts.
> 
> I also learned how to automate the full lifecycle of an Azure ML project, from compute creation to model deployment, using the Azure CLI within GitHub Actions.
> 

## Give three interesting exam questions

1. What is the purpose of the `needs` keyword in a GitHub Actions workflow and how does it affect the execution order of jobs?
2. Explain the difference between running a job on `ubuntu-latest` vs. `self-hosted` runners and why you might choose one over the other for deployment tasks.
3. How can you pass data, such as a trained model file, from one GitHub Actions job to another running on a different machine?
