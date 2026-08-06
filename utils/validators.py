# utils/validators.py
import re

def validate_email(email):
    """Validate email format"""
    if not email:
        return True  # Email is optional
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number (10+ digits)"""
    if not phone:
        return True  # Phone is optional
    return phone.isdigit() and len(phone) >= 10

def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    return True, "Valid password"

def validate_student_id(student_id):
    """Validate student ID format"""
    if not student_id:
        return False, "Student ID is required"
    if len(student_id) < 3:
        return False, "Student ID must be at least 3 characters"
    return True, "Valid student ID"