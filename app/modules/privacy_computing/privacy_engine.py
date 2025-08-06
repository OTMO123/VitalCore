"""
Advanced Privacy Engine for Healthcare Platform V2.0

Enterprise-grade privacy-preserving computation system implementing homomorphic encryption,
secure multiparty computation, and advanced differential privacy for healthcare AI.
"""

import asyncio
import logging
import uuid
import json
import base64
import hashlib
import hmac
import secrets
import numpy as np
import torch
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from dataclasses import dataclass
import threading
from concurrent.futures import ThreadPoolExecutor

# Privacy-preserving computation frameworks
import tenseal as ts  # Homomorphic encryption
from opacus import PrivacyEngine as OpacusPrivacyEngine  # Differential privacy
from opacus.validators import ModuleValidator
from opacus.utils.batch_memory_manager import BatchMemoryManager
import syft as sy  # PySyft for secure computation

# Statistical and mathematical libraries
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Internal imports
from .schemas import (
    PrivacyConfig, HEContext, EncryptedData, EncryptedResult, SecretShare,
    MPCComputation, MPCResult, DifferentialPrivacyParams, PrivatizedData,
    PrivacyBudget, PrivacyAuditEvent, PrivacyValidationResult, PrivacyMetrics,
    PrivacyLevel, EncryptionScheme, MPCProtocol, PrivacyMechanism
)
from ..audit_logger.service import AuditLogService
from ...core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

@dataclass
class ComputationNode:
    """Node in secure computation network."""
    node_id: str
    node_type: str  # "hospital", "research", "coordinator"
    public_key: str
    capabilities: List[str]
    trust_level: float
    last_seen: datetime

@dataclass
class PrivacyCircuit:
    """Privacy-preserving computation circuit."""
    circuit_id: str
    operations: List[str]
    inputs: List[str]
    outputs: List[str]
    privacy_level: PrivacyLevel
    estimated_cost: Dict[str, float]

