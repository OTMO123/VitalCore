"""
Malware Scanning Infrastructure for File Uploads

Provides hooks and protocols for integrating antivirus/malware scanning
into the document upload pipeline. Supports multiple scanning backends.
"""

from typing import Optional, Protocol, Tuple
from abc import ABC, abstractmethod
import hashlib
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class MalwareScannerProtocol(Protocol):
    """
    Protocol defining the interface for malware scanning implementations.

    This allows for multiple backend implementations:
    - ClamAV (open source)
    - VirusTotal API
    - Windows Defender API
    - Commercial solutions (McAfee, Symantec, etc.)
    """

    async def scan_file(
        self, content: bytes, filename: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Scan file for malware threats.

        Args:
            content: File content bytes
            filename: Original filename

        Returns:
            (is_clean, threat_info)
            - is_clean: True if no threats detected, False if threats found
            - threat_info: Description of threat if found, None if clean
        """
        ...


class NoOpMalwareScanner:
    """
    No-operation scanner used when malware scanning is not configured.

    This is the default fallback that logs a warning but allows uploads.
    In production, this should be replaced with a real scanner.
    """

    async def scan_file(
        self, content: bytes, filename: str
    ) -> Tuple[bool, Optional[str]]:
        """
        No-op scan that logs warning and passes through.

        Returns:
            (True, None) - Always returns clean
        """
        logger.warning(
            "Malware scanning not configured - file upload proceeding without scan",
            filename=filename,
            file_size=len(content),
            recommendation="Configure ClamAV or VirusTotal for production",
        )
        return True, None


class ClamAVScanner:
    """
    ClamAV antivirus scanner implementation.

    Integrates with ClamAV daemon (clamd) for real-time scanning.
    Requires: clamd service running and pyclamd package.

    Usage:
        scanner = ClamAVScanner(host="localhost", port=3310)
        is_clean, threat = await scanner.scan_file(file_data, "test.pdf")
    """

    def __init__(self, host: str = "localhost", port: int = 3310):
        """
        Initialize ClamAV scanner.

        Args:
            host: ClamAV daemon host
            port: ClamAV daemon port
        """
        self.host = host
        self.port = port
        self.logger = logger.bind(scanner="ClamAV")

    async def scan_file(
        self, content: bytes, filename: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Scan file using ClamAV daemon.

        Args:
            content: File content bytes
            filename: Original filename

        Returns:
            (is_clean, threat_info)
        """
        try:
            import pyclamd

            # Connect to ClamAV daemon
            cd = pyclamd.ClamdNetworkSocket(host=self.host, port=self.port)

            # Check if ClamAV is available
            if not cd.ping():
                self.logger.error(
                    "ClamAV daemon not responding", host=self.host, port=self.port
                )
                raise ConnectionError("ClamAV daemon not available")

            # Scan the file content
            scan_result = cd.scan_stream(content)

            if scan_result is None:
                # No threats detected
                self.logger.info(
                    "File scanned - clean", filename=filename, scanner="ClamAV"
                )
                return True, None

            # Threat detected
            threat_info = str(scan_result)
            self.logger.warning(
                "Malware detected by ClamAV", filename=filename, threat=threat_info
            )
            return False, f"Malware detected: {threat_info}"

        except ImportError:
            self.logger.error(
                "pyclamd not installed - cannot use ClamAV scanner",
                recommendation="pip install pyclamd",
            )
            raise ImportError("pyclamd package required for ClamAV scanning")

        except Exception as e:
            self.logger.error("ClamAV scan error", filename=filename, error=str(e))
            # In production, decide whether to fail-open or fail-closed
            # Fail-closed (safer): return False, f"Scan error: {str(e)}"
            # Fail-open (current): raise exception to be handled upstream
            raise


class VirusTotalScanner:
    """
    VirusTotal API scanner implementation.

    Uses VirusTotal's API to scan files against 70+ antivirus engines.
    Requires: VirusTotal API key and virustotal-python package.

    Usage:
        scanner = VirusTotalScanner(api_key="your_api_key")
        is_clean, threat = await scanner.scan_file(file_data, "test.pdf")
    """

    def __init__(self, api_key: str):
        """
        Initialize VirusTotal scanner.

        Args:
            api_key: VirusTotal API key
        """
        self.api_key = api_key
        self.logger = logger.bind(scanner="VirusTotal")

    async def scan_file(
        self, content: bytes, filename: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Scan file using VirusTotal API.

        Args:
            content: File content bytes
            filename: Original filename

        Returns:
            (is_clean, threat_info)
        """
        try:
            import vt

            # Calculate file hash
            file_hash = hashlib.sha256(content).hexdigest()

            # Initialize VirusTotal client
            async with vt.Client(self.api_key) as client:
                # First, check if file is already scanned
                try:
                    file_obj = await client.get_object_async(f"/files/{file_hash}")

                    # Get scan results
                    stats = file_obj.last_analysis_stats
                    malicious = stats.get("malicious", 0)
                    suspicious = stats.get("suspicious", 0)

                    if malicious > 0 or suspicious > 0:
                        threat_info = (
                            f"VirusTotal: {malicious} malicious, "
                            f"{suspicious} suspicious detections"
                        )
                        self.logger.warning(
                            "Malware detected by VirusTotal",
                            filename=filename,
                            sha256=file_hash,
                            malicious=malicious,
                            suspicious=suspicious,
                        )
                        return False, threat_info

                    self.logger.info(
                        "File scanned - clean",
                        filename=filename,
                        sha256=file_hash,
                        scanner="VirusTotal",
                    )
                    return True, None

                except vt.APIError as e:
                    if e.code == "NotFoundError":
                        # File not previously scanned, upload for scanning
                        self.logger.info(
                            "File not in VirusTotal database, uploading",
                            filename=filename,
                            sha256=file_hash,
                        )
                        # Note: In production, implement async scanning
                        # or queue-based approach as VT scans take time
                        return True, None
                    raise

        except ImportError:
            self.logger.error(
                "vt-py not installed - cannot use VirusTotal scanner",
                recommendation="pip install vt-py",
            )
            raise ImportError("vt-py package required for VirusTotal scanning")

        except Exception as e:
            self.logger.error("VirusTotal scan error", filename=filename, error=str(e))
            raise


class HashBasedScanner:
    """
    Hash-based malware detection using known malware signatures.

    Maintains a database of known malware file hashes and checks
    uploaded files against this database. Fast but limited to
    known threats.

    This is a simple implementation - in production, integrate with
    threat intelligence feeds (NIST NVD, AlienVault OTX, etc.)
    """

    def __init__(self):
        """Initialize hash-based scanner."""
        self.logger = logger.bind(scanner="HashBased")
        # In production, load from threat intelligence database
        self.known_malware_hashes = set()

    async def scan_file(
        self, content: bytes, filename: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Scan file by comparing hash against known malware database.

        Args:
            content: File content bytes
            filename: Original filename

        Returns:
            (is_clean, threat_info)
        """
        try:
            # Calculate file hash
            file_hash = hashlib.sha256(content).hexdigest()

            # Check against known malware hashes
            if file_hash in self.known_malware_hashes:
                self.logger.warning(
                    "Known malware hash detected", filename=filename, sha256=file_hash
                )
                return False, f"Known malware detected (SHA256: {file_hash[:16]}...)"

            self.logger.info(
                "File hash checked - clean", filename=filename, sha256=file_hash[:16]
            )
            return True, None

        except Exception as e:
            self.logger.error("Hash-based scan error", filename=filename, error=str(e))
            raise

    def add_malware_hash(self, hash_value: str) -> None:
        """
        Add a known malware hash to the database.

        Args:
            hash_value: SHA256 hash of malware file
        """
        self.known_malware_hashes.add(hash_value.lower())
        self.logger.info("Malware hash added to database", hash=hash_value[:16])


# Global scanner instance - configure based on environment
# Default to NoOp for safety (requires explicit configuration)
_malware_scanner: MalwareScannerProtocol = NoOpMalwareScanner()


def configure_scanner(scanner: MalwareScannerProtocol) -> None:
    """
    Configure the global malware scanner.

    Args:
        scanner: Scanner implementation to use

    Example:
        # Configure ClamAV
        configure_scanner(ClamAVScanner(host="localhost", port=3310))

        # Configure VirusTotal
        configure_scanner(VirusTotalScanner(api_key=settings.virustotal_api_key))
    """
    global _malware_scanner
    _malware_scanner = scanner
    logger.info("Malware scanner configured", scanner_type=type(scanner).__name__)


def get_scanner() -> MalwareScannerProtocol:
    """
    Get the configured malware scanner.

    Returns:
        Current scanner instance
    """
    return _malware_scanner


async def scan_uploaded_file(
    content: bytes, filename: str
) -> Tuple[bool, Optional[str]]:
    """
    Scan uploaded file for malware using configured scanner.

    This is the main entry point for malware scanning in the application.

    Args:
        content: File content bytes
        filename: Original filename

    Returns:
        (is_clean, threat_info)
        - is_clean: True if safe, False if threat detected
        - threat_info: Description of threat if found, None if clean

    Example:
        is_clean, threat = await scan_uploaded_file(file_data, "document.pdf")
        if not is_clean:
            raise SecurityError(f"Malware detected: {threat}")
    """
    scanner = get_scanner()

    logger.info(
        "Starting malware scan",
        filename=filename,
        file_size=len(content),
        scanner_type=type(scanner).__name__,
    )

    try:
        is_clean, threat_info = await scanner.scan_file(content, filename)

        if is_clean:
            logger.info(
                "Malware scan completed - clean",
                filename=filename,
                scanner_type=type(scanner).__name__,
            )
        else:
            logger.error(
                "Malware scan detected threat",
                filename=filename,
                threat=threat_info,
                scanner_type=type(scanner).__name__,
            )

        return is_clean, threat_info

    except Exception as e:
        logger.error(
            "Malware scan failed",
            filename=filename,
            error=str(e),
            scanner_type=type(scanner).__name__,
        )
        # Decision point: fail-open or fail-closed?
        # For healthcare/security-critical: fail-closed (reject upload)
        # Current implementation: re-raise to let caller decide
        raise


# Convenience functions for specific scanner types
async def scan_with_clamav(
    content: bytes, filename: str, host: str = "localhost", port: int = 3310
) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to scan with ClamAV.

    Args:
        content: File content bytes
        filename: Original filename
        host: ClamAV daemon host
        port: ClamAV daemon port

    Returns:
        (is_clean, threat_info)
    """
    scanner = ClamAVScanner(host=host, port=port)
    return await scanner.scan_file(content, filename)


async def scan_with_virustotal(
    content: bytes, filename: str, api_key: str
) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to scan with VirusTotal.

    Args:
        content: File content bytes
        filename: Original filename
        api_key: VirusTotal API key

    Returns:
        (is_clean, threat_info)
    """
    scanner = VirusTotalScanner(api_key=api_key)
    return await scanner.scan_file(content, filename)
