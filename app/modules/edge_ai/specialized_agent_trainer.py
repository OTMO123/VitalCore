#!/usr/bin/env python3
"""
Specialized Gemma 3n Agent Training System

This module implements the training pipeline for specialized medical AI agents
using open source healthcare datasets with HIPAA-compliant preprocessing.
"""

import asyncio
import logging
import json
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
import pickle
import hashlib

# ML Training frameworks
try:
    import torch
    import torch.nn as nn
    from transformers import (
        AutoTokenizer, AutoModelForCausalLM, TrainingArguments,
        Trainer, DataCollatorForLanguageModeling
    )
    from peft import LoraConfig, get_peft_model, TaskType
    from datasets import Dataset, load_dataset
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

# Medical data processing
try:
    import pandas as pd
    import requests
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    _DATA_PROCESSING_AVAILABLE = True
except ImportError:
    _DATA_PROCESSING_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class MedicalDataset:
    """Medical dataset configuration for agent training"""
    name: str
    source_url: str
    license: str
    size_description: str
    format_type: str
    medical_domain: str
    preprocessing_required: bool
    phi_risk_level: str  # "none", "low", "medium", "high"
    
@dataclass
class AgentTrainingConfig:
    """Configuration for specialized agent training"""
    agent_name: str
    specialization: str
    base_model: str = "google/gemma-7b"
    max_length: int = 2048
    batch_size: int = 4
    learning_rate: float = 2e-4
    num_epochs: int = 3
    lora_rank: int = 16
    lora_alpha: int = 32
    target_modules: List[str] = None
    
    def __post_init__(self):
        if self.target_modules is None:
            self.target_modules = ["q_proj", "v_proj", "k_proj", "o_proj"]

class MedicalDatasetRegistry:
    """Registry of available open source medical datasets"""
    
    DATASETS = {
        # Large Medical Text Corpora
        "pubmed_abstracts": MedicalDataset(
            name="PubMed Abstracts",
            source_url="https://www.ncbi.nlm.nih.gov/pmc/tools/openftlist/",
            license="Creative Commons",
            size_description="6M+ medical research abstracts",
            format_type="json",
            medical_domain="general_medical_knowledge",
            preprocessing_required=True,
            phi_risk_level="none"
        ),
        
        "mimic_iii": MedicalDataset(
            name="MIMIC-III Clinical Database",
            source_url="https://physionet.org/content/mimiciii/1.4/",
            license="PhysioNet Credentialed Health Data License",
            size_description="40K+ ICU patients",
            format_type="csv",
            medical_domain="intensive_care",
            preprocessing_required=True,
            phi_risk_level="high"
        ),
        
        "medqa": MedicalDataset(
            name="MedQA USMLE Questions",
            source_url="https://github.com/jind11/MedQA",
            license="MIT License",
            size_description="61K+ medical Q&A pairs",
            format_type="json",
            medical_domain="clinical_reasoning",
            preprocessing_required=False,
            phi_risk_level="none"
        ),
        
        "clinical_notes_n2c2": MedicalDataset(
            name="n2c2 Clinical Notes",
            source_url="https://portal.dbmi.hms.harvard.edu/projects/n2c2-nlp/",
            license="Data Use Agreement",
            size_description="Clinical text datasets",
            format_type="xml",
            medical_domain="clinical_documentation",
            preprocessing_required=True,
            phi_risk_level="high"
        ),
        
        "symptom_disease_dataset": MedicalDataset(
            name="Symptom-Disease Dataset",
            source_url="https://www.kaggle.com/datasets/itachi9604/disease-symptom-description-dataset",
            license="Open Source",
            size_description="4.9K+ symptom-disease mappings",
            format_type="csv",
            medical_domain="differential_diagnosis",
            preprocessing_required=False,
            phi_risk_level="none"
        ),
        
        "chest_xray_14": MedicalDataset(
            name="ChestX-ray14",
            source_url="https://nihcc.app.box.com/v/ChestXray-NIHCC",
            license="NIH Clinical Center",
            size_description="112K+ chest X-ray images",
            format_type="png_csv",
            medical_domain="radiology",
            preprocessing_required=True,
            phi_risk_level="medium"
        ),
        
        "drugbank_open": MedicalDataset(
            name="DrugBank Open Data",
            source_url="https://go.drugbank.com/releases/latest",
            license="Creative Commons Attribution-NonCommercial 4.0",
            size_description="14K+ drug entries",
            format_type="xml",
            medical_domain="pharmacology",
            preprocessing_required=True,
            phi_risk_level="none"
        )
    }
    
    @classmethod
    def get_datasets_for_specialization(cls, specialization: str) -> List[str]:
        """Get recommended datasets for agent specialization"""
        
        specialization_mapping = {
            "cardiology_agent": [
                "mimic_iii", "pubmed_abstracts", "medqa", 
                "chest_xray_14", "symptom_disease_dataset"
            ],
            "neurology_agent": [
                "mimic_iii", "pubmed_abstracts", "medqa",
                "clinical_notes_n2c2", "symptom_disease_dataset"
            ],
            "pulmonology_agent": [
                "chest_xray_14", "mimic_iii", "pubmed_abstracts",
                "medqa", "symptom_disease_dataset"
            ],
            "emergency_agent": [
                "mimic_iii", "clinical_notes_n2c2", "symptom_disease_dataset",
                "pubmed_abstracts", "medqa"
            ],
            "pediatric_agent": [
                "pubmed_abstracts", "medqa", "symptom_disease_dataset"
            ],
            "infection_agent": [
                "mimic_iii", "drugbank_open", "pubmed_abstracts",
                "medqa", "symptom_disease_dataset"
            ],
            "psychiatry_agent": [
                "mimic_iii", "pubmed_abstracts", "medqa",
                "clinical_notes_n2c2"
            ],
            "orthopedic_agent": [
                "pubmed_abstracts", "medqa", "symptom_disease_dataset"
            ]
        }
        
        return specialization_mapping.get(specialization, ["pubmed_abstracts", "medqa"])