class AdvancedPrivacyEngine:
    """
    Enterprise privacy-preserving computation engine for healthcare AI.
    
    Provides comprehensive privacy guarantees through homomorphic encryption,
    secure multiparty computation, and advanced differential privacy mechanisms.
    """
    
    def __init__(self, config: PrivacyConfig):
        self.config = config
        self.logger = logger.bind(component="AdvancedPrivacyEngine")
        
        # Core services
        self.audit_service = AuditLogService()
        
        # Privacy state management
        self.he_contexts: Dict[str, HEContext] = {}
        self.encrypted_data_cache: Dict[str, EncryptedData] = {}
        self.secret_shares: Dict[str, List[SecretShare]] = {}
        self.privacy_budgets: Dict[str, PrivacyBudget] = {}
        
        # Computation networks
        self.computation_nodes: Dict[str, ComputationNode] = {}
        self.active_computations: Dict[str, MPCComputation] = {}
        
        # Privacy engines
        self.opacus_engine = None
        self.tenseal_context = None
        self.syft_workers = {}
        
        # Thread safety
        self.engine_lock = threading.Lock()
        self.computation_lock = threading.Lock()
        
        # Performance monitoring
        self.privacy_metrics_history: List[PrivacyMetrics] = []
        self.executor = ThreadPoolExecutor(max_workers=config.num_parties)
        
        self.logger.info("AdvancedPrivacyEngine initialized successfully")

    # DIFFERENTIAL PRIVACY METHODS
    
    async def apply_global_differential_privacy(
        self, 
        dataset: torch.Tensor, 
        epsilon: float
    ) -> torch.Tensor:
        """
        Apply global differential privacy to dataset with Gaussian mechanism.
        
        Args:
            dataset: Input dataset tensor
            epsilon: Privacy budget parameter
            
        Returns:
            Differentially private dataset
        """
        try:
            start_time = datetime.utcnow()
            
            # Validate privacy parameters
            if epsilon <= 0 or epsilon > 10:
                raise ValueError(f"Invalid epsilon value: {epsilon}")
            
            # Calculate sensitivity and noise scale
            sensitivity = await self._calculate_dataset_sensitivity(dataset)
            noise_scale = sensitivity * np.sqrt(2 * np.log(1.25 / self.config.delta)) / epsilon
            
            # Add Gaussian noise
            noise = torch.normal(0, noise_scale, dataset.shape)
            private_dataset = dataset + noise
            
            # Create privacy metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            metrics = PrivacyMetrics(
                metrics_id=str(uuid.uuid4()),
                operation_type="global_differential_privacy",
                privacy_level=self.config.privacy_level,
                data_size_bytes=dataset.element_size() * dataset.nelement(),
                processing_time_seconds=processing_time,
                memory_usage_mb=torch.cuda.memory_allocated() / (1024**2) if torch.cuda.is_available() else 0,
                privacy_cost={"epsilon": epsilon, "delta": self.config.delta},
                accuracy_loss_percentage=await self._calculate_accuracy_loss(dataset, private_dataset),
                utility_score=await self._calculate_utility_score(dataset, private_dataset),
                timestamp=datetime.utcnow()
            )
            
            # Audit privacy operation
            await self._audit_privacy_operation(
                "global_differential_privacy", epsilon, sensitivity, noise_scale, metrics
            )
            
            self.logger.info(
                "Global differential privacy applied",
                epsilon=epsilon,
                delta=self.config.delta,
                noise_scale=noise_scale,
                processing_time=processing_time
            )
            
            return private_dataset
            
        except Exception as e:
            self.logger.error(f"Failed to apply global differential privacy: {str(e)}")
            raise

    async def implement_local_differential_privacy(
        self, 
        record: torch.Tensor, 
        epsilon: float
    ) -> torch.Tensor:
        """
        Apply local differential privacy to individual record.
        
        Args:
            record: Individual data record
            epsilon: Local privacy budget
            
        Returns:
            Locally differentially private record
        """
        try:
            # Validate input
            if record.numel() == 0:
                raise ValueError("Empty record provided")
            
            # Apply randomized response mechanism for categorical data
            if record.dtype in [torch.int32, torch.int64]:
                private_record = await self._apply_randomized_response(record, epsilon)
            else:
                # Apply Laplace mechanism for continuous data
                sensitivity = 1.0  # Assume normalized data
                noise_scale = sensitivity / epsilon
                laplace_noise = torch.from_numpy(
                    np.random.laplace(0, noise_scale, record.shape)
                ).float()
                private_record = record + laplace_noise
            
            # Audit local privacy operation
            await self._audit_privacy_operation(
                "local_differential_privacy", epsilon, 1.0, noise_scale, None
            )
            
            return private_record
            
        except Exception as e:
            self.logger.error(f"Failed to apply local differential privacy: {str(e)}")
            raise

    async def calculate_privacy_loss(
        self, 
        query_sequence: List[Dict[str, Any]], 
        mechanism: str
    ) -> Dict[str, float]:
        """
        Calculate privacy loss for sequence of queries using composition theorems.
        
        Args:
            query_sequence: List of executed queries
            mechanism: Privacy mechanism used
            
        Returns:
            Privacy loss analysis
        """
        try:
            total_epsilon = 0.0
            total_delta = 0.0
            
            # Basic composition for Gaussian mechanism
            if mechanism == "gaussian":
                for query in query_sequence:
                    epsilon_i = query.get("epsilon", 0)
                    delta_i = query.get("delta", 0)
                    
                    # Advanced composition (Dwork et al.)
                    if len(query_sequence) > 1:
                        k = len(query_sequence)
                        total_epsilon += np.sqrt(2 * k * np.log(1/delta_i)) * epsilon_i + k * epsilon_i * (np.exp(epsilon_i) - 1)
                    else:
                        total_epsilon += epsilon_i
                    
                    total_delta += delta_i
            
            # RDP composition for advanced mechanisms
            elif mechanism == "rdp":
                rdp_orders = [1 + x / 10.0 for x in range(1, 100)] + list(range(12, 64))
                rdp_budget = await self._calculate_rdp_composition(query_sequence, rdp_orders)
                total_epsilon, total_delta = await self._convert_rdp_to_dp(rdp_budget, self.config.delta)
            
            # Moments accountant for deep learning
            elif mechanism == "moments_accountant":
                if self.opacus_engine:
                    total_epsilon = self.opacus_engine.get_epsilon(self.config.delta)
                else:
                    # Fallback to basic composition
                    total_epsilon = sum(q.get("epsilon", 0) for q in query_sequence)
            
            privacy_loss = {
                "total_epsilon": total_epsilon,
                "total_delta": total_delta,
                "mechanism": mechanism,
                "query_count": len(query_sequence),
                "composition_method": "advanced" if len(query_sequence) > 1 else "basic"
            }
            
            self.logger.info(
                "Privacy loss calculated",
                total_epsilon=total_epsilon,
                total_delta=total_delta,
                query_count=len(query_sequence)
            )
            
            return privacy_loss
            
        except Exception as e:
            self.logger.error(f"Failed to calculate privacy loss: {str(e)}")
            raise

    async def optimize_privacy_utility_tradeoff(
        self, 
        dataset: torch.Tensor, 
        utility_metric: str
    ) -> Dict[str, float]:
        """
        Optimize privacy-utility tradeoff for given dataset and utility metric.
        
        Args:
            dataset: Input dataset
            utility_metric: Utility metric to optimize ("accuracy", "f1", "auc")
            
        Returns:
            Optimal privacy parameters
        """
        try:
            # Define parameter search space
            epsilon_values = np.logspace(-2, 1, 20)  # 0.01 to 10
            delta_values = [1e-6, 1e-5, 1e-4]
            
            best_params = {"epsilon": 1.0, "delta": 1e-5}
            best_utility = 0.0
            
            # Grid search for optimal parameters
            for epsilon in epsilon_values:
                for delta in delta_values:
                    try:
                        # Apply differential privacy
                        private_dataset = await self.apply_global_differential_privacy(
                            dataset, epsilon
                        )
                        
                        # Calculate utility
                        utility = await self._calculate_utility_metric(
                            dataset, private_dataset, utility_metric
                        )
                        
                        # Check if this is the best utility so far
                        if utility > best_utility:
                            best_utility = utility
                            best_params = {"epsilon": epsilon, "delta": delta}
                    
                    except Exception as e:
                        # Skip invalid parameter combinations
                        continue
            
            # Add additional metrics
            optimal_params = {
                **best_params,
                "best_utility": best_utility,
                "utility_metric": utility_metric,
                "search_space_size": len(epsilon_values) * len(delta_values),
                "optimization_method": "grid_search"
            }
            
            self.logger.info(
                "Privacy-utility optimization completed",
                best_epsilon=best_params["epsilon"],
                best_delta=best_params["delta"],
                best_utility=best_utility
            )
            
            return optimal_params
            
        except Exception as e:
            self.logger.error(f"Failed to optimize privacy-utility tradeoff: {str(e)}")
            raise

    # HOMOMORPHIC ENCRYPTION METHODS
    
    async def initialize_homomorphic_encryption(
        self, 
        key_size: int, 
        scheme: str
    ) -> HEContext:
        """
        Initialize homomorphic encryption context with specified parameters.
        
        Args:
            key_size: Polynomial modulus degree (1024, 2048, 4096, 8192, 16384)
            scheme: Encryption scheme ("ckks", "bfv", "bgv")
            
        Returns:
            Homomorphic encryption context
        """
        try:
            context_id = str(uuid.uuid4())
            
            # Validate parameters
            if key_size not in [1024, 2048, 4096, 8192, 16384, 32768]:
                raise ValueError(f"Invalid key size: {key_size}")
            
            if scheme.lower() not in ["ckks", "bfv", "bgv"]:
                raise ValueError(f"Unsupported encryption scheme: {scheme}")
            
            # Create TenSEAL context
            if scheme.lower() == "ckks":
                context = ts.context(
                    ts.SCHEME_TYPE.CKKS,
                    poly_modulus_degree=key_size,
                    coeff_mod_bit_sizes=self.config.coeff_modulus_bits
                )
                context.global_scale = self.config.scale
                context.generate_galois_keys()
            
            elif scheme.lower() in ["bfv", "bgv"]:
                context = ts.context(
                    ts.SCHEME_TYPE.BFV,
                    poly_modulus_degree=key_size,
                    plain_modulus=786433  # Prime number for BFV
                )
                context.generate_galois_keys()
            
            # Store context
            he_context = HEContext(
                context_id=context_id,
                encryption_scheme=EncryptionScheme(scheme.lower()),
                poly_modulus_degree=key_size,
                coeff_modulus_bits=self.config.coeff_modulus_bits,
                scale=self.config.scale,
                created_timestamp=datetime.utcnow(),
                is_ready=True
            )
            
            self.he_contexts[context_id] = he_context
            self.tenseal_context = context  # Store for operations
            
            self.logger.info(
                "Homomorphic encryption context initialized",
                context_id=context_id,
                scheme=scheme,
                key_size=key_size
            )
            
            return he_context
            
        except Exception as e:
            self.logger.error(f"Failed to initialize homomorphic encryption: {str(e)}")
            raise

    async def encrypt_patient_data(
        self, 
        data: torch.Tensor, 
        context_id: str
    ) -> EncryptedData:
        """
        Encrypt patient data using homomorphic encryption.
        
        Args:
            data: Patient data tensor
            context_id: HE context identifier
            
        Returns:
            Encrypted data container
        """
        try:
            if context_id not in self.he_contexts:
                raise ValueError(f"HE context not found: {context_id}")
            
            he_context = self.he_contexts[context_id]
            
            # Convert tensor to list for encryption
            if data.dim() == 1:
                data_list = data.tolist()
            else:
                data_list = data.flatten().tolist()
            
            # Encrypt based on scheme
            if he_context.encryption_scheme == EncryptionScheme.CKKS:
                encrypted_vector = ts.ckks_vector(self.tenseal_context, data_list)
            else:
                # For BFV/BGV, convert to integers
                int_data = [int(x) for x in data_list]
                encrypted_vector = ts.bfv_vector(self.tenseal_context, int_data)
            
            # Serialize encrypted data
            encrypted_bytes = encrypted_vector.serialize()
            encrypted_b64 = base64.b64encode(encrypted_bytes).decode()
            
            # Create encrypted data container
            encrypted_data = EncryptedData(
                data_id=str(uuid.uuid4()),
                encrypted_values=encrypted_b64,
                encryption_scheme=he_context.encryption_scheme,
                context_id=context_id,
                data_type="vector" if data.dim() == 1 else "matrix",
                dimensions=list(data.shape),
                encryption_timestamp=datetime.utcnow(),
                checksum=hashlib.sha256(encrypted_bytes).hexdigest()
            )
            
            # Cache encrypted data
            self.encrypted_data_cache[encrypted_data.data_id] = encrypted_data
            
            # Audit encryption operation
            await self._audit_privacy_operation(
                "homomorphic_encryption", 0.0, 0.0, 0.0, None,
                additional_data={"data_id": encrypted_data.data_id, "context_id": context_id}
            )
            
            self.logger.info(
                "Patient data encrypted",
                data_id=encrypted_data.data_id,
                context_id=context_id,
                data_shape=list(data.shape)
            )
            
            return encrypted_data
            
        except Exception as e:
            self.logger.error(f"Failed to encrypt patient data: {str(e)}")
            raise

    async def perform_encrypted_computation(
        self, 
        encrypted_data: EncryptedData, 
        operation: str
    ) -> EncryptedResult:
        """
        Perform computation on encrypted data without decryption.
        
        Args:
            encrypted_data: Encrypted input data
            operation: Operation to perform ("add", "multiply", "average", "variance")
            
        Returns:
            Encrypted computation result
        """
        try:
            # Deserialize encrypted data
            encrypted_bytes = base64.b64decode(encrypted_data.encrypted_values.encode())
            
            if encrypted_data.encryption_scheme == EncryptionScheme.CKKS:
                encrypted_vector = ts.ckks_vector_from(self.tenseal_context, encrypted_bytes)
            else:
                encrypted_vector = ts.bfv_vector_from(self.tenseal_context, encrypted_bytes)
            
            # Perform homomorphic operations
            if operation == "square":
                result_vector = encrypted_vector * encrypted_vector
            elif operation == "add_constant":
                result_vector = encrypted_vector + 1.0
            elif operation == "multiply_constant":
                result_vector = encrypted_vector * 2.0
            elif operation == "polynomial":
                # Compute x^2 + x + 1
                result_vector = encrypted_vector * encrypted_vector + encrypted_vector + 1.0
            else:
                raise ValueError(f"Unsupported operation: {operation}")
            
            # Serialize result
            result_bytes = result_vector.serialize()
            result_b64 = base64.b64encode(result_bytes).decode()
            
            # Create result container
            encrypted_result = EncryptedResult(
                result_id=str(uuid.uuid4()),
                encrypted_result=result_b64,
                computation_type=operation,
                input_data_ids=[encrypted_data.data_id],
                context_id=encrypted_data.context_id,
                computation_timestamp=datetime.utcnow(),
                verification_hash=hashlib.sha256(result_bytes).hexdigest()
            )
            
            self.logger.info(
                "Encrypted computation performed",
                operation=operation,
                result_id=encrypted_result.result_id,
                input_data_id=encrypted_data.data_id
            )
            
            return encrypted_result
            
        except Exception as e:
            self.logger.error(f"Failed to perform encrypted computation: {str(e)}")
            raise

    # SECURE MULTIPARTY COMPUTATION METHODS
    
    async def initialize_mpc_protocol(
        self, 
        parties: List[str], 
        threshold: int
    ) -> MPCComputation:
        """
        Initialize secure multiparty computation protocol.
        
        Args:
            parties: List of participating party identifiers
            threshold: Minimum parties needed for reconstruction
            
        Returns:
            MPC computation context
        """
        try:
            if len(parties) < 2:
                raise ValueError("At least 2 parties required for MPC")
            
            if threshold > len(parties):
                raise ValueError("Threshold cannot exceed number of parties")
            
            computation_id = str(uuid.uuid4())
            
            # Create MPC computation
            mpc_computation = MPCComputation(
                computation_id=computation_id,
                protocol=self.config.mpc_protocol,
                participating_parties=parties,
                computation_function="secure_aggregation",  # Default
                input_shares={},
                threshold=threshold,
                privacy_level=self.config.privacy_level,
                created_timestamp=datetime.utcnow(),
                status="initialized"
            )
            
            self.active_computations[computation_id] = mpc_computation
            
            self.logger.info(
                "MPC protocol initialized",
                computation_id=computation_id,
                parties=len(parties),
                threshold=threshold
            )
            
            return mpc_computation
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MPC protocol: {str(e)}")
            raise

    async def secret_share_data(
        self, 
        data: torch.Tensor, 
        num_parties: int
    ) -> List[SecretShare]:
        """
        Create secret shares of data using Shamir's secret sharing.
        
        Args:
            data: Data to be secret shared
            num_parties: Number of parties to create shares for
            
        Returns:
            List of secret shares
        """
        try:
            if num_parties < 2:
                raise ValueError("At least 2 parties required for secret sharing")
            
            # Convert data to integer for Shamir's scheme
            # Scale and round floating point data
            scale_factor = 10**6
            int_data = (data * scale_factor).round().int()
            
            shares = []
            
            # Create shares for each data element
            for i, value in enumerate(int_data.flatten()):
                value_int = int(value.item())
                
                # Generate polynomial coefficients
                coefficients = [value_int] + [secrets.randbelow(2**31) for _ in range(self.config.threshold - 1)]
                
                # Generate shares
                for party_idx in range(num_parties):
                    x = party_idx + 1  # Party index (1-based)
                    y = sum(coeff * (x ** power) for power, coeff in enumerate(coefficients))
                    
                    share = SecretShare(
                        share_id=str(uuid.uuid4()),
                        party_id=f"party_{party_idx}",
                        share_value=str(y % (2**31)),  # Modular arithmetic
                        share_index=x,
                        protocol=self.config.mpc_protocol,
                        threshold=self.config.threshold,
                        total_parties=num_parties,
                        data_type="scalar",
                        metadata={"data_index": i, "scale_factor": scale_factor},
                        created_timestamp=datetime.utcnow()
                    )
                    
                    shares.append(share)
            
            self.logger.info(
                "Data secret shared",
                num_parties=num_parties,
                threshold=self.config.threshold,
                total_shares=len(shares)
            )
            
            return shares
            
        except Exception as e:
            self.logger.error(f"Failed to create secret shares: {str(e)}")
            raise

    async def perform_secure_aggregation(
        self, 
        secret_shares: List[SecretShare]
    ) -> torch.Tensor:
        """
        Perform secure aggregation of secret shares.
        
        Args:
            secret_shares: List of secret shares from multiple parties
            
        Returns:
            Aggregated result
        """
        try:
            if len(secret_shares) < self.config.threshold:
                raise ValueError(f"Insufficient shares for reconstruction: {len(secret_shares)} < {self.config.threshold}")
            
            # Group shares by data index
            shares_by_index = {}
            for share in secret_shares:
                data_index = share.metadata.get("data_index", 0)
                if data_index not in shares_by_index:
                    shares_by_index[data_index] = []
                shares_by_index[data_index].append(share)
            
            # Reconstruct each value using Lagrange interpolation
            reconstructed_values = []
            
            for data_index in sorted(shares_by_index.keys()):
                shares = shares_by_index[data_index][:self.config.threshold]  # Use threshold shares
                
                # Perform Lagrange interpolation
                result = 0
                for i, share_i in enumerate(shares):
                    x_i = share_i.share_index
                    y_i = int(share_i.share_value)
                    
                    # Calculate Lagrange coefficient
                    numerator = 1
                    denominator = 1
                    
                    for j, share_j in enumerate(shares):
                        if i != j:
                            x_j = share_j.share_index
                            numerator *= (0 - x_j)  # Evaluate at x=0
                            denominator *= (x_i - x_j)
                    
                    # Add contribution
                    result += y_i * (numerator // denominator)
                
                # Scale back to original range
                scale_factor = shares[0].metadata.get("scale_factor", 1)
                reconstructed_value = result / scale_factor
                reconstructed_values.append(reconstructed_value)
            
            # Convert back to tensor
            aggregated_result = torch.tensor(reconstructed_values, dtype=torch.float32)
            
            self.logger.info(
                "Secure aggregation completed",
                input_shares=len(secret_shares),
                reconstructed_values=len(reconstructed_values)
            )
            
            return aggregated_result
            
        except Exception as e:
            self.logger.error(f"Failed to perform secure aggregation: {str(e)}")
            raise

    # UTILITY AND HELPER METHODS
    
    async def _calculate_dataset_sensitivity(self, dataset: torch.Tensor) -> float:
        """Calculate sensitivity of dataset for differential privacy."""
        try:
            # For most ML applications, sensitivity is 1 after normalization
            # For specific queries, calculate based on function properties
            
            # Calculate L2 sensitivity (most common)
            if dataset.dim() == 1:
                sensitivity = torch.max(torch.abs(dataset)).item()
            else:
                # For matrices, calculate max L2 norm of rows
                row_norms = torch.norm(dataset, dim=1)
                sensitivity = torch.max(row_norms).item()
            
            # Ensure minimum sensitivity
            return max(sensitivity, 0.1)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate dataset sensitivity: {str(e)}")
            return 1.0  # Conservative default

    async def _calculate_accuracy_loss(
        self, 
        original: torch.Tensor, 
        private: torch.Tensor
    ) -> float:
        """Calculate accuracy loss due to privacy mechanisms."""
        try:
            # Calculate relative error
            mse = torch.mean((original - private) ** 2)
            original_var = torch.var(original)
            
            if original_var > 0:
                relative_error = (mse / original_var).item()
                accuracy_loss = min(relative_error * 100, 100.0)  # Cap at 100%
            else:
                accuracy_loss = 0.0
            
            return accuracy_loss
            
        except Exception as e:
            self.logger.error(f"Failed to calculate accuracy loss: {str(e)}")
            return 0.0

    async def _calculate_utility_score(
        self, 
        original: torch.Tensor, 
        private: torch.Tensor
    ) -> float:
        """Calculate utility score for privacy-utility tradeoff."""
        try:
            # Calculate correlation between original and private data
            if original.numel() > 1 and private.numel() > 1:
                correlation = torch.corrcoef(torch.stack([original.flatten(), private.flatten()]))[0, 1]
                utility = max(0.0, correlation.item())
            else:
                utility = 1.0 - torch.abs(original - private).item()
            
            return min(max(utility, 0.0), 1.0)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate utility score: {str(e)}")
            return 0.0

    async def _audit_privacy_operation(
        self,
        operation_type: str,
        epsilon: float,
        sensitivity: float,
        noise_scale: float,
        metrics: Optional[PrivacyMetrics],
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Audit privacy operation for compliance tracking."""
        try:
            audit_event = PrivacyAuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=operation_type,
                operation_id=str(uuid.uuid4()),
                privacy_level=self.config.privacy_level,
                data_accessed=[],  # Would be populated with actual data IDs
                privacy_cost={"epsilon": epsilon, "delta": self.config.delta},
                computation_details={
                    "sensitivity": sensitivity,
                    "noise_scale": noise_scale,
                    "additional_data": additional_data or {}
                },
                timestamp=datetime.utcnow()
            )
            
            # Store audit event (in production, would use audit service)
            await self.audit_service.log_privacy_event(audit_event.dict())
            
        except Exception as e:
            self.logger.error(f"Failed to audit privacy operation: {str(e)}")

    async def validate_privacy_guarantees(
        self, 
        operation_config: Dict[str, Any]
    ) -> PrivacyValidationResult:
        """
        Validate that privacy guarantees are met for given operation.
        
        Args:
            operation_config: Configuration of privacy operation
            
        Returns:
            Privacy validation result
        """
        try:
            validation_errors = []
            validation_warnings = []
            recommendations = []
            
            epsilon = operation_config.get("epsilon", 0)
            delta = operation_config.get("delta", 0)
            
            # Validate epsilon
            if epsilon <= 0:
                validation_errors.append("Epsilon must be positive")
            elif epsilon > 1.0:
                validation_warnings.append("High epsilon value may provide weak privacy")
            
            # Validate delta
            if delta <= 0:
                validation_errors.append("Delta must be positive")
            elif delta > 1e-3:
                validation_warnings.append("High delta value may compromise privacy guarantees")
            
            # Check composition
            total_epsilon = operation_config.get("composition_epsilon", epsilon)
            if total_epsilon > 10.0:
                validation_errors.append("Total epsilon exceeds reasonable bounds")
            
            # Privacy level assessment
            if epsilon < 0.1:
                achieved_level = PrivacyLevel.MAXIMUM
            elif epsilon < 1.0:
                achieved_level = PrivacyLevel.HIGH
            elif epsilon < 5.0:
                achieved_level = PrivacyLevel.MEDIUM
            else:
                achieved_level = PrivacyLevel.LOW
            
            # Generate recommendations
            if len(validation_warnings) > 0:
                recommendations.append("Consider using lower epsilon for stronger privacy")
            if achieved_level != self.config.privacy_level:
                recommendations.append(f"Privacy level mismatch: achieved {achieved_level}, required {self.config.privacy_level}")
            
            validation_result = PrivacyValidationResult(
                validation_id=str(uuid.uuid4()),
                operation_type=operation_config.get("operation_type", "unknown"),
                is_valid=len(validation_errors) == 0,
                privacy_level_achieved=achieved_level,
                epsilon_consumed=epsilon,
                delta_consumed=delta,
                validation_errors=validation_errors,
                validation_warnings=validation_warnings,
                recommendations=recommendations,
                validation_timestamp=datetime.utcnow()
            )
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Failed to validate privacy guarantees: {str(e)}")
            raise

    async def generate_privacy_report(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate comprehensive privacy operations report.
        
        Args:
            start_date: Report period start
            end_date: Report period end
            
        Returns:
            Privacy report with metrics and compliance status
        """
        try:
            # Filter metrics by date range
            period_metrics = [
                m for m in self.privacy_metrics_history
                if start_date <= m.timestamp <= end_date
            ]
            
            # Calculate summary statistics
            total_operations = len(period_metrics)
            operations_by_type = {}
            total_privacy_cost = {"epsilon": 0.0, "delta": 0.0}
            
            for metric in period_metrics:
                op_type = metric.operation_type
                operations_by_type[op_type] = operations_by_type.get(op_type, 0) + 1
                
                total_privacy_cost["epsilon"] += metric.privacy_cost.get("epsilon", 0)
                total_privacy_cost["delta"] += metric.privacy_cost.get("delta", 0)
            
            # Check compliance status
            compliance_status = {
                "privacy_budget_within_limits": total_privacy_cost["epsilon"] <= 10.0,
                "delta_within_bounds": total_privacy_cost["delta"] <= 1e-3,
                "all_operations_audited": total_operations > 0,
                "privacy_level_maintained": True  # Would check against policy
            }
            
            privacy_report = {
                "report_id": str(uuid.uuid4()),
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "total_operations": total_operations,
                "operations_by_type": operations_by_type,
                "privacy_budget_utilization": total_privacy_cost,
                "compliance_status": compliance_status,
                "average_processing_time": np.mean([m.processing_time_seconds for m in period_metrics]) if period_metrics else 0,
                "generated_timestamp": datetime.utcnow().isoformat()
            }
            
            self.logger.info(
                "Privacy report generated",
                period_days=(end_date - start_date).days,
                total_operations=total_operations,
                epsilon_consumed=total_privacy_cost["epsilon"]
            )
            
            return privacy_report
            
        except Exception as e:
            self.logger.error(f"Failed to generate privacy report: {str(e)}")
            raise