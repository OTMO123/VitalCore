#!/usr/bin/env python3
"""
LoRA Fine-tuning Script for HEMA3N Medical Agents

This script orchestrates the LoRA fine-tuning process for specialized medical agents
using the existing training infrastructure and medical datasets.

Usage:
    python scripts/train_medical_agents.py --agent cardiology --epochs 3
    python scripts/train_medical_agents.py --agent all --batch-size 2
"""

import asyncio
import argparse
import logging
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.modules.edge_ai.specialized_agent_trainer import (
    SpecializedAgentTrainer, 
    AgentTrainingConfig,
    MedicalDatasetRegistry,
    AGENT_TRAINING_CONFIGS
)
from app.ai.diagnosis_engine import AgentSpecialization

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LoRATrainingManager:
    """Manager for LoRA fine-tuning of medical agents"""
    
    def __init__(self, output_base_dir: str = "./models"):
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(exist_ok=True)
        self.trainer = SpecializedAgentTrainer()
        self.training_history = []
        
    async def train_single_agent(
        self,
        agent_name: str,
        epochs: int = 3,
        batch_size: int = 2,
        learning_rate: float = 2e-4,
        lora_rank: int = 16,
        custom_datasets: Optional[List[str]] = None
    ) -> Dict:
        """Train a single medical agent with LoRA fine-tuning"""
        
        logger.info(f"Starting LoRA training for {agent_name} agent")
        
        # Get agent configuration
        if agent_name not in AGENT_TRAINING_CONFIGS:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        config = AGENT_TRAINING_CONFIGS[agent_name]
        
        # Update configuration with provided parameters
        config.num_epochs = epochs
        config.batch_size = batch_size
        config.learning_rate = learning_rate
        config.lora_rank = lora_rank
        
        # Get recommended datasets for this agent
        if custom_datasets:
            datasets = custom_datasets
        else:
            datasets = MedicalDatasetRegistry.get_datasets_for_specialization(agent_name)
        
        logger.info(f"Using datasets: {datasets}")
        
        # Create output directory for this agent
        agent_output_dir = self.output_base_dir / agent_name
        agent_output_dir.mkdir(exist_ok=True)
        
        try:
            # Start training
            training_result = await self.trainer.train_specialized_agent(
                config=config,
                datasets=datasets,
                output_dir=str(agent_output_dir)
            )
            
            # Save training results
            results_file = agent_output_dir / "training_results.json"
            with open(results_file, 'w') as f:
                json.dump(training_result, f, indent=2, default=str)
            
            logger.info(f"Training completed for {agent_name}")
            logger.info(f"Results saved to: {results_file}")
            
            # Add to training history
            self.training_history.append({
                "agent": agent_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "result": training_result
            })
            
            return training_result
            
        except Exception as e:
            logger.error(f"Training failed for {agent_name}: {e}")
            raise
    
    async def train_multiple_agents(
        self,
        agent_names: List[str],
        **kwargs
    ) -> Dict[str, Dict]:
        """Train multiple agents sequentially"""
        
        results = {}
        
        for agent_name in agent_names:
            try:
                logger.info(f"Training agent {agent_name} ({agent_names.index(agent_name) + 1}/{len(agent_names)})")
                result = await self.train_single_agent(agent_name, **kwargs)
                results[agent_name] = result
                
                # Brief pause between trainings
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to train {agent_name}: {e}")
                results[agent_name] = {"error": str(e)}
                continue
        
        return results
    
    async def train_all_agents(self, **kwargs) -> Dict[str, Dict]:
        """Train all available medical agents"""
        
        all_agents = list(AGENT_TRAINING_CONFIGS.keys())
        logger.info(f"Training all {len(all_agents)} agents: {all_agents}")
        
        return await self.train_multiple_agents(all_agents, **kwargs)
    
    def get_training_summary(self) -> Dict:
        """Get summary of all training sessions"""
        
        return {
            "total_training_sessions": len(self.training_history),
            "training_history": self.training_history,
            "available_agents": list(AGENT_TRAINING_CONFIGS.keys()),
            "output_directory": str(self.output_base_dir)
        }

def create_custom_training_config(
    agent_name: str,
    specialization: str,
    epochs: int = 3,
    batch_size: int = 2,
    learning_rate: float = 2e-4,
    lora_rank: int = 16,
    lora_alpha: int = 32
) -> AgentTrainingConfig:
    """Create custom training configuration"""
    
    return AgentTrainingConfig(
        agent_name=f"{agent_name}_specialist",
        specialization=specialization,
        base_model="google/gemma-7b",  # or "microsoft/BioGPT" for medical domain
        max_length=2048,
        batch_size=batch_size,
        learning_rate=learning_rate,
        num_epochs=epochs,
        lora_rank=lora_rank,
        lora_alpha=lora_alpha,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"]  # LoRA target modules
    )

