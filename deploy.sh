#!/bin/bash
# Consensus Gallery - Deployment Script

echo "🎨 Consensus Gallery Deployment Script"
echo "======================================="

# Check for required tools
check_requirements() {
    echo "📋 Checking requirements..."
    
    if ! command -v npm &> /dev/null; then
        echo "❌ npm is not installed. Please install Node.js first."
        exit 1
    fi
    
    echo "✅ npm found"
}

# Install GenLayer CLI
install_genlayer_cli() {
    echo "📦 Installing GenLayer CLI..."
    npm install -g genlayer
    echo "✅ GenLayer CLI installed"
}

# Deploy contract
deploy_contract() {
    local network=$1
    local treasury=$2
    
    echo "🚀 Deploying contract to $network..."
    
    genlayer network $network
    
    result=$(genlayer deploy --contract contracts/consensus_gallery.py --args "$treasury")
    
    # Extract contract address from result
    contract_address=$(echo "$result" | grep -oP '0x[a-fA-F0-9]{40}')
    
    if [ -n "$contract_address" ]; then
        echo "✅ Contract deployed at: $contract_address"
        echo "$contract_address"
    else
        echo "❌ Failed to deploy contract"
        exit 1
    fi
}

# Update frontend config
update_frontend() {
    local contract_address=$1
    local network=$2
    
    echo "🔧 Updating frontend configuration..."
    
    # Update contract address in index.html
    sed -i "s/ADDRESS: '0x0000000000000000000000000000000000000000'/ADDRESS: '$contract_address'/g" public/index.html
    
    # Update network
    sed -i "s/CURRENT_NETWORK: 'studionet'/CURRENT_NETWORK: '$network'/g" public/index.html
    
    echo "✅ Frontend updated"
}

# Deploy to Vercel
deploy_vercel() {
    echo "🌐 Deploying to Vercel..."
    
    if ! command -v vercel &> /dev/null; then
        echo "📦 Installing Vercel CLI..."
        npm install -g vercel
    fi
    
    vercel --prod
    
    echo "✅ Deployed to Vercel"
}

# Main menu
main() {
    echo ""
    echo "Select an option:"
    echo "1) Full deployment (contract + frontend)"
    echo "2) Deploy contract only"
    echo "3) Deploy frontend only (Vercel)"
    echo "4) Exit"
    echo ""
    read -p "Enter choice [1-4]: " choice
    
    case $choice in
        1)
            check_requirements
            install_genlayer_cli
            
            echo ""
            echo "Select network:"
            echo "1) localnet"
            echo "2) studionet"
            echo "3) testnet-asimov"
            read -p "Enter choice [1-3]: " net_choice
            
            case $net_choice in
                1) network="localnet" ;;
                2) network="studionet" ;;
                3) network="testnet-asimov" ;;
                *) echo "Invalid choice"; exit 1 ;;
            esac
            
            read -p "Enter treasury address: " treasury
            
            contract_address=$(deploy_contract $network $treasury)
            update_frontend $contract_address $network
            
            read -p "Deploy frontend to Vercel? (y/n): " deploy_frontend
            if [ "$deploy_frontend" = "y" ]; then
                deploy_vercel
            fi
            
            echo ""
            echo "🎉 Deployment complete!"
            echo "Contract: $contract_address"
            echo "Network: $network"
            ;;
        2)
            check_requirements
            install_genlayer_cli
            
            echo "Select network:"
            echo "1) localnet"
            echo "2) studionet"
            echo "3) testnet-asimov"
            read -p "Enter choice [1-3]: " net_choice
            
            case $net_choice in
                1) network="localnet" ;;
                2) network="studionet" ;;
                3) network="testnet-asimov" ;;
                *) echo "Invalid choice"; exit 1 ;;
            esac
            
            read -p "Enter treasury address: " treasury
            deploy_contract $network $treasury
            ;;
        3)
            deploy_vercel
            ;;
        4)
            echo "Bye! 👋"
            exit 0
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac
}

main
