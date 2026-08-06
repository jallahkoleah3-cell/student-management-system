import streamlit as st
from utils.firebase_db import db
from utils.validators import validate_email, validate_phone
import pandas as pd

def show(user):
    st.header("👨‍🎓 Student Management")
    
    tab1, tab2 = st.tabs(["➕ Add Student", "📋 All Students"])
    
    with tab1:
        with st.form("add_student_form"):
            col1, col2 = st.columns(2)
            with col1:
                student_id = st.text_input("Student ID*", help="Unique identifier")
                full_name = st.text_input("Full Name*")
                email = st.text_input("Email*", help="Will be used for login")
                password = st.text_input("Password", type="password", value="student123", 
                                        help="Default: student123")
            with col2:
                grade = st.selectbox("Grade", ['1','2','3','4','5','6','7','8','9','10','11','12'])
                section = st.text_input("Section", max_chars=5)
                phone = st.text_input("Phone")
                gender = st.selectbox("Gender", ['Male', 'Female', 'Other'])
            
            address = st.text_area("Address")
            parent_contact = st.text_input("Parent Contact")
            
            submitted = st.form_submit_button("➕ Add Student", use_container_width=True)
            
            if submitted:
                if not student_id or not full_name or not email:
                    st.error("⚠️ Student ID, Full Name, and Email are required!")
                elif not validate_email(email):
                    st.error("⚠️ Invalid email format!")
                elif phone and not validate_phone(phone):
                    st.error("⚠️ Phone must be at least 10 digits!")
                else:
                    student_data = {
                        'student_id': student_id,
                        'full_name': full_name,
                        'email': email,
                        'password': password,
                        'grade': grade,
                        'section': section,
                        'phone': phone,
                        'gender': gender,
                        'address': address,
                        'parent_contact': parent_contact,
                        'status': 'Active'
                    }
                    success, msg = db.add_student(student_data)
                    if success:
                        st.success(f"✅ {msg}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
    
    with tab2:
        students = db.get_all_students()
        if students:
            # Search and filter
            search = st.text_input("🔍 Search Students", placeholder="Search by name or ID")
            df = pd.DataFrame(students)
            
            if search:
                df = df[df['full_name'].str.contains(search, case=False) | 
                       df['student_id'].str.contains(search, case=False)]
            
            st.dataframe(df, use_container_width=True, height=400)
            
            # View/Edit/Delete
            selected = st.selectbox("Select Student to Manage", df['student_id'].tolist() if not df.empty else [])
            if selected:
                student = db.get_student(selected)
                if student:
                    with st.expander(f"✏️ Edit Student: {student.get('full_name', '')}"):
                        with st.form("edit_student_form"):
                            col1, col2 = st.columns(2)
                            with col1:
                                s_name = st.text_input("Full Name", student.get('full_name', ''))
                                s_grade = st.selectbox("Grade", ['1','2','3','4','5','6','7','8','9','10','11','12'],
                                                      index=['1','2','3','4','5','6','7','8','9','10','11','12'].index(student.get('grade', '1')) if student.get('grade') in ['1','2','3','4','5','6','7','8','9','10','11','12'] else 0)
                                s_section = st.text_input("Section", student.get('section', ''))
                            with col2:
                                s_phone = st.text_input("Phone", student.get('phone', ''))
                                s_gender = st.selectbox("Gender", ['Male', 'Female', 'Other'],
                                                      index=['Male', 'Female', 'Other'].index(student.get('gender', 'Male')) if student.get('gender') in ['Male', 'Female', 'Other'] else 0)
                                s_status = st.selectbox("Status", ['Active', 'Inactive', 'Graduated'],
                                                      index=['Active', 'Inactive', 'Graduated'].index(student.get('status', 'Active')) if student.get('status') in ['Active', 'Inactive', 'Graduated'] else 0)
                            
                            s_address = st.text_area("Address", student.get('address', ''))
                            s_parent = st.text_input("Parent Contact", student.get('parent_contact', ''))
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("💾 Update"):
                                    update_data = {
                                        'full_name': s_name,
                                        'grade': s_grade,
                                        'section': s_section,
                                        'phone': s_phone,
                                        'gender': s_gender,
                                        'status': s_status,
                                        'address': s_address,
                                        'parent_contact': s_parent
                                    }
                                    success, msg = db.update_student(selected, update_data)
                                    if success:
                                        st.success(f"✅ {msg}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {msg}")
                            with col2:
                                if st.form_submit_button("🗑️ Delete", type="secondary"):
                                    if st.checkbox("Confirm delete?"):
                                        success, msg = db.delete_student(selected)
                                        if success:
                                            st.warning(f"⚠️ {msg}")
                                            st.rerun()
                                        else:
                                            st.error(f"❌ {msg}")
        else:
            st.info("📭 No students added yet. Add your first student!")