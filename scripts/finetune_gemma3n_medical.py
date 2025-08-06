#!/usr/bin/env python3
"""
HEMA3N Medical LoRA Fine-tuning with Gemma 3N

Based on the Unsloth Gemma 3N notebook, this script fine-tunes specialized 
medical agents using LoRA (Low-Rank Adaptation) for efficient training.

Features:
- Gemma 3N multimodal capabilities (text, vision, audio)
- Medical dataset integration
- Specialized medical agent training
- Memory-efficient 4-bit quantization
- LoRA fine-tuning for medical domains

Usage:
    python scripts/finetune_gemma3n_medical.py --agent cardiology --epochs 3
    python scripts/finetune_gemma3n_medical.py --agent all --medical-data
"""

import os
import sys
import asyncio
import argparse
import logging
import json
import torch
import gc
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.ai.diagnosis_engine import AgentSpecialization

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MedicalGemma3NTrainer:
    """LoRA fine-tuning for Gemma 3N medical agents"""
    
    def __init__(self, output_dir: str = "./models/medical_agents"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model = None
        self.tokenizer = None
        
    def setup_environment(self) -> bool:
        """Setup Unsloth environment for Gemma 3N training"""
        
        logger.info("Setting up Gemma 3N training environment...")
        
        try:
            # Install required packages if not available
            required_packages = [
                "unsloth", "transformers", "datasets", "trl", 
                "accelerate", "bitsandbytes", "peft"
            ]
            
            missing_packages = []
            for package in required_packages:
                try:
                    if package == "unsloth":
                        # Check GPU first for Unsloth compatibility
                        import torch
                        if torch.cuda.is_available():
                            from unsloth import FastModel
                        else:
                            # Skip unsloth on CPU - use standard training
                            logger.warning(f"⚠ Skipping {package} on CPU - using standard transformers")
                            continue
                    elif package == "trl":
                        from trl import SFTTrainer, SFTConfig
                    else:
                        __import__(package)
                    logger.info(f"✓ {package} available")
                except ImportError:
                    missing_packages.append(package)
                    logger.warning(f"✗ {package} missing")
            
            # Filter out unsloth if on CPU (it's optional)
            critical_missing = [p for p in missing_packages if p != "unsloth" or torch.cuda.is_available()]
            
            if critical_missing:
                logger.error(f"Missing packages: {critical_missing}")
                logger.info("Install with:")
                logger.info("pip install unsloth[colab-new] trl datasets accelerate bitsandbytes")
                return False
            elif missing_packages:
                logger.info(f"Optional packages skipped: {missing_packages} (CPU mode)")
                logger.info("Training will continue with standard transformers")
            
            # Check GPU availability
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                logger.info(f"✓ CUDA available with {gpu_count} GPU(s)")
                for i in range(gpu_count):
                    gpu_name = torch.cuda.get_device_name(i)
                    gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
                    logger.info(f"  GPU {i}: {gpu_name} ({gpu_memory:.1f} GB)")
            else:
                logger.warning("✗ CUDA not available - will use CPU (much slower)")
            
            return True
            
        except Exception as e:
            logger.error(f"Environment setup failed: {e}")
            return False
    
    def _load_model_standard(self, model_name: str, max_seq_length: int, dtype: str = None):
        """Load model using standard transformers (CPU fallback)"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            logger.info(f"Loading {model_name} with standard transformers...")
            
            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Load model - use smaller precision for CPU
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32,  # Use float32 for CPU
                device_map="cpu",
                trust_remote_code=True
            )
            
            logger.info(f"✓ Model loaded successfully on CPU")
            logger.info(f"✓ Model parameters: {model.num_parameters():,}")
            
            self.model = model
            self.tokenizer = tokenizer
            
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"Failed to load model with standard transformers: {e}")
            return None, None
    
    def load_gemma3n_model(
        self, 
        model_name: str = "unsloth/gemma-3n-E2B-it",
        max_seq_length: int = 1024,
        load_in_4bit: bool = True
    ):
        """Load Gemma 3N model with Unsloth optimizations"""
        
        logger.info(f"Loading Gemma 3N model: {model_name}")
        
        try:
            import torch
            if torch.cuda.is_available():
                from unsloth import FastModel
                logger.info("Using Unsloth optimizations (GPU mode)")
            else:
                logger.info("Using standard transformers (CPU mode)")
                # Use standard transformers approach
                return self._load_model_standard(model_name, max_seq_length, "float32")
            
            # Available Gemma 3N models
            available_models = [
                "unsloth/gemma-3n-E4B-it",      # 4B parameters
                "unsloth/gemma-3n-E2B-it",      # 2B parameters  
                "unsloth/gemma-3n-E4B-it-unsloth-bnb-4bit",  # 4-bit quantized
                "unsloth/gemma-3n-E2B-it-unsloth-bnb-4bit",  # 4-bit quantized
            ]
            
            if model_name not in available_models:
                logger.warning(f"Model {model_name} not in recommended list")
                logger.info(f"Available models: {available_models}")
            
            # Load model and tokenizer
            self.model, self.tokenizer = FastModel.from_pretrained(
                model_name=model_name,
                dtype=None,  # Auto detection
                max_seq_length=max_seq_length,
                load_in_4bit=load_in_4bit,
                full_finetuning=False,  # Use LoRA
            )
            
            logger.info("✓ Gemma 3N model loaded successfully")
            logger.info("✓ Model supports text, vision, and audio processing")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def configure_lora(
        self,
        r: int = 8,
        lora_alpha: int = 8,
        lora_dropout: float = 0.0,
        finetune_vision: bool = False,
        finetune_language: bool = True,
        finetune_attention: bool = True,
        finetune_mlp: bool = True
    ):
        """Configure LoRA for medical fine-tuning"""
        
        logger.info("Configuring LoRA for medical fine-tuning...")
        
        try:
            import torch
            
            # Check if GPU is available for Unsloth
            if torch.cuda.is_available():
                from unsloth import FastModel
                logger.info("Using Unsloth LoRA configuration (GPU mode)")
                
                # Configure LoRA parameters with Unsloth
                self.model = FastModel.get_peft_model(
                    self.model,
                    finetune_vision_layers=finetune_vision,     # Set True for multimodal
                    finetune_language_layers=finetune_language,  # Always True for text
                    finetune_attention_modules=finetune_attention,  # Good for medical reasoning
                    finetune_mlp_modules=finetune_mlp,          # Always True
                    
                    r=r,                    # LoRA rank - higher = more parameters
                    lora_alpha=lora_alpha,  # LoRA scaling factor
                    lora_dropout=lora_dropout,
                    bias="none",
                    random_state=3407,
                )
            else:
                # CPU fallback: Use standard PEFT library
                logger.info("Using standard PEFT LoRA configuration (CPU mode)")
                from peft import LoraConfig, get_peft_model, TaskType
                
                # Configure LoRA with standard PEFT library
                lora_config = LoraConfig(
                    task_type=TaskType.CAUSAL_LM,
                    inference_mode=False,
                    r=r,
                    lora_alpha=lora_alpha,
                    lora_dropout=lora_dropout,
                    bias="none",
                    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
                    fan_in_fan_out=False,
                    init_lora_weights=True,
                )
                
                self.model = get_peft_model(self.model, lora_config)
                logger.info("✓ PEFT LoRA configuration applied successfully")
            
            # Print trainable parameters
            total_params = sum(p.numel() for p in self.model.parameters())
            trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
            trainable_percentage = (trainable_params / total_params) * 100
            
            logger.info(f"Total parameters: {total_params:,}")
            logger.info(f"Trainable parameters: {trainable_params:,}")
            logger.info(f"Trainable percentage: {trainable_percentage:.2f}%")
            
            return True
            
        except Exception as e:
            logger.error(f"LoRA configuration failed: {e}")
            return False
    
    def prepare_medical_dataset(
        self, 
        agent_specialization: str,
        dataset_size: int = 3000,
        use_medical_data: bool = True
    ) -> Any:
        """Prepare medical training dataset"""
        
        logger.info(f"Preparing medical dataset for {agent_specialization}...")
        
        try:
            import torch
            from datasets import Dataset
            
            if use_medical_data:
                # Create medical-specific dataset
                medical_data = self._create_medical_training_data(
                    agent_specialization, dataset_size
                )
            else:
                # Use general dataset for testing
                from datasets import load_dataset
                dataset = load_dataset("mlabonne/FineTome-100k", split=f"train[:{dataset_size}]")
                
                # Handle data formatting based on GPU/CPU availability
                if torch.cuda.is_available():
                    try:
                        from unsloth.chat_templates import standardize_data_formats
                        medical_data = standardize_data_formats(dataset)
                    except ImportError:
                        # Fallback to manual conversion
                        medical_data = dataset
                else:
                    # CPU mode - use dataset as-is
                    medical_data = dataset
            
            logger.info(f"✓ Dataset prepared with {len(medical_data)} samples")
            return medical_data
            
        except Exception as e:
            logger.error(f"Dataset preparation failed: {e}")
            return None
    
    def _create_medical_training_data(
        self, 
        specialization: str, 
        size: int
    ) -> List[Dict]:
        """Create medical training data for specific specialization"""
        
        # Medical training data templates by specialization
        medical_templates = {
            "cardiology": [
                {
                    "user": "A 65-year-old patient presents with chest pain radiating to the left arm. What is your assessment?",
                    "assistant": "This presentation is highly suggestive of acute coronary syndrome, specifically myocardial infarction. Immediate steps should include: 1) Obtain 12-lead ECG within 10 minutes, 2) Check cardiac biomarkers (troponin), 3) Administer aspirin 325mg chewed, 4) Consider nitroglycerin if blood pressure stable, 5) Prepare for emergency cardiac catheterization if STEMI confirmed. Time is muscle - door-to-balloon time should be <90 minutes."
                },
                {
                    "user": "What are the key differences between STEMI and NSTEMI?",
                    "assistant": "Key differences between STEMI and NSTEMI:\n\nSTEMI (ST-Elevation MI):\n- Complete coronary artery occlusion\n- ST-elevation on ECG\n- Requires immediate reperfusion (PCI or thrombolytics)\n- Higher mortality risk\n- Door-to-balloon <90 minutes\n\nNSTEMI (Non-ST-Elevation MI):\n- Partial coronary artery occlusion\n- No ST-elevation (may have ST-depression or T-wave changes)\n- Managed with antiplatelet therapy and risk stratification\n- PCI within 12-72 hours based on risk\n- Lower immediate mortality but similar long-term prognosis"
                }
            ],
            "neurology": [
                {
                    "user": "A patient presents with sudden onset weakness on the right side and difficulty speaking. What is your immediate assessment?",
                    "assistant": "This presentation suggests acute stroke, likely affecting the left hemisphere. Immediate actions: 1) Activate stroke protocol, 2) Check time of last known normal, 3) Obtain CT brain urgently to rule out hemorrhage, 4) Assess NIHSS score, 5) If within window and no contraindications, consider IV tPA, 6) Blood pressure management (don't lower unless >220/120), 7) Swallow assessment before any oral intake. Time-critical condition - 'time is brain'."
                },
                {
                    "user": "What are the contraindications for tPA in stroke?",
                    "assistant": "Absolute contraindications for IV tPA in stroke:\n- Time >4.5 hours from symptom onset\n- Hemorrhage on CT\n- Previous stroke within 3 months\n- Major surgery within 2 weeks\n- GI/urinary bleeding within 3 weeks\n- Platelets <100,000\n- INR >1.7 or PT >15 seconds\n- Blood pressure >185/110 despite treatment\n- Rapidly improving symptoms\n- Seizure at stroke onset\n- Pregnancy\n\nRelative contraindications require careful risk-benefit analysis."
                }
            ],
            "emergency": [
                {
                    "user": "A patient arrives in cardiac arrest. Walk me through the initial management.",
                    "assistant": "Cardiac arrest management - ACLS protocol:\n\n1. Check responsiveness and pulse (≤10 seconds)\n2. Call for help, get AED/defibrillator\n3. Start high-quality CPR:\n   - 30:2 compression:ventilation ratio\n   - Rate 100-120/min, depth 2-2.4 inches\n   - Complete recoil, minimize interruptions\n4. Attach monitor/defibrillator\n5. Check rhythm:\n   - Shockable (VF/VT): Shock + CPR\n   - Non-shockable (PEA/Asystole): CPR + epinephrine\n6. Advanced airway when appropriate\n7. IV/IO access, epinephrine 1mg q3-5min\n8. Consider reversible causes (H's and T's)\n9. Continue until ROSC or decision to terminate"
                }
            ]
        }
        
        # Generate training data
        training_data = []
        base_data = medical_templates.get(specialization, medical_templates["emergency"])
        
        # Repeat and vary the base data to reach desired size
        for i in range(size):
            template = base_data[i % len(base_data)]
            
            conversation = {
                "conversations": [
                    {"role": "user", "content": template["user"]},
                    {"role": "assistant", "content": template["assistant"]}
                ],
                "source": f"hema3n_medical_{specialization}",
                "score": 4.8  # High quality medical content
            }
            
            training_data.append(conversation)
        
        from datasets import Dataset
        return Dataset.from_list(training_data)
    
    def train_medical_agent(
        self,
        dataset: Any,
        agent_name: str,
        num_epochs: int = 1,
        max_steps: int = 60,
        batch_size: int = 1,
        learning_rate: float = 2e-4,
        gradient_accumulation_steps: int = 4
    ) -> Dict:
        """Train medical agent with LoRA fine-tuning"""
        
        logger.info(f"Starting LoRA training for {agent_name}...")
        
        try:
            import torch
            from trl import SFTTrainer, SFTConfig
            
            # Setup chat template for Gemma 3N with GPU/CPU handling
            if torch.cuda.is_available():
                try:
                    from unsloth.chat_templates import get_chat_template, train_on_responses_only
                    logger.info("Using Unsloth chat templates (GPU mode)")
                    
                    # Setup chat template for Gemma 3N
                    self.tokenizer = get_chat_template(
                        self.tokenizer,
                        chat_template="gemma-3",
                    )
                    use_unsloth_templates = True
                except ImportError:
                    logger.warning("Unsloth not available, using standard templates")
                    use_unsloth_templates = False
            else:
                logger.info("Using standard templates (CPU mode)")
                use_unsloth_templates = False
            
            # Format dataset for training
            def formatting_prompts_func(examples):
                convos = examples["conversations"]
                texts = []
                for convo in convos:
                    if use_unsloth_templates:
                        # Use Unsloth formatting
                        text = self.tokenizer.apply_chat_template(
                            convo, 
                            tokenize=False, 
                            add_generation_prompt=False
                        ).removeprefix('<bos>')
                    else:
                        # Use standard formatting for CPU mode
                        text = ""
                        for msg in convo:
                            if msg["role"] == "user":
                                text += f"<start_of_turn>user\n{msg['content']}<end_of_turn>\n"
                            elif msg["role"] == "assistant":
                                text += f"<start_of_turn>model\n{msg['content']}<end_of_turn>\n"
                    texts.append(text)
                return {"text": texts}
            
            dataset = dataset.map(formatting_prompts_func, batched=True)
            
            # Configure training with CPU/GPU specific settings
            if torch.cuda.is_available():
                # GPU settings
                training_args = SFTConfig(
                    dataset_text_field="text",
                    per_device_train_batch_size=batch_size,
                    gradient_accumulation_steps=gradient_accumulation_steps,
                    warmup_steps=5,
                    max_steps=max_steps,
                    num_train_epochs=num_epochs,
                    learning_rate=learning_rate,
                    logging_steps=1,
                    optim="paged_adamw_8bit",
                    weight_decay=0.01,
                    lr_scheduler_type="linear",
                    seed=3407,
                    report_to="none",
                    output_dir=str(self.output_dir / agent_name),
                )
            else:
                # CPU settings - avoid GPU-specific optimizations
                training_args = SFTConfig(
                    dataset_text_field="text",
                    per_device_train_batch_size=batch_size,
                    gradient_accumulation_steps=gradient_accumulation_steps,
                    warmup_steps=5,
                    max_steps=max_steps,
                    num_train_epochs=num_epochs,
                    learning_rate=learning_rate,
                    logging_steps=1,
                    optim="adamw_torch",  # Use standard AdamW for CPU
                    weight_decay=0.01,
                    lr_scheduler_type="linear",
                    seed=3407,
                    report_to="none",
                    output_dir=str(self.output_dir / agent_name),
                    fp16=False,  # Disable half precision
                    bf16=False,  # Disable bfloat16
                    dataloader_pin_memory=False,  # Disable GPU memory pinning
                    use_cpu=True,  # Force CPU usage
                )
                logger.info("Using CPU-optimized training configuration")
            
            trainer = SFTTrainer(
                model=self.model,
                args=training_args,
                train_dataset=dataset,
                eval_dataset=None,
                processing_class=self.tokenizer,
            )
            
            # Train only on assistant responses (not user questions)
            if use_unsloth_templates:
                trainer = train_on_responses_only(
                    trainer,
                    instruction_part="<start_of_turn>user\n",
                    response_part="<start_of_turn>model\n",
                )
            else:
                # For CPU mode, training will include full conversations
                # This is acceptable for medical training data
                logger.info("Training on full conversations (CPU mode - no response-only filtering)")
            
            # Show memory stats before training
            self._show_memory_stats("Before training")
            
            # Train the model
            logger.info("🚀 Starting training...")
            trainer_stats = trainer.train()
            
            # Show memory stats after training
            self._show_memory_stats("After training")
            
            # Save the model
            model_path = self.output_dir / agent_name
            self.model.save_pretrained(str(model_path))
            self.tokenizer.save_pretrained(str(model_path))
            
            # Prepare training results
            results = {
                "agent_name": agent_name,
                "training_loss": trainer_stats.training_loss,
                "training_runtime": trainer_stats.metrics['train_runtime'],
                "training_samples_per_second": trainer_stats.metrics.get('train_samples_per_second', 0),
                "total_steps": max_steps,
                "model_path": str(model_path),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Save training results
            results_file = model_path / "training_results.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"✅ Training completed for {agent_name}")
            logger.info(f"📊 Training time: {results['training_runtime']:.1f} seconds")
            logger.info(f"📉 Final loss: {results['training_loss']:.4f}")
            
            return results
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise
    
    def _show_memory_stats(self, stage: str):
        """Show GPU memory statistics"""
        
        if not torch.cuda.is_available():
            return
        
        gc.collect()
        torch.cuda.empty_cache()
        
        gpu_stats = torch.cuda.get_device_properties(0)
        memory_used = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
        max_memory = round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)
        percentage = round(memory_used / max_memory * 100, 3)
        
        logger.info(f"📊 {stage} - GPU: {gpu_stats.name}")
        logger.info(f"📊 Memory used: {memory_used} GB / {max_memory} GB ({percentage}%)")
    
    def test_inference(self, test_prompt: str = None):
        """Test the fine-tuned model with medical inference"""
        
        if test_prompt is None:
            test_prompt = "A 45-year-old patient presents with severe chest pain. What is your immediate assessment and management plan?"
        
        logger.info("🧪 Testing medical inference...")
        
        try:
            from transformers import TextStreamer
            
            messages = [{
                "role": "user",
                "content": [{"type": "text", "text": test_prompt}]
            }]
            
            inputs = self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                return_tensors="pt",
                tokenize=True,
                return_dict=True,
            ).to("cuda")
            
            logger.info(f"Input: {test_prompt}")
            logger.info("Response:")
            
            _ = self.model.generate(
                **inputs,
                max_new_tokens=256,
                temperature=0.1,  # Lower temperature for medical accuracy
                top_p=0.95,
                top_k=64,
                streamer=TextStreamer(self.tokenizer, skip_prompt=True),
            )
            
        except Exception as e:
            logger.error(f"Inference test failed: {e}")

def main():
    """Main training script"""
    
    parser = argparse.ArgumentParser(description="HEMA3N Medical LoRA Fine-tuning with Gemma 3N")
    parser.add_argument("--agent", default="cardiology", 
                       help="Medical agent to train (cardiology, neurology, emergency)")
    parser.add_argument("--model", default="unsloth/gemma-3n-E2B-it",
                       help="Base Gemma 3N model to use")
    parser.add_argument("--epochs", type=int, default=1,
                       help="Number of training epochs")
    parser.add_argument("--steps", type=int, default=60,
                       help="Maximum training steps")
    parser.add_argument("--batch-size", type=int, default=1,
                       help="Training batch size")
    parser.add_argument("--learning-rate", type=float, default=2e-4,
                       help="Learning rate")
    parser.add_argument("--lora-rank", type=int, default=8,
                       help="LoRA rank parameter")
    parser.add_argument("--dataset-size", type=int, default=1000,
                       help="Size of training dataset")
    parser.add_argument("--medical-data", action="store_true",
                       help="Use medical-specific training data")
    parser.add_argument("--multimodal", action="store_true",
                       help="Enable vision fine-tuning (experimental)")
    parser.add_argument("--output-dir", default="./models/medical_agents",
                       help="Output directory for trained models")
    parser.add_argument("--test-only", action="store_true",
                       help="Only test inference, don't train")
    
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("🏥 HEMA3N Medical LoRA Fine-tuning with Gemma 3N")
    logger.info("=" * 70)
    
    # Initialize trainer
    trainer = MedicalGemma3NTrainer(args.output_dir)
    
    try:
        # Setup environment
        if not trainer.setup_environment():
            logger.error("❌ Environment setup failed")
            return 1
        
        # Load model
        if not trainer.load_gemma3n_model(args.model):
            logger.error("❌ Model loading failed")
            return 1
        
        # Configure LoRA
        if not trainer.configure_lora(
            r=args.lora_rank,
            lora_alpha=args.lora_rank,
            finetune_vision=args.multimodal
        ):
            logger.error("❌ LoRA configuration failed")
            return 1
        
        # Test inference only
        if args.test_only:
            trainer.test_inference()
            return 0
        
        # Prepare dataset
        dataset = trainer.prepare_medical_dataset(
            args.agent, 
            args.dataset_size,
            args.medical_data
        )
        
        if dataset is None:
            logger.error("❌ Dataset preparation failed")
            return 1
        
        # Train the model
        results = trainer.train_medical_agent(
            dataset,
            args.agent,
            num_epochs=args.epochs,
            max_steps=args.steps,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate
        )
        
        # Test inference
        trainer.test_inference()
        
        logger.info("\n" + "=" * 70)
        logger.info("🎉 MEDICAL LORA FINE-TUNING COMPLETED!")
        logger.info("=" * 70)
        logger.info(f"✅ Agent: {results['agent_name']}")
        logger.info(f"📊 Training time: {results['training_runtime']:.1f} seconds")
        logger.info(f"📉 Final loss: {results['training_loss']:.4f}")
        logger.info(f"💾 Model saved to: {results['model_path']}")
        logger.info("\n🚀 Your medical AI agent is ready for deployment!")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)