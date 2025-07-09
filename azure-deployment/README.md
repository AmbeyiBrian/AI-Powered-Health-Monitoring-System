# Azure Deployment Configuration

## Overview
Deploy the AI-Powered Health Monitoring System to Microsoft Azure using:
- **Azure Container Instances (ACI)** or **Azure Container Apps** for hosting
- **Azure Database for PostgreSQL** for the database
- **Azure Cache for Redis** for caching
- **Azure Container Registry** for Docker images
- **Azure Application Gateway** for load balancing

## Prerequisites

1. **Azure CLI installed**
   ```bash
   # Download from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
   az --version
   ```

2. **Azure Account**
   - Free account: https://azure.microsoft.com/free/
   - Or existing subscription

3. **Docker installed** (optional - can build in Azure)

## Quick Deployment

### Option 1: One-Click Deployment (Recommended)
```bash
chmod +x azure-deployment/deploy-complete.sh
./azure-deployment/deploy-complete.sh
```

### Option 2: Step-by-Step
```bash
# 1. Login to Azure
az login

# 2. Create resource group
az group create --name health-monitoring-rg --location eastus

# 3. Deploy infrastructure
az deployment group create \
  --resource-group health-monitoring-rg \
  --template-file azure-deployment/main.bicep \
  --parameters adminPassword=HealthMonitor123!

# 4. Build and deploy container
az acr build --registry healthmonitoringregistry \
  --image health-monitoring:latest .
```

## Azure Services Used

### Core Services
- **Azure Container Apps**: Serverless container hosting
- **Azure Container Registry**: Container image storage
- **Azure Database for PostgreSQL**: Managed database
- **Azure Cache for Redis**: Managed Redis cache
- **Azure Application Gateway**: Load balancer and SSL termination

### Security & Management
- **Azure Key Vault**: Secure credential storage
- **Azure Monitor**: Logging and monitoring
- **Azure Active Directory**: Identity management

## Cost Estimation (East US)

### Monthly Costs (Approximate)
- **Container Apps (1 instance)**: ~$20-30
- **PostgreSQL (Basic tier)**: ~$25-35
- **Redis (Basic tier)**: ~$15-25
- **Application Gateway**: ~$25-35
- **Container Registry**: ~$5-10
- **Storage & Bandwidth**: ~$5-15

**Total: ~$95-150/month**

### Cost Optimization
- Use Azure Reserved Instances
- Enable auto-scaling
- Set up cost alerts
- Use Azure Cost Management

## Management Commands

### View Application Logs
```bash
az containerapp logs show \
  --name health-monitoring-app \
  --resource-group health-monitoring-rg \
  --follow
```

### Scale Application
```bash
az containerapp update \
  --name health-monitoring-app \
  --resource-group health-monitoring-rg \
  --min-replicas 1 \
  --max-replicas 3
```

### Update Application
```bash
# Build new image
az acr build --registry healthmonitoringregistry \
  --image health-monitoring:latest .

# Update container app
az containerapp update \
  --name health-monitoring-app \
  --resource-group health-monitoring-rg \
  --image healthmonitoringregistry.azurecr.io/health-monitoring:latest
```

## Cleanup

To delete all Azure resources:
```bash
az group delete --name health-monitoring-rg --yes --no-wait
```

⚠️ **Warning**: This will delete all data including the database!