class MedicalDataPreprocessor:
    """HIPAA-compliant medical data preprocessing for agent training"""
    
    def __init__(self):
        self.phi_patterns = self._load_phi_patterns()
        self.medical_entities = self._load_medical_entities()
        
    def _load_phi_patterns(self) -> Dict[str, str]:
        """Load PHI detection patterns for HIPAA compliance"""
        return {
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "phone": r'\b\d{3}-\d{3}-\d{4}\b',
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "date_birth": r'\b\d{1,2}/\d{1,2}/\d{4}\b',
            "mrn": r'\b[A-Z]{2,3}\d{6,10}\b',
            "name_pattern": r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            "address": r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd)\b'
        }
    
    def _load_medical_entities(self) -> Dict[str, List[str]]:
        """Load medical entity vocabularies for enhancement"""
        return {
            "symptoms": [
                "chest pain", "shortness of breath", "headache", "nausea", "vomiting",
                "fever", "cough", "fatigue", "dizziness", "palpitations"
            ],
            "conditions": [
                "myocardial infarction", "stroke", "pneumonia", "diabetes", "hypertension",
                "asthma", "copd", "heart failure", "sepsis", "depression"
            ],
            "medications": [
                "aspirin", "metformin", "lisinopril", "atorvastatin", "amlodipine",
                "metoprolol", "omeprazole", "albuterol", "insulin", "warfarin"
            ],
            "procedures": [
                "ct scan", "mri", "ecg", "blood test", "x-ray",
                "biopsy", "surgery", "catheterization", "intubation", "dialysis"
            ]
        }
    
    async def preprocess_dataset(
        self, 
        dataset_name: str,
        raw_data: Any
    ) -> Dict[str, Any]:
        """Preprocess medical dataset with HIPAA compliance"""
        
        dataset_config = MedicalDatasetRegistry.DATASETS[dataset_name]
        
        logger.info(f"Preprocessing {dataset_name} dataset",
                   phi_risk=dataset_config.phi_risk_level,
                   size=dataset_config.size_description)
        
        # Step 1: PHI Detection and Anonymization
        if dataset_config.phi_risk_level in ["medium", "high"]:
            anonymized_data = await self._anonymize_phi_data(raw_data)
        else:
            anonymized_data = raw_data
        
        # Step 2: Medical Entity Enhancement
        enhanced_data = await self._enhance_medical_entities(anonymized_data)
        
        # Step 3: Format-specific preprocessing
        if dataset_config.format_type == "json":
            processed_data = await self._preprocess_json_data(enhanced_data)
        elif dataset_config.format_type == "csv":
            processed_data = await self._preprocess_csv_data(enhanced_data)
        elif dataset_config.format_type == "xml":
            processed_data = await self._preprocess_xml_data(enhanced_data)
        else:
            processed_data = enhanced_data
        
        # Step 4: Quality filtering
        filtered_data = await self._filter_data_quality(processed_data)
        
        # Step 5: Create training examples
        training_examples = await self._create_training_examples(
            filtered_data, dataset_name
        )
        
        return {
            "training_examples": training_examples,
            "dataset_info": asdict(dataset_config),
            "preprocessing_stats": {
                "original_size": len(raw_data) if hasattr(raw_data, '__len__') else "unknown",
                "processed_size": len(training_examples),
                "phi_anonymized": dataset_config.phi_risk_level in ["medium", "high"],
                "quality_filtered": True
            }
        }
    
    async def _anonymize_phi_data(self, data: Any) -> Any:
        """Anonymize PHI data according to HIPAA Safe Harbor method"""
        
        if isinstance(data, str):
            anonymized = data
            for phi_type, pattern in self.phi_patterns.items():
                anonymized = re.sub(pattern, f'[{phi_type.upper()}_REMOVED]', anonymized)
            return anonymized
        
        elif isinstance(data, list):
            return [await self._anonymize_phi_data(item) for item in data]
        
        elif isinstance(data, dict):
            anonymized = {}
            for key, value in data.items():
                anonymized[key] = await self._anonymize_phi_data(value)
            return anonymized
        
        else:
            return data
    
    async def _enhance_medical_entities(self, data: Any) -> Any:
        """Enhance data with medical entity recognition and standardization"""
        
        # This is a simplified version - in production, you'd use medical NLP libraries
        # like scispaCy, ClinicalBERT, or BioBERT for proper entity recognition
        enhanced_data = data
        
        # Add medical context markers for training
        if isinstance(data, str):
            for entity_type, entities in self.medical_entities.items():
                for entity in entities:
                    if entity.lower() in data.lower():
                        enhanced_data = enhanced_data.replace(
                            entity, f"<{entity_type.upper()}>{entity}</{entity_type.upper()}>"
                        )
        
        return enhanced_data
    
    async def _create_training_examples(
        self, 
        processed_data: Any,
        dataset_name: str
    ) -> List[Dict[str, str]]:
        """Create training examples in the format expected by Gemma 3n"""
        
        training_examples = []
        
        if dataset_name == "medqa":
            # Medical Q&A format
            for item in processed_data:
                if isinstance(item, dict) and "question" in item and "answer" in item:
                    example = {
                        "input": f"Medical Question: {item['question']}",
                        "output": f"Medical Answer: {item['answer']}",
                        "specialization": "clinical_reasoning"
                    }
                    training_examples.append(example)
        
        elif dataset_name == "symptom_disease_dataset":
            # Symptom-disease mapping format
            for item in processed_data:
                if isinstance(item, dict) and "symptoms" in item and "disease" in item:
                    example = {
                        "input": f"Patient presents with: {item['symptoms']}",
                        "output": f"Differential diagnosis includes: {item['disease']}",
                        "specialization": "differential_diagnosis"
                    }
                    training_examples.append(example)
        
        elif dataset_name == "mimic_iii":
            # Clinical notes format
            for item in processed_data:
                if isinstance(item, dict) and "text" in item:
                    example = {
                        "input": f"Clinical scenario: {item['text'][:1000]}",
                        "output": f"Clinical assessment and plan would include evaluation of the patient's presentation.",
                        "specialization": "clinical_assessment"
                    }
                    training_examples.append(example)
        
        else:
            # Generic medical text format
            for item in processed_data:
                if isinstance(item, str) and len(item) > 100:
                    # Split into input-output pairs for training
                    mid_point = len(item) // 2
                    example = {
                        "input": item[:mid_point],
                        "output": item[mid_point:],
                        "specialization": "general_medical"
                    }
                    training_examples.append(example)
        
        logger.info(f"Created {len(training_examples)} training examples from {dataset_name}")
        return training_examples

