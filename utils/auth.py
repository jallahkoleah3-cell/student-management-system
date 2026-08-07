import streamlit as st
from .firebase_db import db
from datetime import datetime
from firebase_admin import auth

def login_user(email, password):
    """
    Authenticate user using Firebase
    Returns: (user_data, error_message)
    """
    try:
        # First, check if user exists in Firestore
        users_ref = db.db.collection('users').where('email', '==', email).stream()
        
        user_data = None
        for user_doc in users_ref:
            user_data = user_doc.to_dict()
            user_data['uid'] = user_doc.id
            break
        
        if not user_data:
            return None, "User not found!"
        
        # If user is a student, get their student_id from the students collection
        if user_data.get('role') == 'Student':
            # Search for the student by email in the students collection
            students = db.get_all_students()
            found_student_id = None
            for s in students:
                if s.get('email') == email:
                    found_student_id = s.get('student_id') or s.get('uid')
                    break
            
            if found_student_id:
                user_data['student_id'] = found_student_id
                print(f"✅ Found student_id: {found_student_id}")
            else:
                # Try to find by uid
                for s in students:
                    if s.get('uid') == user_data.get('uid'):
                        found_student_id = s.get('student_id')
                        break
                
                if found_student_id:
                    user_data['student_id'] = found_student_id
                    print(f"✅ Found student_id by uid: {found_student_id}")
                else:
                    # If still not found, use uid as fallback
                    user_data['student_id'] = user_data.get('uid')
                    print(f"⚠️ Using uid as student_id fallback: {user_data['student_id']}")
        
        # Check if user exists in Firebase Auth
        try:
            user = auth.get_user_by_email(email)
            print(f"✅ User found in Firebase Auth: {user.uid}")
        except Exception as e:
            print(f"❌ User not found in Firebase Auth: {e}")
            return None, "User account not fully set up. Contact admin."
        
        # Log the login
        log_user_activity(user_data['uid'], "Login", "User logged in successfully")
        
        return user_data, None
        
    except Exception as e:
        return None, f"Login error: {str(e)}"

def log_user_activity(uid, action, details=""):
    """Log user activity"""
    try:
        activity_data = {
            'user_id': uid,
            'action': action,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        db.db.collection('activity_logs').add(activity_data)
    except Exception as e:
        print(f"Error logging activity: {e}")

def get_current_user():
    """Get the current logged-in user from session state"""
    return st.session_state.get('user', None)

def get_current_role():
    """Get the current user's role"""
    user = get_current_user()
    return user.get('role') if user else None

def is_authenticated():
    """Check if user is logged in"""
    return 'user' in st.session_state and st.session_state.user