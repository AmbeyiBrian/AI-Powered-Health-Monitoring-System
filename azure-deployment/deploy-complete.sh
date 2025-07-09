#!/bin/bash

# Complete Azure Deployment Script for Health Monitoring System
set -e

# Configuration
RESOURCE_GROUP="health-monitoring-rg"
LOCATION="eastus"
DB_PASSWORD="HealthMonitor123!"
DEPLOYMENT_NAME="health-monitoring-deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Complete Azure Deployment for Health Monitoring System${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI is not installed. Please install it first.${NC}"
    echo -e "${YELLOW}📋 Installation: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli${NC}"
    exit 1
fi

# Step 1: Login to Azure
echo -e "\n${YELLOW}📋 Step 1: Logging into Azure...${NC}"
if ! az account show &> /dev/null; then
    echo -e "${BLUE}🔐 Please login to Azure...${NC}"
    az login
fi

# Get subscription info
SUBSCRIPTION_ID=$(az account show --query id --output tsv)
SUBSCRIPTION_NAME=$(az account show --query name --output tsv)
echo -e "${GREEN}✅ Logged into subscription: ${SUBSCRIPTION_NAME} (${SUBSCRIPTION_ID})${NC}"

# Step 2: Create Resource Group
echo -e "\n${YELLOW}📋 Step 2: Creating Resource Group...${NC}"
az group create \
    --name ${RESOURCE_GROUP} \
    --location ${LOCATION} \
    --output table

echo -e "${GREEN}✅ Resource group created successfully!${NC}"

# Step 3: Deploy Infrastructure
echo -e "\n${YELLOW}📋 Step 3: Deploying Infrastructure...${NC}"
echo -e "${BLUE}⏳ This may take 10-15 minutes...${NC}"

az deployment group create \
    --resource-group ${RESOURCE_GROUP} \
    --template-file azure-deployment/main.bicep \
    --parameters adminPassword=${DB_PASSWORD} \
    --name ${DEPLOYMENT_NAME} \
    --output table

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Infrastructure deployed successfully!${NC}"
else
    echo -e "${RED}❌ Infrastructure deployment failed!${NC}"
    exit 1
fi

# Step 4: Get deployment outputs
echo -e "\n${YELLOW}📋 Step 4: Getting deployment outputs...${NC}"

CONTAINER_REGISTRY=$(az deployment group show \
    --resource-group ${RESOURCE_GROUP} \
    --name ${DEPLOYMENT_NAME} \
    --query 'properties.outputs.containerRegistryLoginServer.value' \
    --output tsv)

CONTAINER_APP_FQDN=$(az deployment group show \
    --resource-group ${RESOURCE_GROUP} \
    --name ${DEPLOYMENT_NAME} \
    --query 'properties.outputs.containerAppFQDN.value' \
    --output tsv)

KEY_VAULT_NAME=$(az deployment group show \
    --resource-group ${RESOURCE_GROUP} \
    --name ${DEPLOYMENT_NAME} \
    --query 'properties.outputs.keyVaultName.value' \
    --output tsv)

POSTGRES_FQDN=$(az deployment group show \
    --resource-group ${RESOURCE_GROUP} \
    --name ${DEPLOYMENT_NAME} \
    --query 'properties.outputs.postgresServerFQDN.value' \
    --output tsv)

REDIS_HOSTNAME=$(az deployment group show \
    --resource-group ${RESOURCE_GROUP} \
    --name ${DEPLOYMENT_NAME} \
    --query 'properties.outputs.redisHostName.value' \
    --output tsv)

PUBLIC_IP=$(az deployment group show \
    --resource-group ${RESOURCE_GROUP} \
    --name ${DEPLOYMENT_NAME} \
    --query 'properties.outputs.publicIPAddress.value' \
    --output tsv)

echo -e "${GREEN}✅ Deployment outputs retrieved successfully!${NC}"

