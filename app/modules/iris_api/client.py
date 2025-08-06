import asyncio
import aiohttp
import hashlib
import hmac
import json
import time
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
from urllib.parse import urljoin
import structlog
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.security import security_manager
from app.core.event_bus import EventType, publish_api_event
from app.modules.iris_api.schemas import (
    IRISAuthResponse, IRISPatientResponse, IRISImmunizationResponse,
    HealthStatus, SyncStatus
)
from app.schemas.fhir_r4 import (
    FHIRPatient, FHIRImmunization, FHIRBundle, FHIRAllergyIntolerance,
    validate_fhir_resource, TerminologyValidator, create_search_bundle,
    create_fhir_bundle
)

logger = structlog.get_logger()

class CircuitBreakerError(Exception):
    """Circuit breaker is open."""
    pass

class IRISAPIError(Exception):
    """IRIS API specific error."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)

class CircuitBreaker:
    """Circuit breaker pattern implementation for API resilience."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half-open
        
    def call(self, func):
        """Decorator to wrap function calls with circuit breaker logic."""
        async def wrapper(*args, **kwargs):
            if self.state == "open":
                if self._should_attempt_reset():
                    self.state = "half-open"
                    logger.info("Circuit breaker half-open, attempting reset")
                else:
                    raise CircuitBreakerError("Circuit breaker is open")
            
            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
    
    def _on_success(self):
        """Handle successful operation."""
        if self.state == "half-open":
            self.state = "closed"
            logger.info("Circuit breaker reset to closed state")
        self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning("Circuit breaker opened", failure_count=self.failure_count)

