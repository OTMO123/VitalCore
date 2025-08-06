"""
Medical NER Microservice for Healthcare Platform

Production-ready containerized service for medical named entity recognition
with SNOMED CT and ICD-10 mapping capabilities.
"""
import os
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List, Tuple
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import structlog
import redis.asyncio as redis
import spacy
from spacy import displacy

# Configure structured logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger()

class HealthResponse(BaseModel):
    status: str
    service: str
    model_loaded: bool
    memory_usage_mb: float
    supported_entity_types: List[str]
    version: str

class NERRequest(BaseModel):
    text: str
    extract_snomed: bool = True
    extract_icd: bool = True
    confidence_threshold: float = 0.7
    max_entities: int = 100

class MedicalEntity(BaseModel):
    text: str
    label: str
    start_pos: int
    end_pos: int
    confidence: float
    snomed_code: Optional[str] = None
    snomed_description: Optional[str] = None
    icd_code: Optional[str] = None
    icd_description: Optional[str] = None

class NERResponse(BaseModel):
    request_id: str
    entities: List[MedicalEntity]
    processing_time_ms: float
    text_length: int
    entity_count: int
    entity_density: float  # entities per 100 characters

class MedicalNERService:
    """Enterprise Medical NER service with healthcare terminology mapping."""
    
    def __init__(self):
        self.nlp_model = None
        self.redis_client = None
        self.model_loaded = False
        self.memory_usage_mb = 0.0
        self.supported_entity_types = []
        
        # Medical terminology mappings (simplified for demo)
        self.snomed_mappings = {
            "fever": ("386661006", "Fever (finding)"),
            "headache": ("25064002", "Headache (finding)"),
            "nausea": ("422587007", "Nausea (finding)"),
            "cough": ("49727002", "Cough (finding)"),
            "pain": ("22253000", "Pain (finding)"),
            "hypertension": ("38341003", "Hypertensive disorder (disorder)"),
            "diabetes": ("73211009", "Diabetes mellitus (disorder)"),
            "asthma": ("195967001", "Asthma (disorder)")
        }
        
        self.icd_mappings = {
            "fever": ("R50.9", "Fever, unspecified"),
            "headache": ("R51", "Headache"),
            "nausea": ("R11.0", "Nausea"),
            "cough": ("R05", "Cough"),
            "pain": ("R52", "Pain, not elsewhere classified"),
            "hypertension": ("I10", "Essential hypertension"),
            "diabetes": ("E11.9", "Type 2 diabetes mellitus without complications"),
            "asthma": ("J45.9", "Asthma, unspecified")
        }
        
    async def initialize(self):
        """Initialize spaCy model and Redis connection."""
        try:
            # Initialize Redis connection
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/3")
            self.redis_client = redis.from_url(redis_url)
            await self.redis_client.ping()
            logger.info("Redis connection established")
            
            # Load spaCy model for medical NER
            await self._load_nlp_model()
            
            logger.info("Medical NER service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Medical NER service: {e}")
            raise
    
    async def _load_nlp_model(self):
        """Load spaCy model for medical entity recognition."""
        try:
            # Load English model
            model_name = os.getenv("SPACY_MODEL", "en_core_web_sm")
            self.nlp_model = spacy.load(model_name)
            
            # Add custom medical entity patterns
            await self._add_medical_patterns()
            
            # Set supported entity types
            self.supported_entity_types = [
                "SYMPTOM", "DISEASE", "MEDICATION", "ANATOMY", 
                "PROCEDURE", "LAB_VALUE", "DOSAGE"
            ]
            
            import psutil
            self.memory_usage_mb = psutil.Process().memory_info().rss / 1024 / 1024
            self.model_loaded = True
            
            logger.info(f"spaCy model {model_name} loaded, memory: {self.memory_usage_mb:.1f}MB")
            
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
            self.model_loaded = False
            raise
    
    async def _add_medical_patterns(self):
        """Add medical entity patterns to spaCy model."""
        try:
            from spacy.matcher import Matcher
            
            # Initialize matcher
            matcher = Matcher(self.nlp_model.vocab)
            
            # Define medical patterns
            symptom_patterns = [
                [{"LOWER": {"IN": ["fever", "headache", "nausea", "cough", "pain"]}}],
                [{"LOWER": "sore"}, {"LOWER": "throat"}],
                [{"LOWER": "shortness"}, {"LOWER": "of"}, {"LOWER": "breath"}]
            ]
            
            medication_patterns = [
                [{"LOWER": {"IN": ["ibuprofen", "acetaminophen", "aspirin", "metformin"]}}],
                [{"LOWER": "mg"}],  # Dosage indicator
                [{"LIKE_NUM": True}, {"LOWER": "mg"}]  # Number + mg
            ]
            
            # Add patterns to matcher
            matcher.add("SYMPTOM", symptom_patterns)
            matcher.add("MEDICATION", medication_patterns)
            
            # Store matcher for use in processing
            self.matcher = matcher
            
        except Exception as e:
            logger.warning(f"Failed to add medical patterns: {e}")
    
    async def extract_medical_entities(self, request: NERRequest) -> NERResponse:
        """Extract medical entities from text."""
        import time
        import uuid
        
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            # Check cache first
            cache_key = f"ner:medical:{hash(request.text)}:{request.confidence_threshold}"
            cached_result = await self.redis_client.get(cache_key)
            if cached_result:
                logger.info("Returning cached NER result")
                import json
                return NERResponse(**json.loads(cached_result))
            
            # Process text with spaCy
            doc = self.nlp_model(request.text)
            
            entities = []
            
            # Extract standard spaCy entities
            for ent in doc.ents:
                if len(entities) >= request.max_entities:
                    break
                    
                # Map spaCy labels to medical categories
                medical_label = self._map_to_medical_category(ent.label_)
                if medical_label:
                    confidence = 0.85  # spaCy doesn't provide confidence scores by default
                    
                    if confidence >= request.confidence_threshold:
                        # Get SNOMED and ICD mappings
                        snomed_code, snomed_desc = None, None
                        icd_code, icd_desc = None, None
                        
                        if request.extract_snomed:
                            snomed_code, snomed_desc = self._get_snomed_mapping(ent.text.lower())
                        
                        if request.extract_icd:
                            icd_code, icd_desc = self._get_icd_mapping(ent.text.lower())
                        
                        entities.append(MedicalEntity(
                            text=ent.text,
                            label=medical_label,
                            start_pos=ent.start_char,
                            end_pos=ent.end_char,
                            confidence=confidence,
                            snomed_code=snomed_code,
                            snomed_description=snomed_desc,
                            icd_code=icd_code,
                            icd_description=icd_desc
                        ))
            
            # Extract additional medical patterns using matcher
            if hasattr(self, 'matcher'):
                matches = self.matcher(doc)
                for match_id, start, end in matches:
                    if len(entities) >= request.max_entities:
                        break
                    
                    span = doc[start:end]
                    label = self.nlp_model.vocab.strings[match_id]
                    
                    # Avoid duplicates
                    if not any(e.start_pos == span.start_char for e in entities):
                        entities.append(MedicalEntity(
                            text=span.text,
                            label=label,
                            start_pos=span.start_char,
                            end_pos=span.end_char,
                            confidence=0.8,
                            snomed_code=None,
                            snomed_description=None,
                            icd_code=None,
                            icd_description=None
                        ))
            
            processing_time = (time.time() - start_time) * 1000
            entity_density = (len(entities) / len(request.text)) * 100 if request.text else 0
            
            response = NERResponse(
                request_id=request_id,
                entities=entities,
                processing_time_ms=processing_time,
                text_length=len(request.text),
                entity_count=len(entities),
                entity_density=entity_density
            )
            
            # Cache result for 1 hour
            await self.redis_client.setex(
                cache_key,
                3600,
                response.model_dump_json()
            )
            
            logger.info(
                f"Medical NER completed",
                request_id=request_id,
                text_length=len(request.text),
                entity_count=len(entities),
                processing_time_ms=processing_time
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to extract medical entities: {e}")
            raise HTTPException(status_code=500, detail="Medical NER processing failed")
    
    def _map_to_medical_category(self, spacy_label: str) -> Optional[str]:
        """Map spaCy entity labels to medical categories."""
        mapping = {
            "PERSON": None,  # Skip person names for privacy
            "ORG": None,     # Skip organizations
            "GPE": None,     # Skip geo-political entities
            "DATE": None,    # Skip dates
            "TIME": None,    # Skip times
            "MONEY": None,   # Skip money
            "PERCENT": None, # Skip percentages
            "CARDINAL": "LAB_VALUE",  # Numbers might be lab values
            "ORDINAL": None,
            "QUANTITY": "DOSAGE"  # Quantities might be dosages
        }
        
        return mapping.get(spacy_label, "UNKNOWN")
    
    def _get_snomed_mapping(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Get SNOMED CT code and description for medical term."""
        return self.snomed_mappings.get(text, (None, None))
    
    def _get_icd_mapping(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Get ICD-10 code and description for medical term."""
        return self.icd_mappings.get(text, (None, None))
    
    async def health_check(self) -> HealthResponse:
        """Service health check."""
        import psutil
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        return HealthResponse(
            status="healthy" if self.model_loaded else "initializing",
            service="medical-ner",
            model_loaded=self.model_loaded,
            memory_usage_mb=current_memory,
            supported_entity_types=self.supported_entity_types,
            version="2.0.0"
        )

# Global service instance
ner_service = MedicalNERService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await ner_service.initialize()
    yield
    # Shutdown
    if ner_service.redis_client:
        await ner_service.redis_client.close()

# FastAPI app
app = FastAPI(
    title="Medical NER Service",
    description="Medical named entity recognition with SNOMED CT and ICD-10 mapping",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return await ner_service.health_check()

@app.post("/extract", response_model=NERResponse)
async def extract_medical_entities(request: NERRequest, background_tasks: BackgroundTasks):
    """Extract medical entities from text."""
    
    if not ner_service.model_loaded:
        raise HTTPException(status_code=503, detail="NER model not loaded")
    
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    if len(request.text) > 10000:  # Limit text length
        raise HTTPException(status_code=400, detail="Text too long (max 10,000 characters)")
    
    # Process the NER request
    response = await ner_service.extract_medical_entities(request)
    
    # Log usage for audit (background task)
    background_tasks.add_task(
        log_ner_usage,
        response.request_id,
        response.text_length,
        response.entity_count,
        response.processing_time_ms
    )
    
    return response

async def log_ner_usage(
    request_id: str,
    text_length: int,
    entity_count: int,
    processing_time: float
):
    """Log NER usage for audit and monitoring."""
    logger.info(
        "Medical NER processing completed",
        request_id=request_id,
        text_length=text_length,
        entity_count=entity_count,
        processing_time_ms=processing_time
    )

if __name__ == "__main__":
    uvicorn.run(
        "medical_ner_service:app",
        host="0.0.0.0",
        port=8003,
        reload=False,
        access_log=True
    )