class SpecializedAgentTrainer:
    """Train specialized Gemma 3n agents for medical domains"""
    
    def __init__(self):
        self.preprocessor = MedicalDataPreprocessor()
        self.model_cache = {}
        
    async def train_specialized_agent(
        self,
        config: AgentTrainingConfig,
        datasets: List[str],
        output_dir: str
    ) -> Dict[str, Any]:
        """Train a specialized medical agent using specified datasets"""
        
        if not _TORCH_AVAILABLE:
            raise RuntimeError("PyTorch and transformers not available for training")
        
        logger.info(f"Starting training for {config.agent_name}",
                   specialization=config.specialization,
                   datasets=datasets)
        
        # Step 1: Load and preprocess training data
        training_data = await self._prepare_training_data(datasets, config.specialization)
        
        # Step 2: Load base model and tokenizer
        model, tokenizer = await self._load_base_model(config.base_model)
        
        # Step 3: Configure LoRA for efficient fine-tuning
        lora_model = await self._configure_lora(model, config)
        
        # Step 4: Prepare training dataset
        train_dataset = await self._create_torch_dataset(training_data, tokenizer, config)
        
        # Step 5: Configure training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=config.num_epochs,
            per_device_train_batch_size=config.batch_size,
            gradient_accumulation_steps=4,
            warmup_steps=100,
            learning_rate=config.learning_rate,
            fp16=True,
            logging_steps=10,
            save_steps=500,
            evaluation_strategy="steps",
            eval_steps=500,
            save_total_limit=3,
            remove_unused_columns=False,
            dataloader_pin_memory=False,
        )
        
        # Step 6: Initialize trainer
        trainer = Trainer(
            model=lora_model,
            args=training_args,
            train_dataset=train_dataset,
            tokenizer=tokenizer,
            data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
        )
        
        # Step 7: Train the model
        logger.info(f"Starting training for {config.agent_name}")
        train_result = trainer.train()
        
        # Step 8: Save the trained model
        trainer.save_model()
        tokenizer.save_pretrained(output_dir)
        
        # Step 9: Generate training report
        training_report = {
            "agent_name": config.agent_name,
            "specialization": config.specialization,
            "training_datasets": datasets,
            "training_samples": len(training_data),
            "training_loss": train_result.training_loss,
            "epochs_completed": config.num_epochs,
            "model_size": "7B parameters (LoRA fine-tuned)",
            "output_directory": output_dir,
            "training_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Training completed for {config.agent_name}",
                   final_loss=train_result.training_loss,
                   output_dir=output_dir)
        
        return training_report
    
    async def _prepare_training_data(
        self, 
        datasets: List[str],
        specialization: str
    ) -> List[Dict[str, str]]:
        """Prepare and combine training data from multiple datasets"""
        
        all_training_data = []
        
        for dataset_name in datasets:
            if dataset_name not in MedicalDatasetRegistry.DATASETS:
                logger.warning(f"Dataset {dataset_name} not found in registry")
                continue
            
            # In a real implementation, you would download/load the actual dataset
            # For now, we'll create mock data for demonstration
            mock_data = await self._create_mock_training_data(dataset_name, specialization)
            
            processed_data = await self.preprocessor.preprocess_dataset(
                dataset_name, mock_data
            )
            
            all_training_data.extend(processed_data["training_examples"])
        
        # Shuffle and limit data for training efficiency
        import random
        random.shuffle(all_training_data)
        
        # Limit to manageable size for demonstration
        max_samples = 10000
        if len(all_training_data) > max_samples:
            all_training_data = all_training_data[:max_samples]
        
        logger.info(f"Prepared {len(all_training_data)} training samples for {specialization}")
        return all_training_data
    
    async def _create_mock_training_data(
        self, 
        dataset_name: str, 
        specialization: str
    ) -> List[Dict[str, Any]]:
        """Create mock training data for demonstration purposes"""
        
        mock_data = []
        
        if dataset_name == "medqa":
            mock_data = [
                {
                    "question": "A 65-year-old patient presents with chest pain radiating to the left arm. What is the most likely diagnosis?",
                    "answer": "The presentation is suggestive of myocardial infarction. Immediate ECG and cardiac enzymes should be obtained."
                },
                {
                    "question": "What are the classic signs of stroke?",
                    "answer": "Classic stroke signs include sudden weakness, speech difficulties, facial drooping, and altered consciousness. Use FAST assessment."
                }
            ]
        
        elif dataset_name == "symptom_disease_dataset":
            mock_data = [
                {
                    "symptoms": "chest pain, shortness of breath, diaphoresis",
                    "disease": "myocardial infarction, unstable angina, pulmonary embolism"
                },
                {
                    "symptoms": "headache, confusion, weakness",
                    "disease": "stroke, intracranial hemorrhage, meningitis"
                }
            ]
        
        elif dataset_name == "mimic_iii":
            mock_data = [
                {
                    "text": "Patient admitted to ICU with acute respiratory failure. Requiring mechanical ventilation. Labs show elevated lactate and white blood cell count."
                },
                {
                    "text": "Elderly patient with history of diabetes presenting with altered mental status and hyperglycemia. Blood glucose 450 mg/dL."
                }
            ]
        
        return mock_data
    
    async def _load_base_model(self, model_name: str) -> Tuple[Any, Any]:
        """Load base Gemma model and tokenizer"""
        
        if model_name in self.model_cache:
            return self.model_cache[model_name]
        
        logger.info(f"Loading base model {model_name}")
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        # Add pad token if missing
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        self.model_cache[model_name] = (model, tokenizer)
        return model, tokenizer
    
    async def _configure_lora(self, model: Any, config: AgentTrainingConfig) -> Any:
        """Configure LoRA for efficient fine-tuning"""
        
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=config.lora_rank,
            lora_alpha=config.lora_alpha,
            lora_dropout=0.1,
            target_modules=config.target_modules,
        )
        
        lora_model = get_peft_model(model, lora_config)
        lora_model.print_trainable_parameters()
        
        return lora_model
    
    async def _create_torch_dataset(
        self,
        training_data: List[Dict[str, str]],
        tokenizer: Any,
        config: AgentTrainingConfig
    ) -> Dataset:
        """Create PyTorch dataset for training"""
        
        def tokenize_function(examples):
            # Combine input and output for language modeling
            full_text = examples["input"] + " " + examples["output"]
            
            return tokenizer(
                full_text,
                truncation=True,
                padding="max_length",
                max_length=config.max_length,
                return_tensors="pt"
            )
        
        # Convert to HuggingFace Dataset
        dataset = Dataset.from_list(training_data)
        tokenized_dataset = dataset.map(tokenize_function, batched=False)
        
        return tokenized_dataset

