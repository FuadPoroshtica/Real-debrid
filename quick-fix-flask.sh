#!/bin/bash

# Quick fix to install Flask and continue deployment

echo "🔧 Quick Fix: Installing Flask..."
echo ""

# Try system-wide installation
echo "Installing Flask system-wide..."
pip3 install --break-system-packages flask

# Verify installation
if python3 -c "import flask" 2>/dev/null; then
    echo "✅ Flask installed successfully!"
    echo ""
    echo "You can now continue with deployment:"
    echo "  ./deploy.sh"
    echo ""
    echo "Or start the web wizard directly:"
    echo "  python3 setup_wizard.py"
else
    echo "❌ Flask installation failed"
    echo ""
    echo "Alternative: Create virtual environment manually:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install flask"
    echo "  python setup_wizard.py"
fi
