#!/bin/bash
# January Primus Installation Script
# Unified 10th Dimensional Swarm Intelligence

set -e

echo "🔥 Installing January Primus..."
echo "================================"

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker not found. Some features will be limited."
fi

# Create directories
echo "Creating directories..."
mkdir -p ~/.january/{config,memory,logs,namespace}
mkdir -p ~/.january/skills/{core,swarm,agents}

# Copy configuration
echo "Installing configuration..."
if [ -f ".env.example" ]; then
    cp .env.example ~/.january/.env
    echo "✅ Environment template copied to ~/.january/.env"
fi

# Install core modules
echo "Installing core modules..."
cd core/january
if [ -f "install.sh" ]; then
    chmod +x install.sh
    ./install.sh
fi
cd ../..

# Install memory system
cd core/memory
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
cd ../..

# Install namespace resolver
cd core/namespace
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
cd ../..

# Install swarm protocols
cd swarm/protocols
if [ -f "install.sh" ]; then
    chmod +x install.sh
    ./install.sh
fi
cd ../..

# Set permissions
echo "Setting permissions..."
chmod +x scripts/*.sh 2>/dev/null || true

# Create activation script
echo "Creating activation script..."
cat > ~/.january/activate << 'EOF'
#!/bin/bash
# January Primus Activation

export JANUARY_HOME="$HOME/.january"
export JANUARY_CONFIG="$JANUARY_HOME/config"
export PATH="$PATH:$JANUARY_HOME/bin"

# Load environment
if [ -f "$JANUARY_HOME/.env" ]; then
    source "$JANUARY_HOME/.env"
fi

echo "🔥 January Primus activated (10th Dimension)"
echo "Type 'january --help' for commands"
EOF

chmod +x ~/.january/activate

echo ""
echo "✅ Installation complete!"
echo ""
echo "To activate January Primus:"
echo "  source ~/.january/activate"
echo ""
echo "Or add to your shell profile:"
echo "  echo 'source ~/.january/activate' >> ~/.bashrc"
