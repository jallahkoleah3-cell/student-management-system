import streamlit as st
from utils.firebase_db import db
from utils.validators import validate_email, validate_phone

def show(user):
    st.header("👨‍🏫 Teacher Management")
    
    tab1, tab2 = st.tabs(["➕ Add Teacher", "📋 All Teachers"])
    
    with tab1:
        with st.form("add_teacher_form"):
            col1, col2 = st.columns(2)
            with col1:
                full_name = st.text_input("Full Name*")
                email = st.text_input("Email*", help="Will be used for login")
                password = st.text_input("Password", type="password", value="teacher123")
            with col2:
                phone = st.text_input("Phone")
                subjects = st.text_input("Subjects (comma separated)", help="e.g., Math, Science, English")
                class_assigned = st.text_input("Class Assigned")
            
            submitted = st.form_submit_button("➕ Add Teacher", use_container_width=True)
            
            if submitted:
                if not full_name or not email:
                    st.error("⚠️ Full Name and Email are required!")
                elif not validate_email(email):
                    st.error("⚠️ Invalid email format!")
                else:
                    subject_list = [s.strip() for s in subjects.split(',') if s.strip()]
                    success, msg = db.add_teacher(
                        email=email,
                        password=password,
                        full_name=full_name,
                        phone=phone,
                        subjects=subject_list,
                        class_assigned=class_assigned
                    )