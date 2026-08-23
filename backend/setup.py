"""Setup script to initialize backend environment"""

import os
import sys
import subprocess

def create_directories():
    """Create necessary directories"""
    directories = [
        './logs',
        './data',
        './models',
        './.cache/models',
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")


def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
            check=True
        )
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False
    
    return True


def download_nltk_data():
    """Download NLTK data"""
    print("\n📥 Downloading NLTK data...")
    
    import nltk
    
    data_to_download = [
        'punkt',
        'stopwords',
        'wordnet',
        'vader_lexicon'
    ]
    
    for data in data_to_download:
        try:
            nltk.download(data)
            print(f"✅ Downloaded: {data}")
        except Exception as e:
            print(f"⚠️  Could not download {data}: {e}")


def create_env_file():
    """Create .env file if it doesn't exist"""
    if not os.path.exists('.env'):
        print("\n📝 Creating .env file (using .env.example as template)")
        if os.path.exists('.env.example'):
            with open('.env.example', 'r') as src:
                with open('.env', 'w') as dst:
                    dst.write(src.read())
            print("✅ .env file created - UPDATE WITH YOUR VALUES")
        else:
            print("⚠️  .env.example not found")
    else:
        print("\n✅ .env file already exists")


def main():
    """Main setup function"""
    print("🚀 Setting up Comment Sentiment Analysis Backend\n")
    
    # Create directories
    create_directories()
    
    # Create .env file
    create_env_file()
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed during dependency installation")
        return False
    
    # Download NLTK data
    download_nltk_data()
    
    print("\n" + "="*60)
    print("✅ Setup completed successfully!")
    print("="*60)
    print("\n📋 Next steps:")
    print("1. Update .env file with your configuration")
    print("2. Add firebase-config.json to project root")
    print("3. Run: python app.py")
    print("\nTo clean and prepare your dataset:")
    print("  python scripts/clean_dataset.py")
    print("\nTo test the service:")
    print("  python tests/test_sentiment_service.py")
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
