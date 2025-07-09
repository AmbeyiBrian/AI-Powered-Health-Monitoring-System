# Quick Azure Deployment Guide

## 🚀 One-Command Deployment

### Prerequisites
- Azure CLI: `az --version`
- Azure account (free tier available)
- Docker (optional - Azure can build for you)

### Install Azure CLI (if needed)
```bash
# Windows (PowerShell)
Invoke-WebRequest -Uri https://aka.ms/installazurecliwindows -OutFile .\AzureCLI.msi; Start-Process msiexec.exe -Wait -ArgumentList '/I AzureCLI.msi /quiet'; rm .\AzureCLI.msi

# Or download from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
```

### Deploy to Azure
```bash
# Make script executable (Git Bash/WSL)
chmod +x azure-deployment/deploy-complete.sh

# Run deployment
./azure-deployment/deploy-complete.sh
```

## 🎯 What Gets Created

### Core Services
- **Azure Container Apps**: Serverless container hosting
- **Azure Container Registry**: Your Docker images
- **Azure Database for PostgreSQL**: Managed database
- **Azure Cache for Redis**: Fast caching
- **Azure Virtual Network**: Network isolation
- **Azure Application Gateway**: Load balancer

### Security
- **Azure Key Vault**: Secure secrets
- **Private networking**: Database in private subnet
- **HTTPS by default**: SSL/TLS included

## 💰 Cost (Approximately $95-150/month)
- Much more predictable than AWS
- No surprise charges
- Free tier available for testing

## 🔧 Management Commands

### View logs
```bash
az containerapp logs show --name healthmonitor-prod-app --resource-group health-monitoring-rg --follow
```

### Scale application
```bash
az containerapp update --name healthmonitor-prod-app --resource-group health-monitoring-rg --min-replicas 2 --max-replicas 5
```

### Update application
```bash
# Build new image
az acr build --registry healthmonitorregistryprod --image health-monitoring:latest .

# Update app
az containerapp update --name healthmonitor-prod-app --resource-group health-monitoring-rg --image healthmonitorregistryprod.azurecr.io/health-monitoring:latest
```

### Delete everything
```bash
az group delete --name health-monitoring-rg --yes --no-wait
```

## 🌐 Advantages of Azure over AWS

### Easier Setup
- ✅ Simpler authentication
- ✅ Better integration with VS Code
- ✅ More predictable pricing
- ✅ Faster deployment

### Better Developer Experience
- ✅ Bicep templates (easier than CloudFormation)
- ✅ Container Apps (simpler than ECS)
- ✅ Integrated monitoring
- ✅ Better documentation

### Cost Management
- ✅ More transparent pricing
- ✅ Built-in cost alerts
- ✅ No data transfer charges between regions
- ✅ Better free tier

## 🔍 Troubleshooting

### Common Issues
1. **Login issues**: Run `az login` and follow prompts
2. **Permission errors**: Ensure you have Contributor role
3. **Resource conflicts**: Use unique names or delete existing resources

### Get help
```bash
az deployment group show --resource-group health-monitoring-rg --name health-monitoring-deployment
```

## 🎉 After Deployment

Your app will be available at:
`https://healthmonitor-prod-app.RANDOM.eastus.azurecontainerapps.io`

The exact URL will be shown after deployment completes.