# Step 5: Build and Push Docker Image
echo -e "\n${YELLOW}📋 Step 5: Building and pushing Docker image...${NC}"

# Get registry credentials
REGISTRY_NAME=$(echo ${CONTAINER_REGISTRY} | cut -d'.' -f1)

# Login to Container Registry
az acr login --name ${REGISTRY_NAME}

# Build and push image
echo -e "${BLUE}🔨 Building Docker image...${NC}"
az acr build \
    --registry ${REGISTRY_NAME} \
    --image health-monitoring:latest \
    --file Dockerfile.production \
    .

echo -e "${GREEN}✅ Docker image built and pushed successfully!${NC}"

# Step 6: Update Container App with new image
echo -e "\n${YELLOW}📋 Step 6: Updating Container App...${NC}"

az containerapp update \
    --name healthmonitor-prod-app \
    --resource-group ${RESOURCE_GROUP} \
    --image ${CONTAINER_REGISTRY}/health-monitoring:latest

echo -e "${GREEN}✅ Container App updated successfully!${NC}"

# Step 7: Wait for deployment to be ready
echo -e "\n${YELLOW}📋 Step 7: Waiting for application to be ready...${NC}"
echo -e "${BLUE}⏳ This may take a few minutes...${NC}"

# Wait for the app to be accessible
for i in {1..30}; do
    if curl -s -o /dev/null -w "%{http_code}" https://${CONTAINER_APP_FQDN} | grep -q "200\|302"; then
        echo -e "${GREEN}✅ Application is ready!${NC}"
        break
    else
        echo -e "${YELLOW}⏳ Waiting for application... (${i}/30)${NC}"
        sleep 10
    fi
done

# Step 8: Display deployment summary
echo -e "\n${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}📋 Deployment Summary:${NC}"
echo -e "   • Resource Group: ${RESOURCE_GROUP}"
echo -e "   • Location: ${LOCATION}"
echo -e "   • Container Registry: ${CONTAINER_REGISTRY}"
echo -e "   • Database Server: ${POSTGRES_FQDN}"
echo -e "   • Redis Cache: ${REDIS_HOSTNAME}"
echo -e "   • Public IP: ${PUBLIC_IP}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

echo -e "\n${GREEN}🌐 Your Health Monitoring System is now available at:${NC}"
echo -e "${BLUE}https://${CONTAINER_APP_FQDN}${NC}"

echo -e "\n${YELLOW}📋 Next Steps:${NC}"
echo -e "   1. Access your application at: https://${CONTAINER_APP_FQDN}"
echo -e "   2. Set up custom domain (optional)"
echo -e "   3. Configure SSL certificate (optional)"
echo -e "   4. Set up monitoring and alerts"
echo -e "   5. Configure backup strategy"

echo -e "\n${YELLOW}🔧 Management Commands:${NC}"
echo -e "   • View logs: az containerapp logs show --name healthmonitor-prod-app --resource-group ${RESOURCE_GROUP} --follow"
echo -e "   • Scale app: az containerapp update --name healthmonitor-prod-app --resource-group ${RESOURCE_GROUP} --min-replicas 2"
echo -e "   • Update app: az acr build --registry ${REGISTRY_NAME} --image health-monitoring:latest . && az containerapp update --name healthmonitor-prod-app --resource-group ${RESOURCE_GROUP} --image ${CONTAINER_REGISTRY}/health-monitoring:latest"
echo -e "   • Delete resources: az group delete --name ${RESOURCE_GROUP} --yes --no-wait"

echo -e "\n${YELLOW}💰 Estimated Monthly Cost: ~$95-150 USD${NC}"
echo -e "   • Container Apps: ~$20-30"
echo -e "   • PostgreSQL: ~$25-35"
echo -e "   • Redis: ~$15-25"
echo -e "   • Application Gateway: ~$25-35"
echo -e "   • Other services: ~$10-20"

echo -e "\n${GREEN}✅ Deployment complete!${NC}"
