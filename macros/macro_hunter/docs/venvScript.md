```bash
cat > setup_venvs.sh << 'EOF'
#!/bin/bash

# Create venvs directory if it doesn't exist
mkdir -p venvs

# Setup Python 3.11 environment
echo "Setting up Python 3.11 environment..."
python3.11 -m venv venvs/py311
source venvs/py311/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Setup Python 3.9 environment
echo "Setting up Python 3.9 environment..."
python3.9 -m venv venvs/py39
source venvs/py39/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

echo "Virtual environments setup complete"

echo "To activate environments use:"
echo "source venvs/py311/bin/activate  # For Python 3.11"
echo "source venvs/py39/bin/activate   # For Python 3.9"
EOF

chmod +x setup_venvs.sh

```