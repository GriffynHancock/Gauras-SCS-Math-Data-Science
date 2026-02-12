#!/bin/bash
# Sri Chaitanya Saraswat Math Dataset Creator
# Automated Setup and Execution Script
# 
# Usage: ./setup_and_run.sh

set -e  # Exit on error

echo "=========================================================================="
echo "Sri Chaitanya Saraswat Math Publications Dataset Creator"
echo "=========================================================================="
echo ""
echo "🙏 Jay Srila Guru Maharaj! Jay Srila Acharya Maharaj!"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python 3 is installed
echo "🔍 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.12+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✅ Found Python $PYTHON_VERSION${NC}"

# Check if we're on macOS with Homebrew
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Detected macOS"
    if ! command -v brew &> /dev/null; then
        echo -e "${YELLOW}⚠️  Homebrew not found. Install from https://brew.sh${NC}"
    fi
fi

# Create virtual environment
echo ""
echo "📦 Setting up virtual environment..."
if [ ! -d "scsmath_env" ]; then
    python3 -m venv scsmath_env
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source scsmath_env/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip -q

# Install requirements
echo ""
echo "📥 Installing required packages..."
echo "   This may take a few minutes..."

pip install -q requests beautifulsoup4 lxml PyPDF2 ebooklib

echo -e "${GREEN}✅ All packages installed${NC}"

# Check if scripts exist
if [ ! -f "scsmath_data_processor.py" ]; then
    echo -e "${RED}❌ scsmath_data_processor.py not found in current directory${NC}"
    exit 1
fi

# Make scripts executable
chmod +x scsmath_data_processor.py 2>/dev/null || true
chmod +x dataset_utilities.py 2>/dev/null || true

# Ask user if they want to proceed with download
echo ""
echo "=========================================================================="
echo "⚠️  IMPORTANT NOTES:"
echo "=========================================================================="
echo "1. This will download ~2-3 GB of sacred texts"
echo "2. The process will take 30-60 minutes depending on your connection"
echo "3. The server will be accessed politely with delays between requests"
echo "4. All content belongs to Sri Chaitanya Saraswat Math, Nabadwip"
echo ""
read -p "Do you want to proceed? (yes/no): " -r
echo

if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    echo "Setup complete. Run 'python scsmath_data_processor.py' when ready."
    exit 0
fi

# Run the downloader
echo ""
echo "=========================================================================="
echo "🚀 Starting download and processing..."
echo "=========================================================================="
echo ""

python scsmath_data_processor.py

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================================================="
    echo -e "${GREEN}✅ SUCCESS! Dataset creation complete!${NC}"
    echo "=========================================================================="
    echo ""
    echo "📁 Your dataset is in: ./scsmath_dataset/"
    echo ""
    echo "Next steps:"
    echo "  1. Review the manifest: cat scsmath_dataset/metadata/manifest.json"
    echo "  2. Run analysis: python dataset_utilities.py"
    echo "  3. Prepare for training: see README.md"
    echo ""
    echo "🙏 Hare Krishna! May this preserve the teachings of your guru-paramparā."
    echo ""
else
    echo -e "${RED}❌ An error occurred. Check the output above.${NC}"
    exit 1
fi

# Deactivate virtual environment
deactivate
