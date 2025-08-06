"""
Clinical Feature Extractor for Healthcare ML Platform

Extracts medically meaningful categories and features from patient data
for ML-ready anonymization while preserving clinical similarity for disease prediction.
"""

import re
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Set, Tuple
from enum import Enum
import structlog

from .schemas import (
    AgeGroup, PregnancyStatus, LocationCategory, SeasonCategory, 
    ClinicalCategory
)

logger = structlog.get_logger(__name__)

class ClinicalFeatureExtractor:
    """
    Extracts clinically meaningful features for ML-ready anonymization.
    
    Focuses on preserving medical similarity while removing all PII.
    Categories are designed for disease prediction algorithms.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize clinical feature extractor.
        
        Args:
            config: Configuration for feature extraction
        """
        self.config = config or {}
        self.logger = logger.bind(component="ClinicalFeatureExtractor")
        
        # Medical terminology mappings
        self._load_medical_mappings()
        
        # Seasonal disease patterns (months)
        self.seasonal_patterns = {
            SeasonCategory.WINTER: [12, 1, 2],     # Respiratory illness peak
            SeasonCategory.SPRING: [3, 4, 5],      # Allergy season
            SeasonCategory.SUMMER: [6, 7, 8],      # Different patterns
            SeasonCategory.FALL: [9, 10, 11]       # Flu season beginning
        }
    
    async def extract_all_features(
        self,
        patient_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract all clinical features for ML anonymization.
        
        Args:
            patient_data: Raw patient data dictionary
            
        Returns:
            Dictionary of extracted clinical features
        """
        try:
            features = {
                # Demographic features (medical risk-based)
                "age_group": self.categorize_age_for_medical_risk(
                    patient_data.get("age")
                ),
                "gender_category": self.categorize_gender(
                    patient_data.get("gender")
                ),
                "pregnancy_status": self.categorize_pregnancy_status(
                    patient_data.get("pregnancy", {}),
                    patient_data.get("gender")
                ),
                
                # Geographic and temporal features
                "location_category": self.categorize_location_for_exposure(
                    patient_data.get("location", ""),
                    patient_data.get("address", {})
                ),
                "season_category": self.categorize_season_for_disease_patterns(
                    patient_data.get("visit_date")
                ),
                
                # Clinical history features
                "medical_history_categories": self.categorize_medical_history(
                    patient_data.get("medical_history", [])
                ),
                "medication_categories": self.categorize_medications(
                    patient_data.get("medications", [])
                ),
                "allergy_categories": self.categorize_allergies(
                    patient_data.get("allergies", [])
                ),
                
                # Risk stratification
                "risk_factors": self.extract_risk_factors(patient_data),
                "comorbidity_indicators": self.extract_comorbidity_indicators(
                    patient_data.get("medical_history", [])
                ),
                
                # Healthcare utilization patterns
                "utilization_pattern": self.categorize_utilization_pattern(
                    patient_data.get("visit_history", [])
                ),
                "care_complexity": self.assess_care_complexity(patient_data)
            }
            
            # Calculate similarity weights for ML algorithms
            features["similarity_metadata"] = self.calculate_similarity_weights(
                features
            )
            
            self.logger.info(
                "Clinical features extracted successfully",
                feature_count=len(features)
            )
            
            return features
            
        except Exception as e:
            self.logger.error(
                "Failed to extract clinical features",
                error=str(e)
            )
            raise
    
    def categorize_age_for_medical_risk(self, age: Optional[Any]) -> AgeGroup:
        """
        Categorize age based on medical risk factors and disease susceptibility.
        
        Args:
            age: Patient age (int, float, or None)
            
        Returns:
            Medical age group category
        """
        if age is None:
            return AgeGroup.YOUNG_ADULT  # Default assumption
        
        try:
            age_int = int(float(age))
            
            if age_int < 18:
                return AgeGroup.PEDIATRIC
            elif age_int < 25:
                return AgeGroup.YOUNG_ADULT
            elif age_int < 35:
                return AgeGroup.REPRODUCTIVE_AGE
            elif age_int < 50:
                return AgeGroup.MIDDLE_AGE
            elif age_int < 65:
                return AgeGroup.OLDER_ADULT
            else:
                return AgeGroup.ELDERLY
                
        except (ValueError, TypeError):
            self.logger.warning("Invalid age value", age=age)
            return AgeGroup.YOUNG_ADULT
    
    def categorize_gender(self, gender: Optional[str]) -> str:
        """
        Standardize gender categorization for medical analysis.
        
        Args:
            gender: Patient gender
            
        Returns:
            Standardized gender category
        """
        if not gender:
            return "unknown"
        
        gender_lower = str(gender).lower().strip()
        
        if gender_lower in ["male", "m", "man"]:
            return "male"
        elif gender_lower in ["female", "f", "woman"]:
            return "female"
        else:
            return "other"
    
    def categorize_pregnancy_status(
        self,
        pregnancy_data: Dict[str, Any],
        gender: Optional[str]
    ) -> PregnancyStatus:
        """
        Determine pregnancy status for medical risk assessment.
        
        Args:
            pregnancy_data: Pregnancy-related data
            gender: Patient gender
            
        Returns:
            Pregnancy status category
        """
        # Only applicable to females
        if self.categorize_gender(gender) != "female":
            return PregnancyStatus.NOT_PREGNANT
        
        if not pregnancy_data:
            return PregnancyStatus.NOT_PREGNANT
        
        # Check current pregnancy status
        if pregnancy_data.get("is_pregnant", False):
            trimester = pregnancy_data.get("trimester", 1)
            if trimester == 1:
                return PregnancyStatus.PREGNANT_TRIMESTER_1
            elif trimester == 2:
                return PregnancyStatus.PREGNANT_TRIMESTER_2
            elif trimester == 3:
                return PregnancyStatus.PREGNANT_TRIMESTER_3
            else:
                return PregnancyStatus.PREGNANT_TRIMESTER_1  # Default
        
        # Check recent delivery
        if pregnancy_data.get("recent_delivery", False):
            return PregnancyStatus.POSTPARTUM
        
        # Check for pregnancy-related data without explicit status
        pregnancy_indicators = [
            "prenatal", "maternity", "obstetric", "fetal", "gestational"
        ]
        
        pregnancy_text = str(pregnancy_data).lower()
        if any(indicator in pregnancy_text for indicator in pregnancy_indicators):
            return PregnancyStatus.PREGNANT_TRIMESTER_1  # Conservative assumption
        
        return PregnancyStatus.NOT_PREGNANT
    
    def categorize_location_for_exposure(
        self,
        location: str,
        address: Dict[str, Any]
    ) -> LocationCategory:
        """
        Categorize location for disease exposure pattern analysis.
        
        Args:
            location: Location string
            address: Structured address data
            
        Returns:
            Location category for exposure analysis
        """
        # Combine location sources
        location_text = " ".join([
            str(location).lower(),
            str(address.get("city", "")).lower(),
            str(address.get("state", "")).lower(),
            str(address.get("region", "")).lower()
        ])
        
        # Determine urban vs rural
        urban_keywords = [
            "city", "urban", "metropolitan", "downtown", "metro", 
            "suburb", "town", "municipality"
        ]
        rural_keywords = [
            "rural", "farm", "countryside", "village", "county", 
            "agricultural", "ranch"
        ]
        
        is_urban = any(keyword in location_text for keyword in urban_keywords)
        is_rural = any(keyword in location_text for keyword in rural_keywords)
        
        # Default to urban if unclear
        density = "urban" if is_urban or not is_rural else "rural"
        
        # Determine geographic region (US-focused, expandable)
        northeast_keywords = [
            "northeast", "new england", "maine", "new hampshire", "vermont",
            "massachusetts", "rhode island", "connecticut", "new york",
            "new jersey", "pennsylvania"
        ]
        southeast_keywords = [
            "southeast", "south", "florida", "georgia", "alabama", "mississippi",
            "tennessee", "kentucky", "north carolina", "south carolina",
            "virginia", "west virginia", "delaware", "maryland"
        ]
        midwest_keywords = [
            "midwest", "ohio", "michigan", "indiana", "wisconsin", "illinois",
            "minnesota", "iowa", "missouri", "north dakota", "south dakota",
            "nebraska", "kansas"
        ]
        west_keywords = [
            "west", "california", "oregon", "washington", "nevada", "utah",
            "colorado", "arizona", "new mexico", "montana", "wyoming",
            "idaho", "alaska", "hawaii"
        ]
        
        region = "unknown"
        if any(keyword in location_text for keyword in northeast_keywords):
            region = "northeast"
        elif any(keyword in location_text for keyword in southeast_keywords):
            region = "southeast"
        elif any(keyword in location_text for keyword in midwest_keywords):
            region = "midwest"
        elif any(keyword in location_text for keyword in west_keywords):
            region = "west"
        
        # Combine density and region
        if region == "unknown":
            return LocationCategory.UNKNOWN
        
        try:
            location_category = LocationCategory(f"{density}_{region}")
            return location_category
        except ValueError:
            return LocationCategory.UNKNOWN
    
    def categorize_season_for_disease_patterns(
        self,
        visit_date: Optional[Any]
    ) -> SeasonCategory:
        """
        Determine season for disease pattern analysis.
        
        Args:
            visit_date: Visit date (various formats)
            
        Returns:
            Season category for disease patterns
        """
        try:
            # Parse date
            if isinstance(visit_date, str):
                # Try common date formats
                for date_format in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]:
                    try:
                        parsed_date = datetime.strptime(visit_date, date_format)
                        month = parsed_date.month
                        break
                    except ValueError:
                        continue
                else:
                    # If no format works, use current date
                    month = datetime.now().month
            elif isinstance(visit_date, (datetime, date)):
                month = visit_date.month
            elif isinstance(visit_date, (int, float)):
                # Assume timestamp
                parsed_date = datetime.fromtimestamp(visit_date)
                month = parsed_date.month
            else:
                # Use current date as fallback
                month = datetime.now().month
            
            # Map month to season
            for season, months in self.seasonal_patterns.items():
                if month in months:
                    return season
            
            return SeasonCategory.WINTER  # Fallback
            
        except Exception as e:
            self.logger.warning("Could not parse visit date", date=visit_date, error=str(e))
            return SeasonCategory.WINTER  # Default to winter (peak illness season)
    
    def categorize_medical_history(
        self,
        medical_history: List[Any]
    ) -> List[ClinicalCategory]:
        """
        Categorize medical history into clinical categories for similarity matching.
        
        Args:
            medical_history: List of medical conditions/history
            
        Returns:
            List of clinical categories
        """
        categories = set()
        
        # Convert all history items to lowercase strings
        history_text = " ".join(str(item).lower() for item in medical_history)
        
        # Respiratory conditions
        respiratory_terms = [
            "asthma", "copd", "pneumonia", "bronchitis", "respiratory",
            "lung", "breathing", "shortness of breath", "cough", "wheeze",
            "pulmonary", "emphysema", "tuberculosis", "influenza", "flu"
        ]
        if any(term in history_text for term in respiratory_terms):
            categories.add(ClinicalCategory.RESPIRATORY_HISTORY)
        
        # Cardiac conditions
        cardiac_terms = [
            "heart", "cardiac", "cardiovascular", "hypertension", "blood pressure",
            "coronary", "arrhythmia", "atrial fibrillation", "heart attack",
            "myocardial infarction", "angina", "chest pain", "palpitations"
        ]
        if any(term in history_text for term in cardiac_terms):
            categories.add(ClinicalCategory.CARDIAC_HISTORY)
        
        # Allergic conditions
        allergic_terms = [
            "allergy", "allergic", "hay fever", "eczema", "dermatitis",
            "rhinitis", "sinusitis", "hives", "urticaria", "anaphylaxis"
        ]
        if any(term in history_text for term in allergic_terms):
            categories.add(ClinicalCategory.ALLERGIC_HISTORY)
        
        # Diabetic conditions
        diabetic_terms = [
            "diabetes", "diabetic", "blood sugar", "glucose", "insulin",
            "hyperglycemia", "hypoglycemia", "ketoacidosis"
        ]
        if any(term in history_text for term in diabetic_terms):
            categories.add(ClinicalCategory.DIABETIC_HISTORY)
        
        # Neurological conditions
        neurological_terms = [
            "neurological", "seizure", "epilepsy", "stroke", "migraine",
            "headache", "parkinson", "alzheimer", "dementia", "multiple sclerosis",
            "neuropathy", "concussion"
        ]
        if any(term in history_text for term in neurological_terms):
            categories.add(ClinicalCategory.NEUROLOGICAL_HISTORY)
        
        # Psychiatric conditions
        psychiatric_terms = [
            "depression", "anxiety", "bipolar", "psychiatric", "mental health",
            "schizophrenia", "ptsd", "adhd", "autism", "ocd", "panic"
        ]
        if any(term in history_text for term in psychiatric_terms):
            categories.add(ClinicalCategory.PSYCHIATRIC_HISTORY)
        
        # Oncological conditions
        oncological_terms = [
            "cancer", "tumor", "oncology", "chemotherapy", "radiation",
            "malignancy", "carcinoma", "lymphoma", "leukemia", "metastasis"
        ]
        if any(term in history_text for term in oncological_terms):
            categories.add(ClinicalCategory.ONCOLOGICAL_HISTORY)
        
        # Infectious disease history
        infectious_terms = [
            "infection", "infectious", "sepsis", "abscess", "cellulitis",
            "meningitis", "hepatitis", "hiv", "aids", "mrsa", "uti"
        ]
        if any(term in history_text for term in infectious_terms):
            categories.add(ClinicalCategory.INFECTIOUS_DISEASE_HISTORY)
        
        # Autoimmune conditions
        autoimmune_terms = [
            "autoimmune", "lupus", "rheumatoid arthritis", "crohn", "colitis",
            "multiple sclerosis", "thyroiditis", "psoriasis", "fibromyalgia"
        ]
        if any(term in history_text for term in autoimmune_terms):
            categories.add(ClinicalCategory.AUTOIMMUNE_HISTORY)
        
        # Surgical history
        surgical_terms = [
            "surgery", "surgical", "operation", "procedure", "appendectomy",
            "cholecystectomy", "bypass", "transplant", "implant", "removal"
        ]
        if any(term in history_text for term in surgical_terms):
            categories.add(ClinicalCategory.SURGICAL_HISTORY)
        
        return list(categories)
    
    def categorize_medications(self, medications: List[Any]) -> List[str]:
        """
        Categorize medications into drug classes for similarity matching.
        
        Args:
            medications: List of medications
            
        Returns:
            List of medication categories
        """
        categories = set()
        
        # Convert all medications to lowercase strings
        med_text = " ".join(str(med).lower() for med in medications)
        
        # Map medication names/types to categories
        medication_mappings = {
            "antibiotics": [
                "antibiotic", "penicillin", "amoxicillin", "azithromycin",
                "ciprofloxacin", "doxycycline", "cephalexin"
            ],
            "antihistamines": [
                "antihistamine", "benadryl", "diphenhydramine", "loratadine",
                "cetirizine", "fexofenadine", "chlorpheniramine"
            ],
            "beta_agonists": [
                "albuterol", "salbutamol", "salmeterol", "formoterol",
                "bronchodilator", "inhaler"
            ],
            "ace_inhibitors": [
                "ace inhibitor", "lisinopril", "enalapril", "captopril",
                "ramipril", "benazepril"
            ],
            "beta_blockers": [
                "beta blocker", "metoprolol", "atenolol", "propranolol",
                "carvedilol", "bisoprolol"
            ],
            "statins": [
                "statin", "atorvastatin", "simvastatin", "rosuvastatin",
                "pravastatin", "lovastatin"
            ],
            "nsaids": [
                "nsaid", "ibuprofen", "naproxen", "diclofenac", "indomethacin",
                "aspirin", "celecoxib"
            ],
            "corticosteroids": [
                "steroid", "prednisone", "prednisolone", "hydrocortisone",
                "dexamethasone", "methylprednisolone"
            ],
            "antidiabetics": [
                "metformin", "insulin", "glipizide", "glyburide", "pioglitazone",
                "sitagliptin", "empagliflozin"
            ],
            "antidepressants": [
                "antidepressant", "ssri", "sertraline", "fluoxetine", "citalopram",
                "escitalopram", "venlafaxine", "bupropion"
            ]
        }
        
        for category, terms in medication_mappings.items():
            if any(term in med_text for term in terms):
                categories.add(category)
        
        return list(categories)
    
    def categorize_allergies(self, allergies: List[Any]) -> List[str]:
        """
        Categorize allergies for clinical similarity matching.
        
        Args:
            allergies: List of allergies
            
        Returns:
            List of allergy categories
        """
        categories = set()
        
        # Convert all allergies to lowercase strings
        allergy_text = " ".join(str(allergy).lower() for allergy in allergies)
        
        # Allergy category mappings
        allergy_mappings = {
            "drug_allergies": [
                "penicillin", "sulfa", "aspirin", "ibuprofen", "latex",
                "antibiotic", "nsaid"
            ],
            "food_allergies": [
                "peanut", "tree nut", "shellfish", "dairy", "egg", "wheat",
                "soy", "fish", "food"
            ],
            "environmental_allergies": [
                "pollen", "dust", "mold", "pet", "cat", "dog", "grass",
                "tree", "ragweed", "environmental"
            ],
            "seasonal_allergies": [
                "seasonal", "hay fever", "spring", "fall", "pollen"
            ],
            "contact_allergies": [
                "contact", "metal", "nickel", "fragrance", "cosmetic",
                "preservative"
            ]
        }
        
        for category, terms in allergy_mappings.items():
            if any(term in allergy_text for term in terms):
                categories.add(category)
        
        return list(categories)
    
    def extract_risk_factors(self, patient_data: Dict[str, Any]) -> List[str]:
        """
        Extract risk factors for disease prediction.
        
        Args:
            patient_data: Complete patient data
            
        Returns:
            List of risk factor categories
        """
        risk_factors = set()
        
        # Age-based risk factors
        age_group = self.categorize_age_for_medical_risk(patient_data.get("age"))
        if age_group == AgeGroup.ELDERLY:
            risk_factors.add("advanced_age_risk")
        elif age_group == AgeGroup.PEDIATRIC:
            risk_factors.add("pediatric_vulnerability")
        
        # Pregnancy-related risks
        pregnancy_status = self.categorize_pregnancy_status(
            patient_data.get("pregnancy", {}),
            patient_data.get("gender")
        )
        if pregnancy_status in [
            PregnancyStatus.PREGNANT_TRIMESTER_1,
            PregnancyStatus.PREGNANT_TRIMESTER_2,
            PregnancyStatus.PREGNANT_TRIMESTER_3
        ]:
            risk_factors.add("pregnancy_immunosuppression")
        
        # Seasonal exposure risks
        season = self.categorize_season_for_disease_patterns(
            patient_data.get("visit_date")
        )
        if season == SeasonCategory.WINTER:
            risk_factors.add("winter_respiratory_exposure")
        elif season == SeasonCategory.SPRING:
            risk_factors.add("spring_allergy_exposure")
        
        # Location-based exposure risks
        location = self.categorize_location_for_exposure(
            patient_data.get("location", ""),
            patient_data.get("address", {})
        )
        if "urban" in location.value:
            risk_factors.add("urban_disease_exposure")
        elif "rural" in location.value:
            risk_factors.add("rural_environmental_exposure")
        
        # Medical history-based risks
        medical_categories = self.categorize_medical_history(
            patient_data.get("medical_history", [])
        )
        
        if ClinicalCategory.RESPIRATORY_HISTORY in medical_categories:
            risk_factors.add("respiratory_history_risk")
        if ClinicalCategory.CARDIAC_HISTORY in medical_categories:
            risk_factors.add("cardiovascular_risk")
        if ClinicalCategory.DIABETIC_HISTORY in medical_categories:
            risk_factors.add("diabetic_complications_risk")
        if ClinicalCategory.ALLERGIC_HISTORY in medical_categories:
            risk_factors.add("allergic_reaction_risk")
        
        # Medication-based risks
        medications = self.categorize_medications(
            patient_data.get("medications", [])
        )
        if "corticosteroids" in medications:
            risk_factors.add("immunosuppression_risk")
        if "anticoagulants" in medications:
            risk_factors.add("bleeding_risk")
        
        return list(risk_factors)
    
    def extract_comorbidity_indicators(
        self,
        medical_history: List[Any]
    ) -> Dict[str, int]:
        """
        Extract comorbidity indicators for severity assessment.
        
        Args:
            medical_history: Medical history list
            
        Returns:
            Dictionary of comorbidity indicators with counts
        """
        categories = self.categorize_medical_history(medical_history)
        
        # Map categories to comorbidity scores
        comorbidity_weights = {
            ClinicalCategory.CARDIAC_HISTORY: 3,
            ClinicalCategory.DIABETIC_HISTORY: 2,
            ClinicalCategory.RESPIRATORY_HISTORY: 2,
            ClinicalCategory.ONCOLOGICAL_HISTORY: 4,
            ClinicalCategory.NEUROLOGICAL_HISTORY: 2,
            ClinicalCategory.AUTOIMMUNE_HISTORY: 2,
            ClinicalCategory.PSYCHIATRIC_HISTORY: 1,
            ClinicalCategory.ALLERGIC_HISTORY: 1,
            ClinicalCategory.INFECTIOUS_DISEASE_HISTORY: 1,
            ClinicalCategory.SURGICAL_HISTORY: 1
        }
        
        total_score = sum(
            comorbidity_weights.get(category, 1) for category in categories
        )
        
        return {
            "total_comorbidity_count": len(categories),
            "weighted_comorbidity_score": total_score,
            "high_risk_conditions": len([
                cat for cat in categories 
                if comorbidity_weights.get(cat, 0) >= 3
            ])
        }
    
    def categorize_utilization_pattern(
        self,
        visit_history: List[Any]
    ) -> str:
        """
        Categorize healthcare utilization pattern.
        
        Args:
            visit_history: List of healthcare visits
            
        Returns:
            Utilization pattern category
        """
        visit_count = len(visit_history) if visit_history else 0
        
        if visit_count == 0:
            return "no_recent_utilization"
        elif visit_count <= 2:
            return "low_utilization"
        elif visit_count <= 5:
            return "moderate_utilization"
        elif visit_count <= 10:
            return "high_utilization"
        else:
            return "very_high_utilization"
    
    def assess_care_complexity(self, patient_data: Dict[str, Any]) -> str:
        """
        Assess care complexity for resource planning.
        
        Args:
            patient_data: Complete patient data
            
        Returns:
            Care complexity category
        """
        complexity_score = 0
        
        # Add points for various complexity factors
        medical_categories = self.categorize_medical_history(
            patient_data.get("medical_history", [])
        )
        complexity_score += len(medical_categories)
        
        medications = self.categorize_medications(
            patient_data.get("medications", [])
        )
        complexity_score += len(medications) * 0.5
        
        allergies = self.categorize_allergies(
            patient_data.get("allergies", [])
        )
        complexity_score += len(allergies) * 0.3
        
        # Age factor
        age_group = self.categorize_age_for_medical_risk(patient_data.get("age"))
        if age_group in [AgeGroup.PEDIATRIC, AgeGroup.ELDERLY]:
            complexity_score += 2
        
        # Pregnancy factor
        pregnancy_status = self.categorize_pregnancy_status(
            patient_data.get("pregnancy", {}),
            patient_data.get("gender")
        )
        if pregnancy_status != PregnancyStatus.NOT_PREGNANT:
            complexity_score += 1
        
        # Categorize complexity
        if complexity_score <= 2:
            return "low_complexity"
        elif complexity_score <= 5:
            return "moderate_complexity"
        elif complexity_score <= 8:
            return "high_complexity"
        else:
            return "very_high_complexity"
    
    def calculate_similarity_weights(
        self,
        features: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate similarity weights for ML prediction algorithms.
        
        Args:
            features: Extracted clinical features
            
        Returns:
            Dictionary of similarity weights for different feature types
        """
        weights = {
            "medical_similarity_weight": 0.8,      # High weight for medical history
            "demographic_similarity_weight": 0.3,  # Lower weight for age/gender
            "temporal_similarity_weight": 0.5,     # Medium weight for seasonal factors
            "geographic_similarity_weight": 0.4,   # Medium weight for location
            "medication_similarity_weight": 0.6,   # Medium-high weight for medications
            "risk_factor_similarity_weight": 0.7   # High weight for risk factors
        }
        
        # Adjust weights based on feature complexity
        medical_categories = features.get("medical_history_categories", [])
        if len(medical_categories) > 3:
            weights["medical_similarity_weight"] = 0.9  # Even higher for complex cases
        
        pregnancy_status = features.get("pregnancy_status")
        if pregnancy_status != PregnancyStatus.NOT_PREGNANT:
            weights["demographic_similarity_weight"] = 0.6  # Higher for pregnancy
        
        age_group = features.get("age_group")
        if age_group in [AgeGroup.PEDIATRIC, AgeGroup.ELDERLY]:
            weights["demographic_similarity_weight"] = 0.5  # Higher for vulnerable populations
        
        return weights
    
    def _load_medical_mappings(self):
        """Load medical terminology mappings for feature extraction."""
        # This would load from a medical terminology database in production
        # For now, we use hardcoded mappings defined in the methods above
        pass