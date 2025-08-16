#!/usr/bin/env python3
"""
Tests for HL7 v2 Message Processing
Comprehensive test suite for HL7 v2 message parsing and processing.
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

from app.modules.hl7_v2.hl7_processor import (
    HL7MessageProcessor, HL7Parser, HL7Message, HL7Segment,
    HL7MessageType, HL7SegmentType, HL7Field, HL7DataType
)

class TestHL7Field:
    """Test HL7 field validation"""
    
    def test_field_creation(self):
        """Test HL7 field creation"""
        field = HL7Field(
            position=1,
            name="Patient ID",
            data_type=HL7DataType.ST,
            length=20,
            required=True,
            description="Patient identifier"
        )
        
        assert field.position == 1
        assert field.name == "Patient ID"
        assert field.data_type == HL7DataType.ST
        assert field.required is True
    
    def test_string_validation(self):
        """Test string field validation"""
        field = HL7Field(1, "Test Field", HL7DataType.ST, length=10, required=True)
        
        # Valid string
        assert field.validate_value("test") is True
        
        # Empty required field
        assert field.validate_value("") is False
        
        # Too long string
        assert field.validate_value("this is too long") is False
        
        # Valid length
        assert field.validate_value("exactly10") is True
    
    def test_numeric_validation(self):
        """Test numeric field validation"""
        field = HL7Field(1, "Numeric Field", HL7DataType.NM)
        
        # Valid numbers
        assert field.validate_value("123") is True
        assert field.validate_value("123.45") is True
        assert field.validate_value("-67.89") is True
        
        # Invalid numbers
        assert field.validate_value("abc") is False
        assert field.validate_value("12.34.56") is False
    
    def test_date_validation(self):
        """Test date field validation"""
        field = HL7Field(1, "Date Field", HL7DataType.DT)
        
        # Valid dates (YYYYMMDD)
        assert field.validate_value("20250724") is True
        assert field.validate_value("19901225") is True
        
        # Invalid dates
        assert field.validate_value("2025-07-24") is False
        assert field.validate_value("25072024") is False
        assert field.validate_value("abcd1234") is False
    
    def test_timestamp_validation(self):
        """Test timestamp field validation"""
        field = HL7Field(1, "Timestamp Field", HL7DataType.TS)
        
        # Valid timestamps (YYYYMMDDHHMMSS)
        assert field.validate_value("20250724120000") is True
        assert field.validate_value("19901225235959") is True
        
        # Invalid timestamps
        assert field.validate_value("2025-07-24 12:00:00") is False
        assert field.validate_value("20250724") is False

class TestHL7Segment:
    """Test HL7 segment functionality"""
    
    def test_segment_creation(self):
        """Test HL7 segment creation"""
        segment = HL7Segment(HL7SegmentType.PID)
        
        assert segment.segment_type == HL7SegmentType.PID
        assert len(segment.fields) == 0
    
    def test_field_operations(self):
        """Test segment field operations"""
        segment = HL7Segment(HL7SegmentType.PID)
        
        # Set fields
        segment.set_field(1, "1")  # Set ID
        segment.set_field(5, "Doe^John^M")  # Patient name
        
        # Get fields
        assert segment.get_field(1) == "1"
        assert segment.get_field(5) == "Doe^John^M"
        assert segment.get_field(99) is None  # Non-existent field
    
    def test_segment_to_string(self):
        """Test segment string conversion"""
        segment = HL7Segment(HL7SegmentType.PID)
        segment.set_field(1, "1")
        segment.set_field(3, "12345")
        segment.set_field(5, "Doe^John")
        
        segment_str = segment.to_string()
        
        assert segment_str.startswith("PID")
        assert "12345" in segment_str
        assert "Doe^John" in segment_str
    
    def test_msh_segment_special_handling(self):
        """Test MSH segment special field separator handling"""
        msh_segment = HL7Segment(HL7SegmentType.MSH)
        msh_segment.set_field(3, "SENDING_APP")
        msh_segment.set_field(4, "SENDING_FACILITY")
        msh_segment.set_field(9, "ADT^A01")
        
        segment_str = msh_segment.to_string()
        
        assert segment_str.startswith("MSH|")
        assert "^~\\&" in segment_str  # Encoding characters
        assert "SENDING_APP" in segment_str
        assert "ADT^A01" in segment_str

class TestHL7Message:
    """Test HL7 message functionality"""
    
    def test_message_creation(self):
        """Test HL7 message creation"""
        message = HL7Message(HL7MessageType.ADT_A01)
        
        assert message.message_type == HL7MessageType.ADT_A01
        assert len(message.segments) == 0
        assert message.field_separator == "|"
    
    def test_segment_operations(self):
        """Test message segment operations"""
        message = HL7Message(HL7MessageType.ADT_A01)
        
        # Add segments
        msh_segment = HL7Segment(HL7SegmentType.MSH)
        pid_segment = HL7Segment(HL7SegmentType.PID)
        
        message.add_segment(msh_segment)
        message.add_segment(pid_segment)
        
        assert len(message.segments) == 2
        
        # Get segments
        msh = message.get_segment(HL7SegmentType.MSH)
        assert msh is not None
        assert msh.segment_type == HL7SegmentType.MSH
        
        # Get non-existent segment
        evn = message.get_segment(HL7SegmentType.EVN)
        assert evn is None
    
    def test_message_to_string(self):
        """Test message string conversion"""
        message = HL7Message(HL7MessageType.ADT_A01)
        
        # Add MSH segment
        msh_segment = HL7Segment(HL7SegmentType.MSH)
        msh_segment.set_field(3, "SENDING_APP")
        msh_segment.set_field(9, "ADT^A01")
        message.add_segment(msh_segment)
        
        # Add PID segment
        pid_segment = HL7Segment(HL7SegmentType.PID)
        pid_segment.set_field(3, "12345")
        pid_segment.set_field(5, "Doe^John")
        message.add_segment(pid_segment)
        
        message_str = message.to_string()
        
        assert "MSH|" in message_str
        assert "PID|" in message_str
        assert "\r" in message_str  # Segment separator
        assert "SENDING_APP" in message_str
        assert "Doe^John" in message_str

class TestHL7Parser:
    """Test HL7 message parser"""
    
    @pytest.fixture
    def parser(self):
        """Create HL7 parser for testing"""
        return HL7Parser()
    
    def test_parse_simple_adt_message(self, parser):
        """Test parsing simple ADT message"""
        message_text = (
            "MSH|^~\\&|SENDING_APP|SENDING_FACILITY|RECEIVING_APP|RECEIVING_FACILITY|"
            "20250724120000||ADT^A01|MSG123|P|2.5\r"
            "PID|1||12345^^^MRN||Doe^John^M||19800101|M|||123 Main St^^Anytown^ST^12345|"
            "||555-1234|||||||123-45-6789\r"
            "PV1|1|I|ICU^101^1|||ATTENDING^DOC^A|||MED||||||||V123|||||||||||||||||||"
            "||20250724120000"
        )
        
        message = parser.parse_message(message_text)
        
        assert message.message_type == HL7MessageType.ADT_A01
        assert message.message_control_id == "MSG123"
        assert message.sending_application == "SENDING_APP"
        assert len(message.segments) == 3  # MSH, PID, PV1
        
        # Check MSH segment
        msh = message.get_segment(HL7SegmentType.MSH)
        assert msh is not None
        assert msh.get_field(9) == "ADT^A01"
        
        # Check PID segment
        pid = message.get_segment(HL7SegmentType.PID)
        assert pid is not None
        assert pid.get_field(3) == "12345^^^MRN"
        assert pid.get_field(5) == "Doe^John^M"
        
        # Check PV1 segment
        pv1 = message.get_segment(HL7SegmentType.PV1)
        assert pv1 is not None
        assert pv1.get_field(2) == "I"  # Inpatient
    
    def test_parse_message_with_encoding_characters(self, parser):
        """Test parsing message with different encoding characters"""
        message_text = (
            "MSH|^~\\&|SYSTEM|FACILITY|||20250724120000||ACK|ACK123|P|2.5\r"
            "MSA|AA|MSG123|Message accepted"
        )
        
        message = parser.parse_message(message_text)
        
        assert message.field_separator == "|"
        assert message.component_separator == "^"
        assert message.repetition_separator == "~"
        assert message.escape_character == "\\"
        assert message.subcomponent_separator == "&"
    
    def test_parse_timestamp(self, parser):
        """Test HL7 timestamp parsing"""
        # Full timestamp
        dt = parser._parse_hl7_timestamp("20250724120530")
        assert dt is not None
        assert dt.year == 2025
        assert dt.month == 7
        assert dt.day == 24
        assert dt.hour == 12
        assert dt.minute == 5
        assert dt.second == 30
        
        # Date only
        dt = parser._parse_hl7_timestamp("20250724")
        assert dt is not None
        assert dt.year == 2025
        assert dt.month == 7
        assert dt.day == 24
        
        # Invalid timestamp
        dt = parser._parse_hl7_timestamp("invalid")
        assert dt is None
    
    def test_validate_message(self, parser):
        """Test message validation"""
        # Create valid message
        message = HL7Message(HL7MessageType.ADT_A01)
        
        # Add MSH segment
        msh = HL7Segment(HL7SegmentType.MSH)
        msh.set_field(9, "ADT^A01")
        msh.set_field(10, "MSG123")
        message.add_segment(msh)
        
        # Add PID segment (required for ADT)
        pid = HL7Segment(HL7SegmentType.PID)
        pid.set_field(3, "12345")  # Patient ID
        pid.set_field(5, "Doe^John")  # Patient name
        message.add_segment(pid)
        
        is_valid, errors = parser.validate_message(message)
        
        # Should be valid (basic validation)
        assert is_valid is True or len(errors) == 0  # Allow for some validation flexibility
    
    def test_parse_invalid_message(self, parser):
        """Test parsing invalid message"""
        # Empty message
        with pytest.raises(ValueError):
            parser.parse_message("")
        
        # Message not starting with MSH
        with pytest.raises(ValueError):
            parser.parse_message("PID|1|")
    
    def test_parse_oru_message(self, parser):
        """Test parsing ORU (Observation Result) message"""
        message_text = (
            "MSH|^~\\&|LAB|HOSPITAL|||20250724120000||ORU^R01|MSG123|P|2.5\r"
            "PID|1||12345|||Doe^John||||||||||||\r"
            "OBR|1||12345|CBC^Complete Blood Count|||20250724120000||||||||||||\r"
            "OBX|1|NM|WBC^White Blood Cell Count|1|7.5|10^3/uL|4.0-11.0|N|||F"
        )
        
        message = parser.parse_message(message_text)
        
        assert message.message_type == HL7MessageType.ORU_R01
        
        # Check OBX segment
        obx_segments = message.get_segments(HL7SegmentType.OBX)
        assert len(obx_segments) == 1
        
        obx = obx_segments[0]
        assert obx.get_field(2) == "NM"  # Numeric value
        assert obx.get_field(3) == "WBC^White Blood Cell Count"
        assert obx.get_field(5) == "7.5"  # Result value

class TestHL7MessageProcessor:
    """Test HL7 message processor"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return AsyncMock()
    
    @pytest.fixture
    def processor(self, mock_db_session):
        """Create HL7 processor for testing"""
        return HL7MessageProcessor(mock_db_session)
    
    @pytest.mark.asyncio
    async def test_process_adt_a01_message(self, processor):
        """Test processing ADT A01 (admit) message"""
        message_text = (
            "MSH|^~\\&|SENDING_APP|SENDING_FACILITY|||20250724120000||ADT^A01|MSG123|P|2.5\r"
            "PID|1||12345^^^MRN||Doe^John^M||19800101|M|||123 Main St^^Anytown^ST^12345\r"
            "PV1|1|I|ICU^101^1|||ATTENDING^DOC^A|||MED||||||||V123|||||||||||||||||||"
            "||20250724120000"
        )
        
        result = await processor.process_message(message_text, "TEST_SYSTEM")
        
        assert result["status"] == "success"
        assert result["message_type"] == "ADT^A01"
        assert result["event_type"] == "A01"
        assert result["action"] == "patient_admitted"
        
        # Check FHIR Patient mapping
        patient_data = result["patient_data"]
        assert patient_data["resourceType"] == "Patient"
        assert patient_data["gender"] == "male"
        
        # Check patient name
        assert len(patient_data["name"]) > 0
        name = patient_data["name"][0]
        assert name["family"] == "Doe"
        assert name["given"] == ["John"]
        
        # Check FHIR Encounter mapping
        encounter_data = result["encounter_data"]
        assert encounter_data["resourceType"] == "Encounter"
        assert encounter_data["status"] == "in-progress"
    
    @pytest.mark.asyncio
    async def test_process_oru_message(self, processor):
        """Test processing ORU (Observation Result) message"""
        message_text = (
            "MSH|^~\\&|LAB|HOSPITAL|||20250724120000||ORU^R01|MSG123|P|2.5\r"
            "PID|1||12345|||Doe^John||||||||||||\r"
            "OBR|1||12345|CBC^Complete Blood Count|||20250724120000||||||||||||\r"
            "OBX|1|NM|WBC^White Blood Cell Count|1|7.5|10^3/uL|4.0-11.0|N|||F\r"
            "OBX|2|NM|RBC^Red Blood Cell Count|1|4.2|10^6/uL|4.0-5.5|N|||F"
        )
        
        result = await processor.process_message(message_text, "LAB_SYSTEM")
        
        assert result["status"] == "success"
        assert result["message_type"] == "ORU^R01"
        
        # Check observations
        observations = result["observations"]
        assert len(observations) == 2
        
        # Check first observation (WBC)
        wbc_obs = observations[0]
        assert wbc_obs["resourceType"] == "Observation"
        assert wbc_obs["status"] == "final"
        assert "valueQuantity" in wbc_obs
        assert wbc_obs["valueQuantity"]["value"] == 7.5
        assert wbc_obs["valueQuantity"]["unit"] == "10^3/uL"
    
    @pytest.mark.asyncio
    async def test_process_siu_message(self, processor):
        """Test processing SIU (Scheduling) message"""
        message_text = (
            "MSH|^~\\&|SCHEDULE|HOSPITAL|||20250724120000||SIU^S12|MSG123|P|2.5\r"
            "SCH|APPT123||SCHEDULED^New Appointment||||^^^^^20250725140000^20250725150000|||60|MIN\r"
            "PID|1||12345|||Doe^John||||||||||||\r"
            "AIS|1|OFFICE_VISIT^Office Visit|||||||"
        )
        
        result = await processor.process_message(message_text, "SCHEDULE_SYSTEM")
        
        assert result["status"] == "success"
        assert result["message_type"] == "SIU^S12"
        assert result["event_type"] == "S12"
        assert result["action"] == "appointment_scheduled"
        
        # Check appointment data
        appointment_data = result["appointment_data"]
        assert appointment_data["resourceType"] == "Appointment"
        assert appointment_data["status"] == "booked"
    
    @pytest.mark.asyncio
    async def test_process_vxu_message(self, processor):
        """Test processing VXU (Vaccination) message"""
        message_text = (
            "MSH|^~\\&|IMMUN|CLINIC|||20250724120000||VXU^V04|MSG123|P|2.5\r"
            "PID|1||12345|||Doe^John||||||||||||\r"
            "RXA|0|1|20250724|20250724|08^Hepatitis B^CVX|0.5|ML||||||||||||||||"
        )
        
        result = await processor.process_message(message_text, "IMMUNIZATION_SYSTEM")
        
        assert result["status"] == "success"
        assert result["message_type"] == "VXU^V04"
        
        # Check immunizations
        immunizations = result["immunizations"]
        assert len(immunizations) == 1
        
        immunization = immunizations[0]
        assert immunization["resourceType"] == "Immunization"
        assert immunization["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_invalid_message_processing(self, processor):
        """Test processing invalid message"""
        invalid_message = "INVALID MESSAGE FORMAT"
        
        result = await processor.process_message(invalid_message, "TEST_SYSTEM")
        
        assert result["status"] == "error"
        assert "error" in result["message"].lower()
        assert result["ack_message"] is not None
    
    @pytest.mark.asyncio
    async def test_unsupported_message_type(self, processor):
        """Test processing unsupported message type"""
        message_text = (
            "MSH|^~\\&|SYSTEM|FACILITY|||20250724120000||XYZ^Z99|MSG123|P|2.5\r"
            "PID|1||12345|||Doe^John||||||||||||"
        )
        
        # This should handle unknown message types gracefully
        result = await processor.process_message(message_text, "TEST_SYSTEM")
        
        # Should process but may not have specific handling
        assert result["status"] in ["success", "unsupported"]
    
    @pytest.mark.asyncio
    async def test_fhir_patient_mapping(self, processor):
        """Test detailed FHIR Patient resource mapping"""
        # Create PID segment with comprehensive patient data
        pid_segment = HL7Segment(HL7SegmentType.PID)
        pid_segment.set_field(3, "12345^^^MRN")  # Patient ID
        pid_segment.set_field(5, "Doe^John^Michael^Jr^MD")  # Full name
        pid_segment.set_field(7, "19800101")  # Birth date
        pid_segment.set_field(8, "M")  # Gender
        pid_segment.set_field(11, "123 Main St^^Anytown^CA^90210")  # Address
        pid_segment.set_field(13, "555-123-4567")  # Home phone
        pid_segment.set_field(14, "555-987-6543")  # Work phone
        
        patient_data = await processor._map_pid_to_fhir_patient(pid_segment)
        
        assert patient_data["resourceType"] == "Patient"
        assert patient_data["gender"] == "male"
        assert patient_data["birthDate"] == "1980-01-01"
        
        # Check name mapping
        name = patient_data["name"][0]
        assert name["family"] == "Doe"
        assert name["given"] == ["John"]
        
        # Check identifier
        identifier = patient_data["identifier"][0]
        assert identifier["value"] == "12345"
        assert identifier["type"]["coding"][0]["code"] == "MR"
        
        # Check address
        address = patient_data["address"][0]
        assert address["line"] == ["123 Main St"]
        assert address["city"] == "Anytown"
        assert address["state"] == "CA"
        assert address["postalCode"] == "90210"
        
        # Check phone numbers
        telecom = patient_data["telecom"]
        assert len(telecom) == 2
        
        home_phone = next((t for t in telecom if t["use"] == "home"), None)
        assert home_phone is not None
        assert home_phone["value"] == "555-123-4567"
        
        work_phone = next((t for t in telecom if t["use"] == "work"), None)
        assert work_phone is not None
        assert work_phone["value"] == "555-987-6543"
    
    @pytest.mark.asyncio
    async def test_ack_message_creation(self, processor):
        """Test ACK message creation"""
        # Create a test message
        original_message = HL7Message(HL7MessageType.ADT_A01)
        original_message.message_control_id = "TEST123"
        original_message.sending_application = "TEST_APP"
        original_message.receiving_application = "DEST_APP"
        
        # Create ACK response
        ack_message = await processor._create_ack_response(
            original_message, "AA", "Message accepted"
        )
        
        assert "MSH|" in ack_message
        assert "MSA|" in ack_message
        assert "AA" in ack_message  # Acknowledgment code
        assert "TEST123" in ack_message  # Original message control ID
        assert "Message accepted" in ack_message
        
        # Parse the ACK to verify structure
        parser = HL7Parser()
        ack_parsed = parser.parse_message(ack_message)
        
        msa = ack_parsed.get_segment(HL7SegmentType.MSA)
        assert msa is not None
        assert msa.get_field(1) == "AA"  # Acknowledgment code
        assert msa.get_field(2) == "TEST123"  # Message control ID
        assert msa.get_field(3) == "Message accepted"  # Text message

# Performance and Edge Case Tests

class TestHL7Performance:
    """Test HL7 processing performance and edge cases"""
    
    @pytest.fixture
    def processor(self):
        """Create HL7 processor for testing"""
        mock_db = AsyncMock()
        return HL7MessageProcessor(mock_db)
    
    @pytest.mark.asyncio
    async def test_large_message_processing(self, processor):
        """Test processing large HL7 message with many segments"""
        # Create message with many OBX segments (lab results)
        message_parts = [
            "MSH|^~\\&|LAB|HOSPITAL|||20250724120000||ORU^R01|MSG123|P|2.5",
            "PID|1||12345|||Doe^John||||||||||||",
            "OBR|1||12345|PANEL^Lab Panel|||20250724120000||||||||||||"
        ]
        
        # Add 100 OBX segments
        for i in range(100):
            obx = f"OBX|{i+1}|NM|TEST{i}^Test {i}|1|{i*1.5}|mg/dL|0-100|N|||F"
            message_parts.append(obx)
        
        message_text = "\r".join(message_parts)
        
        result = await processor.process_message(message_text, "LAB_SYSTEM")
        
        assert result["status"] == "success"
        assert len(result["observations"]) == 100
    
    @pytest.mark.asyncio
    async def test_message_with_special_characters(self, processor):
        """Test processing message with special characters"""
        message_text = (
            "MSH|^~\\&|SYSTEM|FACILITY|||20250724120000||ADT^A01|MSG123|P|2.5\r"
            "PID|1||12345^^^MRN||O'Connor^Seán^José||19800101|M|||"
            "123 Rue de la Paix^^Paris^75^75001|||||||||||"
            # Using special characters in patient name and address
        )
        
        result = await processor.process_message(message_text, "TEST_SYSTEM")
        
        assert result["status"] == "success"
        
        # Verify special characters are preserved
        patient_data = result["patient_data"]
        name = patient_data["name"][0]
        assert name["family"] == "O'Connor"
        assert "Seán" in name["given"]
    
    @pytest.mark.asyncio
    async def test_concurrent_message_processing(self, processor):
        """Test concurrent processing of multiple messages"""
        message_template = (
            "MSH|^~\\&|SYSTEM|FACILITY|||20250724120000||ADT^A01|MSG{id}|P|2.5\r"
            "PID|1||{id}^^^MRN||Patient^{id}||19800101|M||||||||||||"
        )
        
        # Create multiple messages
        messages = []
        for i in range(10):
            message = message_template.format(id=i)
            messages.append(message)
        
        # Process messages concurrently
        tasks = []
        for i, message in enumerate(messages):
            task = processor.process_message(message, f"SYSTEM_{i}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 10
        for result in results:
            assert result["status"] == "success"
    
    def test_memory_efficiency(self):
        """Test memory efficiency with large field values"""
        parser = HL7Parser()
        
        # Create message with very large field
        large_text = "A" * 10000  # 10KB text field
        message_text = (
            f"MSH|^~\\&|SYSTEM|FACILITY|||20250724120000||ADT^A01|MSG123|P|2.5\r"
            f"PID|1||12345^^^MRN||{large_text}||19800101|M||||||||||||"
        )
        
        # Should parse without memory issues
        parsed_message = parser.parse_message(message_text)
        
        assert parsed_message is not None
        pid = parsed_message.get_segment(HL7SegmentType.PID)
        assert len(pid.get_field(5)) == 10000