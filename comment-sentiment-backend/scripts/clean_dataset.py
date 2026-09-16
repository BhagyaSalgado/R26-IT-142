"""Clean and prepare dataset from Excel file"""

import pandas as pd
import logging
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import DATA_DIR, CLEANED_DATA_PATH
from config.constants import SENTIMENT_LABELS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_excel_dataset(excel_path: str) -> pd.DataFrame:
    """
    Clean dataset from Excel file
    
    Args:
        excel_path: Path to Excel file
        
    Returns:
        Cleaned DataFrame
    """
    logger.info(f"Loading Excel file: {excel_path}")
    
    try:
        # Read Excel file
        df = pd.read_excel(excel_path)
        logger.info(f"Loaded {len(df)} rows")
        
        # Display columns
        logger.info(f"Columns: {df.columns.tolist()}")
        
        # Remove empty rows
        df = df.dropna(subset=df.columns[0] if len(df.columns) > 0 else None)
        logger.info(f"After removing empty rows: {len(df)} rows")
        
        # Assuming first column is comment, second is sentiment
        if len(df.columns) >= 2:
            df.columns = ['comment', 'sentiment']
            
            # Clean sentiment labels
            df['sentiment'] = df['sentiment'].str.strip().str.lower()
            
            # Map sentiments to standard format
            df['sentiment'] = df['sentiment'].map(
                lambda x: SENTIMENT_LABELS.get(x, x) if x in SENTIMENT_LABELS else 'NEUTRAL'
            )
            
            # Remove rows with invalid sentiments
            valid_sentiments = ['POSITIVE', 'NEGATIVE', 'NEUTRAL']
            df = df[df['sentiment'].isin(valid_sentiments)]
            logger.info(f"After cleaning sentiments: {len(df)} rows")
            
            # Remove duplicates
            df = df.drop_duplicates(subset=['comment'])
            logger.info(f"After removing duplicates: {len(df)} rows")
            
            # Display sentiment distribution
            logger.info("\nSentiment Distribution:")
            print(df['sentiment'].value_counts())
            print(f"\nPercentages:")
            print(df['sentiment'].value_counts(normalize=True) * 100)
            
            return df
        else:
            logger.error("Excel file must have at least 2 columns")
            return None
    
    except Exception as e:
        logger.error(f"Error cleaning dataset: {str(e)}")
        return None


def save_cleaned_data(df: pd.DataFrame, output_path: str):
    """
    Save cleaned data to CSV
    
    Args:
        df: Cleaned DataFrame
        output_path: Path to save CSV
    """
    try:
        # Create directory if needed
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"✅ Saved cleaned data to: {output_path}")
        logger.info(f"Total rows: {len(df)}")
        
    except Exception as e:
        logger.error(f"Error saving data: {str(e)}")


def main():
    """Main function"""
    
    # Try multiple locations for the Excel file
    possible_paths = [
        './finalized_movie_info.xlsx',
        './data/finalized_movie_info.xlsx',
        '../finalized_movie_info.xlsx',
    ]
    
    excel_path = None
    for path in possible_paths:
        if os.path.exists(path):
            excel_path = path
            break
    
    if not excel_path:
        logger.error("❌ Could not find finalized_movie_info.xlsx")
        logger.error("Please place it in one of these locations:")
        for path in possible_paths:
            logger.error(f"  - {path}")
        return False
    
    # Clean the dataset
    df = clean_excel_dataset(excel_path)
    
    if df is not None:
        # Save cleaned data
        save_cleaned_data(df, CLEANED_DATA_PATH)
        logger.info("✅ Dataset cleaning completed!")
    else:
        logger.error("❌ Failed to clean dataset")


if __name__ == '__main__':
    main()
