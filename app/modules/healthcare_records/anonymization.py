"""
Healthcare Data Anonymization Engine

Implements k-anonymity, differential privacy, and other anonymization techniques
for patient data used in research and analytics while preserving utility.
"""

import asyncio
import hashlib
import random
import uuid
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Set, Tuple
import numpy as np
import structlog

logger = structlog.get_logger(__name__)


class AnonymizationEngine:
    """
    Advanced anonymization engine for healthcare data.
    Supports k-anonymity, differential privacy, and custom anonymization rules.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the anonymization engine with configuration.
        
        Args:
            config: Anonymization configuration including techniques and parameters
        """
        self.config = config
        self.logger = logger.bind(component="AnonymizationEngine")
        
        # Default anonymization techniques
        self.techniques = {
            'generalization': self._generalize_value,
            'suppression': self._suppress_value,
            'perturbation': self._perturb_value,
            'substitution': self._substitute_value,
            'masking': self._mask_value
        }
        
        # Quasi-identifier handling
        self.qi_generalizations = {
            'age': self._generalize_age,
            'zipcode': self._generalize_zipcode,
            'date_of_birth': self._generalize_date_of_birth,
            'location': self._generalize_location
        }
    
    async def anonymize_record(
        self,
        record: Dict[str, Any],
        preserve_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Anonymize a single patient record.
        
        Args:
            record: Patient record to anonymize
            preserve_fields: Fields to preserve without anonymization
            
        Returns:
            Anonymized record
        """
        preserve_fields = preserve_fields or []
        anonymized = {}
        
        for field, value in record.items():
            if field in preserve_fields:
                # Preserve field as-is
                anonymized[field] = value
            elif field in self._get_direct_identifiers():
                # Remove direct identifiers
                continue
            elif field in self._get_quasi_identifiers():
                # Apply quasi-identifier generalization
                anonymized[field] = await self._anonymize_quasi_identifier(field, value)
            else:
                # Apply general anonymization
                anonymized[field] = await self._anonymize_field(field, value)
        
        # Add anonymization metadata
        anonymized['_anonymized_at'] = datetime.utcnow().isoformat()
        anonymized['_anonymization_id'] = str(uuid.uuid4())
        
        return anonymized
    
    async def apply_k_anonymity(
        self,
        records: List[Dict[str, Any]],
        k: int,
        quasi_identifiers: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Apply k-anonymity to a dataset.
        
        Args:
            records: List of records to anonymize
            k: Minimum group size for k-anonymity
            quasi_identifiers: List of quasi-identifier fields
            
        Returns:
            k-anonymous dataset
        """
        if k < 2:
            raise ValueError("k must be at least 2 for k-anonymity")
        
        self.logger.info(
            "Applying k-anonymity",
            k=k,
            record_count=len(records),
            quasi_identifiers=quasi_identifiers
        )
        
        # Group records by quasi-identifier combinations
        groups = self._group_by_quasi_identifiers(records, quasi_identifiers)
        
        # Identify groups smaller than k
        small_groups = [group for group in groups.values() if len(group) < k]
        
        # Generalize small groups until they meet k-anonymity
        while small_groups:
            # Find the most generalizable attribute
            attr_to_generalize = self._select_attribute_for_generalization(
                small_groups,
                quasi_identifiers
            )
            
            # Generalize the selected attribute
            for group in small_groups:
                for record in group:
                    record[attr_to_generalize] = await self._generalize_quasi_identifier(
                        attr_to_generalize,
                        record[attr_to_generalize]
                    )
            
            # Re-group and check
            groups = self._group_by_quasi_identifiers(records, quasi_identifiers)
            small_groups = [group for group in groups.values() if len(group) < k]
        
        self.logger.info(
            "K-anonymity applied successfully",
            final_groups=len(groups),
            min_group_size=min(len(group) for group in groups.values())
        )
        
        return records
    
    async def apply_differential_privacy(
        self,
        records: List[Dict[str, Any]],
        epsilon: float,
        numeric_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Apply differential privacy noise to numeric fields.
        
        Args:
            records: List of records
            epsilon: Privacy budget (smaller = more private)
            numeric_fields: Fields to apply noise to
            
        Returns:
            Records with differential privacy applied
        """
        if epsilon <= 0:
            raise ValueError("Epsilon must be positive")
        
        numeric_fields = numeric_fields or self._identify_numeric_fields(records)
        
        self.logger.info(
            "Applying differential privacy",
            epsilon=epsilon,
            record_count=len(records),
            numeric_fields=numeric_fields
        )
        
        # Calculate noise scale (Laplace mechanism)
        sensitivity = 1.0  # Assuming unit sensitivity
        noise_scale = sensitivity / epsilon
        
        for record in records:
            for field in numeric_fields:
                if field in record and isinstance(record[field], (int, float)):
                    # Add Laplace noise
                    noise = np.random.laplace(0, noise_scale)
                    record[field] = record[field] + noise
                    
                    # Ensure non-negative for certain fields
                    if field in ['age', 'weight', 'height']:
                        record[field] = max(0, record[field])
        
        return records
    
    async def calculate_utility_metrics(
        self,
        anonymized_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate data utility metrics for anonymized dataset.
        
        Args:
            anonymized_records: Anonymized records
            
        Returns:
            Utility metrics
        """
        metrics = {
            'record_count': len(anonymized_records),
            'field_completeness': {},
            'value_diversity': {},
            'information_loss': 0.0,
            'data_quality_score': 0.0
        }
        
        if not anonymized_records:
            return metrics
        
        # Calculate field completeness
        for field in anonymized_records[0].keys():
            non_null_count = sum(
                1 for record in anonymized_records 
                if record.get(field) is not None
            )
            metrics['field_completeness'][field] = non_null_count / len(anonymized_records)
        
        # Calculate value diversity (unique values per field)
        for field in anonymized_records[0].keys():
            unique_values = set(
                record.get(field) for record in anonymized_records
                if record.get(field) is not None
            )
            metrics['value_diversity'][field] = len(unique_values)
        
        # Calculate overall data quality score
        completeness_avg = np.mean(list(metrics['field_completeness'].values()))
        diversity_avg = np.mean(list(metrics['value_diversity'].values()))
        metrics['data_quality_score'] = (completeness_avg + min(diversity_avg / 10, 1.0)) / 2
        
        return metrics
    
    # Private methods
    
    def _get_direct_identifiers(self) -> Set[str]:
        """Get list of direct identifier fields to remove."""
        return {
            'ssn', 'social_security_number', 'drivers_license',
            'passport_number', 'medical_record_number', 'mrn',
            'full_name', 'first_name', 'last_name', 'email',
            'phone_number', 'address', 'account_number'
        }
    
    def _get_quasi_identifiers(self) -> Set[str]:
        """Get list of quasi-identifier fields that need generalization."""
        return {
            'age', 'date_of_birth', 'zipcode', 'postal_code',
            'city', 'state', 'gender', 'race', 'ethnicity',
            'occupation', 'education_level', 'income_range'
        }
    
    async def _anonymize_quasi_identifier(self, field: str, value: Any) -> Any:
        """Anonymize a quasi-identifier field."""
        if field in self.qi_generalizations:
            return await self.qi_generalizations[field](value)
        return await self._generalize_value(value)
    
    async def _anonymize_field(self, field: str, value: Any) -> Any:
        """Apply general anonymization to a field."""
        technique = self.config.get('default_technique', 'generalization')
        if technique in self.techniques:
            return await self.techniques[technique](value)
        return value
    
    async def _generalize_age(self, age: Any) -> str:
        """Generalize age into ranges."""
        if not isinstance(age, (int, float)):
            return "unknown"
        
        age = int(age)
        if age < 18:
            return "0-17"
        elif age < 30:
            return "18-29"
        elif age < 40:
            return "30-39"
        elif age < 50:
            return "40-49"
        elif age < 60:
            return "50-59"
        elif age < 70:
            return "60-69"
        else:
            return "70+"
    
    async def _generalize_zipcode(self, zipcode: Any) -> str:
        """Generalize zipcode to 3-digit prefix."""
        if not isinstance(zipcode, str) or len(zipcode) < 3:
            return "000"
        return zipcode[:3] + "**"
    
    async def _generalize_date_of_birth(self, dob: Any) -> str:
        """Generalize date of birth to year only."""
        if isinstance(dob, date):
            return str(dob.year)
        elif isinstance(dob, str):
            try:
                parsed_date = datetime.fromisoformat(dob.replace('Z', '+00:00'))
                return str(parsed_date.year)
            except:
                return "unknown"
        return "unknown"
    
    async def _generalize_location(self, location: Any) -> str:
        """Generalize location to region."""
        # Simple region mapping - could be enhanced with actual geographic data
        location_str = str(location).lower()
        if any(term in location_str for term in ['north', 'northern']):
            return "northern_region"
        elif any(term in location_str for term in ['south', 'southern']):
            return "southern_region"
        elif any(term in location_str for term in ['east', 'eastern']):
            return "eastern_region"
        elif any(term in location_str for term in ['west', 'western']):
            return "western_region"
        else:
            return "central_region"
    
    async def _generalize_value(self, value: Any) -> Any:
        """Apply general generalization to a value."""
        if isinstance(value, str):
            # Hash-based generalization for strings
            hash_obj = hashlib.sha256(value.encode())
            return f"gen_{hash_obj.hexdigest()[:8]}"
        elif isinstance(value, (int, float)):
            # Range-based generalization for numbers
            return self._generalize_numeric_value(value)
        else:
            return "generalized"
    
    def _generalize_numeric_value(self, value: float, bin_size: float = 10.0) -> str:
        """Generalize numeric value into ranges."""
        lower = int(value // bin_size) * bin_size
        upper = lower + bin_size
        return f"{lower}-{upper}"
    
    async def _suppress_value(self, value: Any) -> Any:
        """Suppress (remove) a value."""
        return None
    
    async def _perturb_value(self, value: Any) -> Any:
        """Add noise to a value."""
        if isinstance(value, (int, float)):
            noise = random.gauss(0, abs(value) * 0.1)  # 10% noise
            return value + noise
        return value
    
    async def _substitute_value(self, value: Any) -> Any:
        """Substitute value with a similar but different value."""
        if isinstance(value, str):
            return f"sub_{hashlib.md5(value.encode()).hexdigest()[:6]}"
        elif isinstance(value, (int, float)):
            return value + random.randint(-5, 5)
        return value
    
    async def _mask_value(self, value: Any) -> Any:
        """Mask part of a value."""
        if isinstance(value, str) and len(value) > 3:
            return value[:2] + "*" * (len(value) - 2)
        return value
    
    def _group_by_quasi_identifiers(
        self,
        records: List[Dict[str, Any]],
        quasi_identifiers: List[str]
    ) -> Dict[tuple, List[Dict[str, Any]]]:
        """Group records by quasi-identifier combinations."""
        groups = {}
        
        for record in records:
            qi_tuple = tuple(
                record.get(qi, None) for qi in quasi_identifiers
            )
            if qi_tuple not in groups:
                groups[qi_tuple] = []
            groups[qi_tuple].append(record)
        
        return groups
    
    def _select_attribute_for_generalization(
        self,
        small_groups: List[List[Dict[str, Any]]],
        quasi_identifiers: List[str]
    ) -> str:
        """Select the best attribute for generalization."""
        # Simple heuristic: select the attribute with the most unique values
        value_counts = {}
        
        for qi in quasi_identifiers:
            unique_values = set()
            for group in small_groups:
                for record in group:
                    unique_values.add(record.get(qi))
            value_counts[qi] = len(unique_values)
        
        # Return attribute with most unique values
        return max(value_counts, key=value_counts.get)
    
    async def _generalize_quasi_identifier(self, field: str, value: Any) -> Any:
        """Apply one level of generalization to a quasi-identifier."""
        if field in self.qi_generalizations:
            return await self.qi_generalizations[field](value)
        return await self._generalize_value(value)
    
    def _identify_numeric_fields(self, records: List[Dict[str, Any]]) -> List[str]:
        """Identify numeric fields in the dataset."""
        if not records:
            return []
        
        numeric_fields = []
        sample_record = records[0]
        
        for field, value in sample_record.items():
            if isinstance(value, (int, float)):
                numeric_fields.append(field)
        
        return numeric_fields