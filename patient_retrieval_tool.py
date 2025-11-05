"""
Patient Data Retrieval Tool
Handles database interaction for patient discharge reports
"""
import json
from typing import Optional, Dict, List
from pathlib import Path

from config import PATIENTS_JSON
from logger_system import get_logger


class PatientRetrievalTool:
    """Tool for retrieving patient discharge reports from database"""
    
    def __init__(self, patients_file: Path = PATIENTS_JSON):
        self.patients_file = patients_file
        self.logger = get_logger()
        self.patients_data = self._load_patients()
        self.logger.log_system_event(
            f"Patient database loaded with {len(self.patients_data)} records"
        )
    
    def _load_patients(self) -> List[Dict]:
        """Load patient data from JSON file"""
        try:
            with open(self.patients_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.log_error("PatientDataLoad", str(e))
            return []
    
    def get_patient_by_name(self, patient_name: str) -> Optional[Dict]:
        """
        Retrieve patient discharge report by name
        
        Args:
            patient_name: Name of the patient to search for
            
        Returns:
            Patient discharge report dict or None if not found
        """
        self.logger.log_tool_call(
            "get_patient_by_name",
            {"patient_name": patient_name},
            None
        )
        
        # Normalize name for case-insensitive search
        search_name = patient_name.strip().lower()
        
        # Find matching patients
        matches = [
            patient for patient in self.patients_data
            if patient.get("patient_name", "").lower() == search_name
        ]
        
        if not matches:
            self.logger.log_tool_call(
                "get_patient_by_name",
                {"patient_name": patient_name},
                {"status": "not_found"}
            )
            return None
        
        if len(matches) > 1:
            self.logger.log_tool_call(
                "get_patient_by_name",
                {"patient_name": patient_name},
                {"status": "multiple_matches", "count": len(matches)}
            )
            # Return first match with warning
            return {
                "warning": f"Multiple patients found with name '{patient_name}'",
                "patient": matches[0]
            }
        
        self.logger.log_tool_call(
            "get_patient_by_name",
            {"patient_name": patient_name},
            {"status": "success", "patient_found": True}
        )
        
        return matches[0]
    
    def search_patients(self, query: str) -> List[Dict]:
        """
        Search for patients by partial name match
        
        Args:
            query: Search query string
            
        Returns:
            List of matching patient records
        """
        query = query.strip().lower()
        matches = [
            patient for patient in self.patients_data
            if query in patient.get("patient_name", "").lower()
        ]
        
        self.logger.log_tool_call(
            "search_patients",
            {"query": query},
            {"matches_found": len(matches)}
        )
        
        return matches
    
    def get_all_patients(self) -> List[Dict]:
        """Get all patient records"""
        return self.patients_data
    
    def format_patient_info(self, patient_data: Dict) -> str:
        """
        Format patient information for display
        
        Args:
            patient_data: Patient discharge report dictionary
            
        Returns:
            Formatted string representation of patient data
        """
        if not patient_data:
            return "No patient data available."
        
        # Handle multiple matches warning
        if "warning" in patient_data:
            warning = patient_data["warning"]
            patient_data = patient_data["patient"]
            formatted = f"⚠️ {warning}\n\n"
        else:
            formatted = ""
        
        formatted += f"""
📋 **Patient Discharge Report**

**Name:** {patient_data.get('patient_name', 'N/A')}
**Discharge Date:** {patient_data.get('discharge_date', 'N/A')}
**Primary Diagnosis:** {patient_data.get('primary_diagnosis', 'N/A')}

**Medications:**
{self._format_list(patient_data.get('medications', []))}

**Dietary Restrictions:** {patient_data.get('dietary_restrictions', 'N/A')}

**Follow-up:** {patient_data.get('follow_up', 'N/A')}

**Warning Signs to Watch For:**
{patient_data.get('warning_signs', 'N/A')}

**Discharge Instructions:**
{patient_data.get('discharge_instructions', 'N/A')}
"""
        return formatted.strip()
    
    def _format_list(self, items: List[str]) -> str:
        """Format a list of items as bullet points"""
        if not items:
            return "• None specified"
        return "\n".join(f"• {item}" for item in items)
    
    def get_patient_summary(self, patient_name: str) -> str:
        """
        Get a concise summary of patient information
        
        Args:
            patient_name: Name of the patient
            
        Returns:
            Summary string
        """
        patient = self.get_patient_by_name(patient_name)
        
        if not patient:
            return f"❌ No discharge report found for patient '{patient_name}'."
        
        # Handle multiple matches
        if "warning" in patient:
            patient = patient["patient"]
        
        summary = f"""
Found discharge report for {patient.get('patient_name')} from {patient.get('discharge_date')}.
Diagnosis: {patient.get('primary_diagnosis')}
Medications: {len(patient.get('medications', []))} prescribed
Follow-up: {patient.get('follow_up')}
"""
        return summary.strip()


# Standalone functions for agent tool integration
def retrieve_patient(patient_name: str) -> str:
    """
    Retrieve patient information by name (for agent tool use)
    
    Args:
        patient_name: Name of the patient to retrieve
        
    Returns:
        Formatted patient information or error message
    """
    tool = PatientRetrievalTool()
    patient = tool.get_patient_by_name(patient_name)
    
    if not patient:
        return f"❌ No discharge report found for patient '{patient_name}'. Please verify the name spelling."
    
    return tool.format_patient_info(patient)


def search_patients_by_name(query: str) -> str:
    """
    Search for patients by partial name (for agent tool use)
    
    Args:
        query: Search query
        
    Returns:
        List of matching patient names
    """
    tool = PatientRetrievalTool()
    matches = tool.search_patients(query)
    
    if not matches:
        return f"No patients found matching '{query}'."
    
    names = [p.get("patient_name") for p in matches]
    return f"Found {len(names)} matching patient(s):\n" + "\n".join(f"• {name}" for name in names)


# Test the tool
if __name__ == "__main__":
    tool = PatientRetrievalTool()
    
    print("Testing Patient Retrieval Tool")
    print("=" * 60)
    
    # Test 1: Get patient by exact name
    print("\n1. Retrieving John Smith:")
    patient = tool.get_patient_by_name("John Smith")
    if patient:
        print(tool.format_patient_info(patient))
    
    # Test 2: Search patients
    print("\n2. Searching for patients with 'Smith':")
    results = tool.search_patients("Smith")
    print(f"Found {len(results)} matches")
    
    # Test 3: Case insensitive search
    print("\n3. Case insensitive search for 'john smith':")
    patient = tool.get_patient_by_name("john smith")
    if patient:
        print(tool.get_patient_summary("john smith"))