async def download_and_prepare_datasets():
    """Download and prepare medical datasets for training"""
    
    logger.info("Preparing medical datasets for training...")
    
    # This would implement actual dataset downloading in production
    # For now, we'll create mock data preparation
    
    datasets_info = {
        "pubmed_abstracts": {
            "status": "mock_ready",
            "samples": "6M+ medical abstracts (simulated)",
            "format": "json"
        },
        "medqa": {
            "status": "mock_ready", 
            "samples": "61K+ medical Q&A pairs (simulated)",
            "format": "json"
        },
        "symptom_disease_dataset": {
            "status": "mock_ready",
            "samples": "4.9K+ symptom-disease mappings (simulated)", 
            "format": "csv"
        },
        "mimic_iii": {
            "status": "requires_credentials",
            "samples": "40K+ ICU patients",
            "note": "Requires PhysioNet credentials"
        }
    }
    
    logger.info("Dataset preparation summary:")
    for dataset, info in datasets_info.items():
        logger.info(f"  {dataset}: {info['status']} - {info['samples']}")
    
    return datasets_info

def setup_training_environment():
    """Setup training environment and dependencies"""
    
    logger.info("Setting up LoRA training environment...")
    
    # Check for required packages
    required_packages = [
        "torch", "transformers", "peft", "datasets", 
        "accelerate", "bitsandbytes"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✓ {package} available")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"✗ {package} missing")
    
    if missing_packages:
        logger.error(f"Missing required packages: {missing_packages}")
        logger.info("Install with: pip install torch transformers peft datasets accelerate bitsandbytes")
        return False
    
    # Check GPU availability
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            logger.info(f"✓ CUDA available with {gpu_count} GPU(s)")
            for i in range(gpu_count):
                gpu_name = torch.cuda.get_device_name(i)
                logger.info(f"  GPU {i}: {gpu_name}")
        else:
            logger.warning("✗ CUDA not available - will use CPU (slower)")
    except Exception as e:
        logger.warning(f"Could not check GPU availability: {e}")
    
    logger.info("Training environment setup complete")
    return True

async def main():
    """Main training script entry point"""
    
    parser = argparse.ArgumentParser(description="LoRA Fine-tuning for HEMA3N Medical Agents")
    parser.add_argument("--agent", default="cardiology", 
                       help="Agent to train (cardiology, neurology, emergency, etc.) or 'all'")
    parser.add_argument("--epochs", type=int, default=3,
                       help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=2,
                       help="Training batch size")
    parser.add_argument("--learning-rate", type=float, default=2e-4,
                       help="Learning rate for training")
    parser.add_argument("--lora-rank", type=int, default=16,
                       help="LoRA rank parameter")
    parser.add_argument("--output-dir", default="./models",
                       help="Output directory for trained models")
    parser.add_argument("--datasets", nargs="+", 
                       help="Custom datasets to use (optional)")
    parser.add_argument("--setup-only", action="store_true",
                       help="Only setup environment, don't train")
    parser.add_argument("--prepare-data", action="store_true",
                       help="Prepare datasets before training")
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("HEMA3N LoRA Fine-tuning Script")
    logger.info("=" * 60)
    
    # Setup environment
    if not setup_training_environment():
        logger.error("Environment setup failed")
        return 1
    
    if args.setup_only:
        logger.info("Environment setup complete - exiting as requested")
        return 0
    
    # Prepare datasets if requested
    if args.prepare_data:
        await download_and_prepare_datasets()
    
    # Initialize training manager
    training_manager = LoRATrainingManager(args.output_dir)
    
    try:
        # Train agents
        if args.agent == "all":
            logger.info("Training all medical agents with LoRA fine-tuning")
            results = await training_manager.train_all_agents(
                epochs=args.epochs,
                batch_size=args.batch_size,
                learning_rate=args.learning_rate,
                lora_rank=args.lora_rank,
                custom_datasets=args.datasets
            )
        else:
            logger.info(f"Training {args.agent} agent with LoRA fine-tuning")
            result = await training_manager.train_single_agent(
                args.agent,
                epochs=args.epochs,
                batch_size=args.batch_size,
                learning_rate=args.learning_rate,
                lora_rank=args.lora_rank,
                custom_datasets=args.datasets
            )
            results = {args.agent: result}
        
        # Print training summary
        logger.info("\n" + "=" * 60)
        logger.info("TRAINING COMPLETED")
        logger.info("=" * 60)
        
        for agent, result in results.items():
            if "error" in result:
                logger.error(f"{agent}: FAILED - {result['error']}")
            else:
                logger.info(f"{agent}: SUCCESS")
                logger.info(f"  Training samples: {result.get('training_samples', 'N/A')}")
                logger.info(f"  Final loss: {result.get('training_loss', 'N/A')}")
                logger.info(f"  Model size: {result.get('model_size', 'N/A')}")
        
        # Save overall summary
        summary = training_manager.get_training_summary()
        summary_file = Path(args.output_dir) / "training_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"\nTraining summary saved to: {summary_file}")
        logger.info("🎉 LoRA fine-tuning completed successfully!")
        
        return 0
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)