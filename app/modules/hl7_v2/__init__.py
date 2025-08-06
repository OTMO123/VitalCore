#!/usr/bin/env python3
"""
HL7 v2 Processing Module
Legacy healthcare system integration with HL7 v2.x message formats.

This module provides comprehensive HL7 v2 message processing capabilities including:
- Message parsing and validation
- FHIR R4 resource mapping
- ACK/NAK response generation
- Support for major HL7 message types
- PHI-compliant audit logging

Key Components:
- hl7_processor.py: Core HL7 parsing, validation, and processing engine
- router.py: REST API endpoints for HL7 message handling

Supported Message Types:
- ADT (Admission, Discharge, Transfer): A01, A02, A03, A04, A08, A11, A12
- ORM (Order Management): O01, O02
- ORU (Observation Results): R01, R03
- SIU (Scheduling Information): S12, S13, S14, S15, S17, S26
- VXU (Vaccination Updates): V04
- MDM (Medical Document Management): T02, T04, T06, T08, T11

Standards Compliance:
- HL7 v2.x message format specification
- FHIR R4 resource mapping
- HIPAA PHI handling requirements
- Healthcare interoperability standards
"""

from .hl7_processor import (
    HL7MessageProcessor,
    HL7Parser,
    HL7Message,
    HL7Segment,
    HL7MessageType,
    HL7SegmentType
)
from .router import router

__all__ = [
    "HL7MessageProcessor",
    "HL7Parser",
    "HL7Message", 
    "HL7Segment",
    "HL7MessageType",
    "HL7SegmentType",
    "router"
]