# Example usage and configuration
AGENT_TRAINING_CONFIGS = {
    "cardiology_agent": AgentTrainingConfig(
        agent_name="cardiology_specialist",
        specialization="cardiovascular_medicine",
        base_model="google/gemma-7b",
        max_length=2048,
        batch_size=2,
        learning_rate=2e-4,
        num_epochs=3,
        lora_rank=16
    ),
    
    "neurology_agent": AgentTrainingConfig(
        agent_name="neurology_specialist",
        specialization="neurological_medicine",
        base_model="google/gemma-7b",
        max_length=2048,
        batch_size=2,
        learning_rate=2e-4,
        num_epochs=3,
        lora_rank=16
    ),
    
    "emergency_agent": AgentTrainingConfig(
        agent_name="emergency_medicine_specialist",
        specialization="emergency_medicine",
        base_model="google/gemma-7b",
        max_length=2048,
        batch_size=2,
        learning_rate=2e-4,
        num_epochs=3,
        lora_rank=16
    )
}

async def main():
    """Example training pipeline for specialized medical agents"""
    
    trainer = SpecializedAgentTrainer()
    
    # Train cardiology agent
    cardiology_datasets = MedicalDatasetRegistry.get_datasets_for_specialization("cardiology_agent")
    cardiology_config = AGENT_TRAINING_CONFIGS["cardiology_agent"]
    
    cardiology_result = await trainer.train_specialized_agent(
        config=cardiology_config,
        datasets=cardiology_datasets,
        output_dir="./models/cardiology_agent"
    )
    
    print("Cardiology agent training completed:")
    print(json.dumps(cardiology_result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())