class IRISAPIClient:
    """Secure IRIS API client with OAuth2/HMAC authentication."""
    
    def __init__(self, base_url: str, client_id: str, client_secret: str, auth_type: str = "oauth2"):
        self.settings = get_settings()
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_type = auth_type
        
        # Authentication state
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.settings.IRIS_API_RETRY_ATTEMPTS,
            recovery_timeout=60
        )
        
        # HTTP client configuration
        self.timeout = aiohttp.ClientTimeout(
            total=self.settings.IRIS_API_TIMEOUT,
            connect=10.0,
            sock_read=self.settings.IRIS_API_TIMEOUT,
            sock_connect=10.0
        )
        
        # Rate limiting
        self.rate_limiter = RateLimiter(
            requests_per_second=10,
            burst_size=20
        )
    
    @asynccontextmanager
    async def get_client(self):
        """Async context manager for HTTP client."""
        connector = aiohttp.TCPConnector(
            limit=20,  # max connections
            limit_per_host=5,  # max keepalive connections per host
            ssl=True,  # Always verify SSL in production
            use_dns_cache=True,
            ttl_dns_cache=300
        )
        
        async with aiohttp.ClientSession(
            timeout=self.timeout,
            connector=connector,
            headers={"User-Agent": "IRIS-Integration-Client/1.0"}
        ) as client:
            yield client
    
    async def authenticate(self) -> IRISAuthResponse:
        """Authenticate with IRIS API using configured method."""
        if self.auth_type == "oauth2":
            return await self._oauth2_authenticate()
        elif self.auth_type == "hmac":
            return await self._hmac_authenticate()
        else:
            raise IRISAPIError(f"Unsupported authentication type: {self.auth_type}")
    
    async def _oauth2_authenticate(self) -> IRISAuthResponse:
        """OAuth2 authentication flow."""
        auth_url = urljoin(self.base_url, "/oauth/token")
        
        auth_data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "read write"
        }
        
        try:
            async with self.get_client() as client:
                response = await client.post(
                    auth_url,
                    data=auth_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status == 200:
                    response_data = await response.json()
                    auth_response = IRISAuthResponse(**response_data)
                    self.access_token = auth_response.access_token
                    self.token_expires_at = datetime.utcnow() + timedelta(seconds=auth_response.expires_in - 60)
                    
                    await publish_api_event(
                        EventType.IRIS_API_RESPONSE,
                        endpoint="/oauth/token",
                        method="POST",
                        status_code=200,
                        data={"auth_type": "oauth2", "expires_in": auth_response.expires_in}
                    )
                    
                    logger.info("OAuth2 authentication successful")
                    return auth_response
                else:
                    response_text = await response.text()
                    try:
                        error_data = await response.json()
                    except:
                        error_data = {"error": response_text}
                    
                    raise IRISAPIError(
                        f"OAuth2 authentication failed: {response.status}",
                        response.status,
                        error_data
                    )
                    
        except aiohttp.ClientError as e:
            logger.error("OAuth2 authentication request failed", error=str(e))
            raise IRISAPIError(f"Authentication request failed: {str(e)}")
    
    async def _hmac_authenticate(self) -> IRISAuthResponse:
        """HMAC authentication for API requests."""
        # HMAC doesn't require a separate auth step, but we simulate the response
        # In real implementation, this might involve key exchange or validation
        
        # Validate HMAC credentials
        if not self.client_secret:
            raise IRISAPIError("HMAC secret is required for HMAC authentication")
        
        # Generate a session token for HMAC
        session_token = secrets.token_urlsafe(32)
        self.access_token = session_token
        self.token_expires_at = datetime.utcnow() + timedelta(hours=24)  # HMAC tokens last longer
        
        logger.info("HMAC authentication initialized")
        
        return IRISAuthResponse(
            access_token=session_token,
            token_type="HMAC",
            expires_in=86400,  # 24 hours
            scope="read write"
        )
    
    async def _ensure_authenticated(self):
        """Ensure we have a valid authentication token."""
        if not self.access_token or (self.token_expires_at and datetime.utcnow() >= self.token_expires_at):
            logger.info("Token expired or missing, re-authenticating")
            await self.authenticate()
    
    def _generate_hmac_signature(self, method: str, path: str, body: str, timestamp: str) -> str:
        """Generate HMAC signature for request authentication."""
        string_to_sign = f"{method}\n{path}\n{body}\n{timestamp}"
        signature = hmac.new(
            self.client_secret.encode(),
            string_to_sign.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_auth_headers(self, method: str, path: str, body: str = "") -> Dict[str, str]:
        """Get authentication headers based on auth type."""
        headers = {}
        
        if self.auth_type == "oauth2":
            headers["Authorization"] = f"Bearer {self.access_token}"
        elif self.auth_type == "hmac":
            timestamp = str(int(time.time()))
            signature = self._generate_hmac_signature(method, path, body, timestamp)
            headers.update({
                "Authorization": f"HMAC {self.client_id}:{signature}",
                "X-Timestamp": timestamp,
                "X-Client-ID": self.client_id
            })
        
        return headers
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make authenticated API request with retry logic and circuit breaker."""
        # Check circuit breaker state
        if self.circuit_breaker.state == "open":
            if self.circuit_breaker._should_attempt_reset():
                self.circuit_breaker.state = "half-open"
                logger.info("Circuit breaker half-open, attempting reset")
            else:
                raise CircuitBreakerError("Circuit breaker is open")
        
        if not correlation_id:
            correlation_id = secrets.token_hex(8)
        
        await self._ensure_authenticated()
        await self.rate_limiter.acquire()
        
        url = urljoin(self.base_url, endpoint)
        body = json.dumps(data) if data else ""
        auth_headers = self._get_auth_headers(method, endpoint, body)
        
        headers = {
            "Content-Type": "application/json",
            "X-Correlation-ID": correlation_id,
            **auth_headers
        }
        
        start_time = time.time()
        attempt = 0
        last_exception = None
        
        while attempt < self.settings.IRIS_API_RETRY_ATTEMPTS:
            attempt += 1
            
            try:
                async with self.get_client() as client:
                    request_kwargs = {
                        "url": url,
                        "headers": headers
                    }
                    
                    if data:
                        request_kwargs["json"] = data
                    if params:
                        request_kwargs["params"] = params
                        
                    response = await client.request(method, **request_kwargs)
                    
                    duration_ms = int((time.time() - start_time) * 1000)
                    
                    await publish_api_event(
                        EventType.IRIS_API_RESPONSE,
                        endpoint=endpoint,
                        method=method,
                        status_code=response.status,
                        data={
                            "correlation_id": correlation_id,
                            "attempt": attempt,
                            "duration_ms": duration_ms
                        }
                    )
                    
                    if response.status < 400:
                        # Success - update circuit breaker
                        self.circuit_breaker._on_success()
                        logger.info("API request successful", 
                                  endpoint=endpoint, method=method, 
                                  status_code=response.status,
                                  duration_ms=duration_ms)
                        
                        # Handle response content
                        try:
                            return await response.json()
                        except:
                            return {}
                            
                    elif response.status in [401, 403]:
                        # Authentication error, try to re-authenticate
                        if attempt == 1:
                            await self.authenticate()
                            auth_headers = self._get_auth_headers(method, endpoint, body)
                            headers.update(auth_headers)
                            continue
                        else:
                            try:
                                error_data = await response.json()
                            except:
                                error_data = {"error": await response.text()}
                                
                            raise IRISAPIError(
                                f"Authentication failed: {response.status}",
                                response.status,
                                error_data
                            )
                    elif response.status in [429, 503]:
                        # Rate limited or service unavailable, wait and retry
                        wait_time = min(2 ** attempt, 30)  # Exponential backoff, max 30 seconds
                        logger.warning("Rate limited or service unavailable, retrying",
                                     attempt=attempt, wait_time=wait_time)
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        try:
                            error_data = await response.json()
                        except:
                            error_data = {"error": await response.text()}
                            
                        raise IRISAPIError(
                            f"API request failed: {response.status}",
                            response.status,
                            error_data
                        )
                        
            except aiohttp.ClientError as e:
                last_exception = e
                wait_time = min(2 ** attempt, 30)
                logger.warning("Request error, retrying", 
                             error=str(e), attempt=attempt, wait_time=wait_time)
                
                if attempt < self.settings.IRIS_API_RETRY_ATTEMPTS:
                    await asyncio.sleep(wait_time)
                    continue
        
        # All retries exhausted - update circuit breaker
        self.circuit_breaker._on_failure()
        error_msg = f"Request failed after {self.settings.IRIS_API_RETRY_ATTEMPTS} attempts"
        if last_exception:
            error_msg += f": {str(last_exception)}"
        
        raise IRISAPIError(error_msg)
    
    # ============================================
    # IRIS API SPECIFIC METHODS
    # ============================================
    
    async def get_patient(self, patient_id: str) -> IRISPatientResponse:
        """Get patient data by ID with FHIR R4 support."""
        endpoint = f"/fhir/r4/Patient/{patient_id}"
        response_data = await self._make_request("GET", endpoint)
        
        # Process FHIR R4 Patient resource
        fhir_patient = self._process_fhir_patient(response_data)
        return fhir_patient
    
    async def get_patient_immunizations(self, patient_id: str) -> List[IRISImmunizationResponse]:
        """Get patient immunization records with FHIR R4 support."""
        endpoint = f"/fhir/r4/Immunization"
        params = {"patient": patient_id}
        response_data = await self._make_request("GET", endpoint, params=params)
        
        # Process FHIR R4 Bundle
        immunizations = []
        if response_data.get("resourceType") == "Bundle":
            for entry in response_data.get("entry", []):
                if entry.get("resource", {}).get("resourceType") == "Immunization":
                    fhir_immunization = self._process_fhir_immunization(entry["resource"], patient_id)
                    immunizations.append(fhir_immunization)
        
        return immunizations
    
    async def search_patients(self, search_params: Dict[str, str]) -> List[IRISPatientResponse]:
        """Search for patients with FHIR R4 parameters."""
        endpoint = "/fhir/r4/Patient"
        response_data = await self._make_request("GET", endpoint, params=search_params)
        
        patients = []
        if response_data.get("resourceType") == "Bundle":
            for entry in response_data.get("entry", []):
                if entry.get("resource", {}).get("resourceType") == "Patient":
                    fhir_patient = self._process_fhir_patient(entry["resource"])
                    patients.append(fhir_patient)
        
        return patients
    
    async def get_patient_bundle(self, patient_id: str) -> Dict[str, Any]:
        """Get complete patient bundle including all related resources."""
        endpoint = f"/fhir/r4/Patient/{patient_id}/$everything"
        response_data = await self._make_request("GET", endpoint)
        
        # Process complete FHIR Bundle
        processed_bundle = self._process_fhir_bundle(response_data)
        return processed_bundle
    
    async def sync_immunization_registry(self, registry_params: Dict[str, Any]) -> Dict[str, Any]:
        """Sync with state immunization registry via IRIS."""
        endpoint = "/registry/immunizations/sync"
        response_data = await self._make_request("POST", endpoint, data=registry_params)
        return response_data
    
    async def get_provider_directory(self, search_params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get healthcare provider directory from IRIS."""
        endpoint = "/fhir/r4/Practitioner"
        response_data = await self._make_request("GET", endpoint, params=search_params or {})
        return response_data
    
    async def submit_immunization_record(self, immunization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit new immunization record via IRIS."""
        endpoint = "/fhir/r4/Immunization"
        response_data = await self._make_request("POST", endpoint, data=immunization_data)
        return response_data
    
    async def get_vaccine_inventory(self, location_id: Optional[str] = None) -> Dict[str, Any]:
        """Get vaccine inventory from IRIS."""
        endpoint = "/inventory/vaccines"
        params = {"location": location_id} if location_id else {}
        response_data = await self._make_request("GET", endpoint, params=params)
        return response_data
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check against IRIS API."""
        try:
            endpoint = "/health"
            start_time = time.time()
            response_data = await self._make_request("GET", endpoint)
            response_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "status": HealthStatus.HEALTHY,
                "response_time_ms": response_time_ms,
                "data": response_data
            }
            
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return {
                "status": HealthStatus.UNHEALTHY,
                "error": str(e),
                "response_time_ms": None
            }
    
    # ============================================
    # FHIR R4 DATA PROCESSING METHODS
    # ============================================
    
    def _process_fhir_patient(self, fhir_patient: Dict[str, Any]) -> IRISPatientResponse:
        """Process FHIR R4 Patient resource into internal format with enhanced validation."""
        try:
            # Validate FHIR Patient resource structure
            fhir_patient_obj = FHIRPatient(**fhir_patient)
            if not validate_fhir_resource(fhir_patient_obj):
                logger.warning("FHIR Patient validation failed", patient_id=fhir_patient.get("id"))
        except Exception as e:
            logger.warning("FHIR Patient structure validation error", error=str(e), patient_id=fhir_patient.get("id"))
        
        patient_id = fhir_patient.get("id", "")
        
        # Extract MRN from identifiers with improved validation
        mrn = None
        for identifier in fhir_patient.get("identifier", []):
            # Check for MRN type code in coding
            if identifier.get("type", {}).get("coding"):
                for coding in identifier["type"]["coding"]:
                    if coding.get("code") == "MR":
                        mrn = identifier.get("value")
                        # Validate MRN has proper system
                        if not identifier.get("system"):
                            logger.warning("MRN identifier missing system", patient_id=patient_id)
                        break
            if mrn:
                break
        
        # Extract demographics with FHIR R4 compliance
        demographics = {}
        
        # Name (handle multiple names, prefer official)
        if fhir_patient.get("name"):
            official_name = None
            for name in fhir_patient["name"]:
                if name.get("use") == "official":
                    official_name = name
                    break
            
            selected_name = official_name or fhir_patient["name"][0]
            demographics["first_name"] = " ".join(selected_name.get("given", []))
            demographics["last_name"] = selected_name.get("family", "")
            
            # Store full name text if available
            if selected_name.get("text"):
                demographics["full_name"] = selected_name["text"]
        
        # Birth date
        if fhir_patient.get("birthDate"):
            demographics["date_of_birth"] = fhir_patient["birthDate"]
        
        # Gender (validate against FHIR value set)
        if fhir_patient.get("gender"):
            valid_genders = ["male", "female", "other", "unknown"]
            if fhir_patient["gender"] in valid_genders:
                demographics["gender"] = fhir_patient["gender"]
            else:
                logger.warning("Invalid gender value", gender=fhir_patient["gender"], patient_id=patient_id)
        
        # Address (handle multiple addresses, prefer home)
        if fhir_patient.get("address"):
            home_address = None
            for addr in fhir_patient["address"]:
                if addr.get("use") == "home":
                    home_address = addr
                    break
            
            selected_address = home_address or fhir_patient["address"][0]
            demographics["address"] = {
                "line": selected_address.get("line", []),
                "city": selected_address.get("city"),
                "state": selected_address.get("state"),
                "postal_code": selected_address.get("postalCode"),
                "country": selected_address.get("country"),
                "use": selected_address.get("use"),
                "type": selected_address.get("type")
            }
        
        # Contact info (handle multiple contacts by priority)
        if fhir_patient.get("telecom"):
            phone_contacts = []
            email_contacts = []
            
            for contact in fhir_patient["telecom"]:
                if contact.get("system") == "phone":
                    phone_contacts.append(contact)
                elif contact.get("system") == "email":
                    email_contacts.append(contact)
            
            # Prefer home/mobile for phone, work/home for email
            if phone_contacts:
                home_phone = next((c for c in phone_contacts if c.get("use") == "home"), None)
                mobile_phone = next((c for c in phone_contacts if c.get("use") == "mobile"), None)
                demographics["phone"] = (home_phone or mobile_phone or phone_contacts[0]).get("value")
            
            if email_contacts:
                work_email = next((c for c in email_contacts if c.get("use") == "work"), None)
                home_email = next((c for c in email_contacts if c.get("use") == "home"), None)
                demographics["email"] = (work_email or home_email or email_contacts[0]).get("value")
        
        # Active status
        demographics["active"] = fhir_patient.get("active", True)
        
        # Deceased information
        if fhir_patient.get("deceasedBoolean"):
            demographics["deceased"] = True
        elif fhir_patient.get("deceasedDateTime"):
            demographics["deceased"] = True
            demographics["deceased_date"] = fhir_patient["deceasedDateTime"]
        
        return IRISPatientResponse(
            patient_id=patient_id,
            mrn=mrn,
            demographics=demographics,
            last_updated=datetime.fromisoformat(fhir_patient.get("meta", {}).get("lastUpdated", datetime.utcnow().isoformat()).replace("Z", "+00:00")),
            data_version=fhir_patient.get("meta", {}).get("versionId")
        )
    
    def _process_fhir_immunization(self, fhir_immunization: Dict[str, Any], patient_id: str) -> IRISImmunizationResponse:
        """Process FHIR R4 Immunization resource into internal format with enhanced validation."""
        try:
            # Validate FHIR Immunization resource structure
            fhir_immunization_obj = FHIRImmunization(**fhir_immunization)
            if not validate_fhir_resource(fhir_immunization_obj):
                logger.warning("FHIR Immunization validation failed", immunization_id=fhir_immunization.get("id"))
                
            # Validate vaccine code terminology
            if fhir_immunization_obj.vaccineCode and fhir_immunization_obj.vaccineCode.coding:
                for coding in fhir_immunization_obj.vaccineCode.coding:
                    if not TerminologyValidator.validate_vaccine_code(coding):
                        logger.warning("Vaccine code validation failed", 
                                     code=coding.code, system=coding.system,
                                     immunization_id=fhir_immunization.get("id"))
        except Exception as e:
            logger.warning("FHIR Immunization structure validation error", 
                         error=str(e), immunization_id=fhir_immunization.get("id"))
        
        immunization_id = fhir_immunization.get("id", "")
        
        # Extract vaccine information with improved validation
        vaccine_code = ""
        vaccine_name = ""
        vaccine_system = ""
        
        if fhir_immunization.get("vaccineCode", {}).get("coding"):
            # Prefer CVX coding if available
            cvx_coding = None
            for coding in fhir_immunization["vaccineCode"]["coding"]:
                if coding.get("system") == TerminologyValidator.TERMINOLOGY_SYSTEMS['CVX']:
                    cvx_coding = coding
                    break
            
            selected_coding = cvx_coding or fhir_immunization["vaccineCode"]["coding"][0]
            vaccine_code = selected_coding.get("code", "")
            vaccine_name = selected_coding.get("display", "")
            vaccine_system = selected_coding.get("system", "")
            
            # Validate CVX code if system is CVX
            if vaccine_system == TerminologyValidator.TERMINOLOGY_SYSTEMS['CVX']:
                if vaccine_code not in TerminologyValidator.VACCINE_CODES:
                    logger.warning("Unknown CVX vaccine code", code=vaccine_code, immunization_id=immunization_id)
        
        # Administration date with validation 
        admin_date = None
        if fhir_immunization.get("occurrenceDateTime"):
            try:
                admin_date = datetime.fromisoformat(fhir_immunization["occurrenceDateTime"].replace("Z", "+00:00")).date()
            except ValueError as e:
                logger.warning("Invalid occurrence date format", 
                             date=fhir_immunization["occurrenceDateTime"], 
                             immunization_id=immunization_id, error=str(e))
        elif fhir_immunization.get("occurrenceString"):
            # Handle string-based dates (less precise)
            logger.info("Using string-based occurrence date", 
                       date_string=fhir_immunization["occurrenceString"],
                       immunization_id=immunization_id)
        
        # Lot number and manufacturer with validation
        lot_number = None
        manufacturer = None
        expiration_date = None
        
        if fhir_immunization.get("lotNumber"):
            lot_number = fhir_immunization["lotNumber"]
            # Validate lot number format (basic validation)
            if len(lot_number) < 3:
                logger.warning("Potentially invalid lot number", lot_number=lot_number, immunization_id=immunization_id)
        
        if fhir_immunization.get("manufacturer"):
            if fhir_immunization["manufacturer"].get("display"):
                manufacturer = fhir_immunization["manufacturer"]["display"]
            elif fhir_immunization["manufacturer"].get("reference"):
                manufacturer = fhir_immunization["manufacturer"]["reference"]
        
        if fhir_immunization.get("expirationDate"):
            expiration_date = fhir_immunization["expirationDate"]
        
        # Dose information with validation
        dose_number = None
        series_complete = False
        series_doses = None
        
        if fhir_immunization.get("protocolApplied"):
            for protocol in fhir_immunization["protocolApplied"]:
                dose_number = protocol.get("doseNumberPositiveInt")
                series_doses = protocol.get("seriesDosesPositiveInt")
                
                if dose_number and series_doses:
                    series_complete = dose_number >= series_doses
                    break
        
        # Administration details with enhanced extraction
        administered_by = None
        administration_site = None
        route = None
        dose_quantity = None
        
        # Performer information
        if fhir_immunization.get("performer"):
            for performer in fhir_immunization["performer"]:
                if performer.get("actor", {}).get("display"):
                    administered_by = performer["actor"]["display"]
                    break
        
        # Administration site
        if fhir_immunization.get("site", {}).get("coding"):
            site_coding = fhir_immunization["site"]["coding"][0]
            administration_site = site_coding.get("display") or site_coding.get("code")
        
        # Route of administration
        if fhir_immunization.get("route", {}).get("coding"):
            route_coding = fhir_immunization["route"]["coding"][0]
            route = route_coding.get("display") or route_coding.get("code")
        
        # Dose quantity
        if fhir_immunization.get("doseQuantity"):
            dose_quantity = f"{fhir_immunization['doseQuantity'].get('value', '')} {fhir_immunization['doseQuantity'].get('unit', '')}"
        
        # Validate status
        status = fhir_immunization.get("status", "completed")
        if status not in ["completed", "entered-in-error", "not-done"]:
            logger.warning("Invalid immunization status", status=status, immunization_id=immunization_id)
            status = "completed"  # Default to completed
        
        return IRISImmunizationResponse(
            immunization_id=immunization_id,
            patient_id=patient_id,
            vaccine_code=vaccine_code,
            vaccine_name=vaccine_name,
            administration_date=admin_date or datetime.now().date(),
            lot_number=lot_number,
            manufacturer=manufacturer,
            dose_number=dose_number,
            series_complete=series_complete,
            administered_by=administered_by,
            administration_site=administration_site,
            route=route
        )
    
    def _process_fhir_bundle(self, fhir_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Process complete FHIR R4 Bundle for patient data with enhanced validation."""
        processed_data = {
            "patient": None,
            "immunizations": [],
            "allergies": [],
            "medications": [],
            "encounters": [],
            "observations": [],
            "bundle_metadata": {},
            "validation_errors": []
        }
        
        try:
            # Validate FHIR Bundle structure
            fhir_bundle_obj = FHIRBundle(**fhir_bundle)
            if not validate_fhir_resource(fhir_bundle_obj):
                processed_data["validation_errors"].append("Bundle structure validation failed")
        except Exception as e:
            processed_data["validation_errors"].append(f"Bundle validation error: {str(e)}")
        
        if fhir_bundle.get("resourceType") != "Bundle":
            processed_data["validation_errors"].append("Resource is not a Bundle")
            return processed_data
        
        # Extract bundle metadata
        processed_data["bundle_metadata"] = {
            "type": fhir_bundle.get("type"),
            "total": fhir_bundle.get("total"),
            "timestamp": fhir_bundle.get("timestamp"),
            "id": fhir_bundle.get("id")
        }
        
        # Process bundle entries
        for entry in fhir_bundle.get("entry", []):
            try:
                resource = entry.get("resource", {})
                resource_type = resource.get("resourceType")
                
                if resource_type == "Patient":
                    processed_data["patient"] = self._process_fhir_patient(resource)
                    
                elif resource_type == "Immunization":
                    # Extract patient ID from reference
                    patient_ref = resource.get("patient", {}).get("reference", "")
                    patient_id = patient_ref.split("/")[-1] if "/" in patient_ref else ""
                    
                    if not patient_id:
                        # Try to get from identifier
                        patient_identifier = resource.get("patient", {}).get("identifier")
                        if patient_identifier and patient_identifier.get("value"):
                            patient_id = patient_identifier["value"]
                    
                    if patient_id:
                        immunization = self._process_fhir_immunization(resource, patient_id)
                        processed_data["immunizations"].append(immunization)
                    else:
                        processed_data["validation_errors"].append(f"Immunization {resource.get('id')} missing patient reference")
                
                elif resource_type == "AllergyIntolerance":
                    try:
                        # Validate AllergyIntolerance structure
                        allergy_obj = FHIRAllergyIntolerance(**resource)
                        processed_data["allergies"].append(resource)
                    except Exception as e:
                        processed_data["validation_errors"].append(f"AllergyIntolerance validation error: {str(e)}")
                        processed_data["allergies"].append(resource)  # Include anyway but log error
                
                elif resource_type == "MedicationStatement":
                    processed_data["medications"].append(resource)
                    
                elif resource_type == "Encounter":
                    processed_data["encounters"].append(resource)
                    
                elif resource_type == "Observation":
                    processed_data["observations"].append(resource)
                    
                else:
                    # Log unknown resource types
                    logger.info("Unknown resource type in bundle", resource_type=resource_type)
                    
            except Exception as e:
                processed_data["validation_errors"].append(f"Error processing bundle entry: {str(e)}")
                continue
        
        # Log bundle processing summary
        logger.info("FHIR Bundle processed",
                   bundle_type=processed_data["bundle_metadata"]["type"],
                   total_entries=len(fhir_bundle.get("entry", [])),
                   patients=1 if processed_data["patient"] else 0,
                   immunizations=len(processed_data["immunizations"]),
                   allergies=len(processed_data["allergies"]),
                   observations=len(processed_data["observations"]),
                   validation_errors=len(processed_data["validation_errors"]))
        
        return processed_data
    
    def _process_fhir_allergy_intolerance(self, fhir_allergy: Dict[str, Any]) -> Dict[str, Any]:
        """Process FHIR R4 AllergyIntolerance resource."""
        try:
            # Validate FHIR AllergyIntolerance structure
            allergy_obj = FHIRAllergyIntolerance(**fhir_allergy)
            if not validate_fhir_resource(allergy_obj):
                logger.warning("FHIR AllergyIntolerance validation failed", allergy_id=fhir_allergy.get("id"))
        except Exception as e:
            logger.warning("FHIR AllergyIntolerance validation error", error=str(e), allergy_id=fhir_allergy.get("id"))
        
        # Extract key allergy information
        allergy_data = {
            "id": fhir_allergy.get("id"),
            "clinical_status": None,
            "verification_status": None,
            "type": fhir_allergy.get("type"),
            "category": fhir_allergy.get("category", []),
            "criticality": fhir_allergy.get("criticality"),
            "code": None,
            "patient_id": None,
            "onset": None,
            "recorded_date": fhir_allergy.get("recordedDate"),
            "reactions": []
        }
        
        # Extract clinical and verification status
        if fhir_allergy.get("clinicalStatus", {}).get("coding"):
            allergy_data["clinical_status"] = fhir_allergy["clinicalStatus"]["coding"][0].get("code")
        
        if fhir_allergy.get("verificationStatus", {}).get("coding"):
            allergy_data["verification_status"] = fhir_allergy["verificationStatus"]["coding"][0].get("code")
        
        # Extract allergen code
        if fhir_allergy.get("code", {}).get("coding"):
            coding = fhir_allergy["code"]["coding"][0]
            allergy_data["code"] = {
                "system": coding.get("system"),
                "code": coding.get("code"),
                "display": coding.get("display")
            }
        
        # Extract patient reference
        patient_ref = fhir_allergy.get("patient", {}).get("reference", "")
        if patient_ref.startswith("Patient/"):
            allergy_data["patient_id"] = patient_ref.split("/")[-1]
        
        # Extract onset information
        if fhir_allergy.get("onsetDateTime"):
            allergy_data["onset"] = fhir_allergy["onsetDateTime"]
        elif fhir_allergy.get("onsetString"):
            allergy_data["onset"] = fhir_allergy["onsetString"]
        
        # Extract reaction information
        for reaction in fhir_allergy.get("reaction", []):
            reaction_data = {
                "manifestation": [],
                "severity": reaction.get("severity"),
                "onset": reaction.get("onset"),
                "description": reaction.get("description")
            }
            
            for manifestation in reaction.get("manifestation", []):
                if manifestation.get("coding"):
                    coding = manifestation["coding"][0]
                    reaction_data["manifestation"].append({
                        "system": coding.get("system"),
                        "code": coding.get("code"),
                        "display": coding.get("display")
                    })
            
            allergy_data["reactions"].append(reaction_data)
        
        return allergy_data

class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, requests_per_second: float, burst_size: int):
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire a token for making a request."""
        async with self._lock:
            now = time.time()
            time_passed = now - self.last_update
            self.tokens = min(self.burst_size, self.tokens + time_passed * self.requests_per_second)
            self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return
            
            # Need to wait
            wait_time = (1 - self.tokens) / self.requests_per_second
            await asyncio.sleep(wait_time)
            self.tokens = 0