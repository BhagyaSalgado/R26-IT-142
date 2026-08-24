"""
Advanced Training Script - Fine-tune BERT on your dataset
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def train_bert_model():
    """
    Train BERT model on your dataset
    
    This is Phase 3 - Custom fine-tuning for better accuracy
    """
    
    logger.info("\n" + "="*60)
    logger.info("BERT FINE-TUNING - Phase 3")
    logger.info("="*60)
    
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification, TextClassificationPipeline
        from datasets import load_dataset, Dataset
        from transformers import Trainer, TrainingArguments
        import torch
        
        # Configuration
        MODEL_NAME = "bert-base-uncased"
        CLEANED_DATA = "./data/cleaned_comments.csv"
        OUTPUT_DIR = "./models/finetuned_bert"
        EPOCHS = 3
        BATCH_SIZE = 32
        LEARNING_RATE = 2e-5
        
        logger.info(f"Configuration:")
        logger.info(f"  Model: {MODEL_NAME}")
        logger.info(f"  Data: {CLEANED_DATA}")
        logger.info(f"  Output: {OUTPUT_DIR}")
        logger.info(f"  Epochs: {EPOCHS}")
        logger.info(f"  Batch Size: {BATCH_SIZE}")
        
        # 1. Load cleaned data
        logger.info("\n1️⃣  Loading cleaned data...")
        if not os.path.exists(CLEANED_DATA):
            logger.error(f"❌ File not found: {CLEANED_DATA}")
            logger.error("Run: python scripts/clean_dataset.py")
            return False
        
        df = pd.read_csv(CLEANED_DATA)
        logger.info(f"✅ Loaded {len(df)} comments")
        
        # 2. Prepare data
        logger.info("\n2️⃣  Preparing dataset...")
        
        # Map sentiments to labels
        sentiment_to_id = {"NEGATIVE": 0, "NEUTRAL": 1, "POSITIVE": 2}
        df['label'] = df['sentiment'].map(sentiment_to_id)
        
        # Split train/test
        from sklearn.model_selection import train_test_split
        train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
        
        logger.info(f"✅ Train: {len(train_df)} | Test: {len(test_df)}")
        
        # Convert to HuggingFace Dataset
        train_dataset = Dataset.from_pandas(train_df[['comment', 'label']])
        test_dataset = Dataset.from_pandas(test_df[['comment', 'label']])
        
        # 3. Load tokenizer and model
        logger.info("\n3️⃣  Loading model and tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForSequenceClassification.from_pretrained(
            MODEL_NAME,
            num_labels=3
        )
        logger.info(f"✅ Model loaded: {MODEL_NAME}")
        
        # 4. Tokenize data
        logger.info("\n4️⃣  Tokenizing data...")
        
        def tokenize_function(example):
            return tokenizer(
                example['comment'],
                padding="max_length",
                truncation=True,
                max_length=128
            )
        
        train_dataset = train_dataset.map(tokenize_function, batched=True)
        test_dataset = test_dataset.map(tokenize_function, batched=True)
        logger.info("✅ Data tokenized")
        
        # 5. Setup training
        logger.info("\n5️⃣  Setting up training...")
        
        training_args = TrainingArguments(
            output_dir=OUTPUT_DIR,
            num_train_epochs=EPOCHS,
            per_device_train_batch_size=BATCH_SIZE,
            per_device_eval_batch_size=BATCH_SIZE,
            learning_rate=LEARNING_RATE,
            weight_decay=0.01,
            save_strategy="epoch",
            eval_strategy="epoch",
            logging_steps=10,
            push_to_hub=False,
        )
        
        from transformers import Trainer
        
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=test_dataset,
        )
        
        # 6. Train model
        logger.info("\n6️⃣  Training model (this may take a while)...")
        trainer.train()
        logger.info("✅ Training complete!")
        
        # 7. Evaluate
        logger.info("\n7️⃣  Evaluating model...")
        results = trainer.evaluate()
        
        logger.info(f"✅ Evaluation Results:")
        logger.info(f"  Accuracy: {results['eval_accuracy']:.4f}")
        logger.info(f"  Loss: {results['eval_loss']:.4f}")
        
        # 8. Save model
        logger.info("\n8️⃣  Saving model...")
        model.save_pretrained(OUTPUT_DIR)
        tokenizer.save_pretrained(OUTPUT_DIR)
        logger.info(f"✅ Model saved to: {OUTPUT_DIR}")
        
        logger.info("\n" + "="*60)
        logger.info("✅ FINE-TUNING COMPLETE!")
        logger.info("="*60)
        logger.info("\nYour fine-tuned model is now ready!")
        logger.info(f"Backend will automatically use: {OUTPUT_DIR}")
        logger.info("\nNext: python app.py")
        
        return True
    
    except ImportError as e:
        logger.error(f"❌ Missing package: {e}")
        logger.error("Install with: pip install transformers datasets scikit-learn torch")
        return False
    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = train_bert_model()
    sys.exit(0 if success else 1)
