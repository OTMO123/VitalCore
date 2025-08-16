#!/usr/bin/env python3
"""
Quick test to check SFTTrainer syntax without loading the full model
"""

import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sft_trainer_syntax():
    """Test SFTTrainer initialization syntax"""
    
    try:
        from trl import SFTTrainer, SFTConfig
        logger.info("✓ TRL imported successfully")
        
        # Check SFTTrainer signature
        import inspect
        signature = inspect.signature(SFTTrainer.__init__)
        logger.info(f"SFTTrainer signature: {signature}")
        
        # List all parameters
        params = list(signature.parameters.keys())
        logger.info(f"SFTTrainer parameters: {params}")
        
        # Test configuration without actual model
        try:
            config = SFTConfig(
                dataset_text_field="text",
                per_device_train_batch_size=1,
                max_steps=5,
                learning_rate=2e-4,
                logging_steps=1,
                optim="adamw_torch",
                output_dir="./test_output",
                fp16=False,
                bf16=False,
                dataloader_pin_memory=False,
                use_cpu=True,
            )
            logger.info("✓ SFTConfig created successfully")
            
        except Exception as e:
            logger.error(f"SFTConfig failed: {e}")
            
        return True
        
    except ImportError as e:
        logger.error(f"Import failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Testing SFTTrainer syntax...")
    success = test_sft_trainer_syntax()
    
    if success:
        logger.info("✅ Syntax test completed")
    else:
        logger.error("❌ Syntax test failed")
        sys.exit(1)