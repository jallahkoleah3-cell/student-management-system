import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import json
from streamlit_cookies_controller import CookieController
import utils.pages.admin_roles as admin_roles

# Import Firebase and utilities
from utils.firebase_db import db
from utils.auth import login_user
from utils.validators import validate_email, validate_phone

# Import announcement pages
import utils.pages.admin_announcements as admin_announcements
import utils.pages.teacher_announcements as teacher_announcements
import utils.pages.student_announcements as student_announcements

import traceback
import sys

try:
    # ALL your existing imports go here...
    import pandas as pd
    from datetime import datetime, timedelta
    # ... etc ...
except Exception as e:
    st.error(f"❌ Import Error: {e}")
    st.code(traceback.format_exc())
    st.stop()

# ---------- STREAMLIT CLOUD SECRETS ----------
import os
import json

# Load secrets from Streamlit Cloud
if 'FIREBASE_CREDENTIALS' in os.environ:
    print("✅ Running on Streamlit Cloud - loading secrets from environment")
    # The Firebase credentials are already handled in firebase_db.py
else:
    print("🔍 Running locally - using .env file")

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Student Management System",
    page_icon="🏫",
    layout="wide"
)

# ---------- COOKIE CONTROLLER ----------
controller = CookieController()

# ---------- SHOW MESSAGES ----------
def show_messages():
    if st.session_state.message:
        if st.session_state.message_type == "success":
            st.success(st.session_state.message)
        elif st.session_state.message_type == "error":
            st.error(st.session_state.message)
        elif st.session_state.message_type == "warning":
            st.warning(st.session_state.message)
        elif st.session_state.message_type == "info":
            st.info(st.session_state.message)
        st.session_state.message = None
        st.session_state.message_type = None

# ---------- SESSION STATE ----------
def init_session():
    """Initialize session state with cookie persistence"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'role' not in st.session_state:
        st.session_state.role = None
    if 'message' not in st.session_state:
        st.session_state.message = None
    if 'message_type' not in st.session_state:
        st.session_state.message_type = None
    if 'session_initialized' not in st.session_state:
        st.session_state.session_initialized = False
    
    try:
        cookie_user = controller.get('user_data')
        if cookie_user and not st.session_state.logged_in:
            st.session_state.user = cookie_user
            st.session_state.logged_in = True
            st.session_state.role = cookie_user.get('role', 'Unknown')
            print(f"✅ Auto-login from cookie: {cookie_user.get('email', 'Unknown')}")
    except Exception as e:
        print(f"Cookie load error: {e}")

def save_session(user_data):
    st.session_state.user = user_data
    st.session_state.logged_in = True
    st.session_state.role = user_data.get('role', 'Unknown')
    
    try:
        cookie_data = {}
        for key, value in user_data.items():
            if hasattr(value, 'isoformat'):
                cookie_data[key] = value.isoformat()
            elif isinstance(value, dict):
                cookie_data[key] = str(value)
            elif isinstance(value, (int, float, str, bool)) or value is None:
                cookie_data[key] = value
            else:
                cookie_data[key] = str(value)
        
        expires_date = datetime.now() + timedelta(days=7)
        
        controller.set(
            'user_data',
            cookie_data,
            expires=expires_date
        )
        print(f"✅ Cookie saved successfully for: {user_data.get('email', 'Unknown')}")
        print(f"✅ Cookie expires: {expires_date}")
        
    except Exception as e:
        print(f"❌ Cookie save error: {e}")

def clear_session():
    st.session_state.user = None
    st.session_state.logged_in = False
    st.session_state.role = None
    
    try:
        controller.remove('user_data')
        print("✅ Cookie cleared!")
    except Exception as e:
        print(f"Cookie remove error: {e}")

# ---------- LOGIN PAGE ----------
def login_page():
    st.title("🏫 Student Management System")
    st.subheader("🔐 Secure Login")
    
    if st.session_state.get('logged_in', False) and st.session_state.get('user'):
        st.rerun()
        return
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            email = st.text_input("📧 Email Address", placeholder="Enter your email")
            password = st.text_input("🔑 Password", type="password", placeholder="Enter your password")
            remember_me = st.checkbox("Remember me (stay logged in for 7 days)", value=True)
            submit = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if submit:
                if not email or not password:
                    st.error("⚠️ Please enter both email and password!")
                else:
                    user, error = login_user(email, password)
                    if user:
                        if remember_me:
                            save_session(user)
                        else:
                            st.session_state.user = user
                            st.session_state.logged_in = True
                            st.session_state.role = user.get('role', 'Unknown')
                        
                        st.session_state.message = f"✅ Welcome back, {user.get('full_name', 'User')}!"
                        st.session_state.message_type = "success"
                        st.rerun()
                    else:
                        st.error(f"❌ Login failed: {error or 'Invalid credentials'}")
        
        st.caption("🔒 Secure system. Contact administrator for access.")

# ---------- MAIN APP ----------
def main():
    if db is None:
        st.error("❌ Firebase not initialized!")
        return
    
    init_session()
    
    print(f"🔍 main: logged_in={st.session_state.logged_in}, user={st.session_state.user is not None}")
    
    if not st.session_state.get('logged_in', False):
        login_page()
        return
    
    show_messages()
    
    user = st.session_state.user
    role = st.session_state.role
    full_name = user.get('full_name', 'User')
    
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/school--v1.png", width=80)
        st.title(f"👋 {full_name}")
        st.write(f"**Role:** {role}")
        st.write(f"**Logged in:** {datetime.now().strftime('%H:%M:%S')}")
        st.divider()
        
        if role == 'Admin':
            pages = {
                "📊 Dashboard": admin_dashboard,
                "👨‍🎓 Students": admin_students,
                "👨‍🏫 Teachers": admin_teachers,
                "👥 Roles": admin_roles.show,
                "📝 Grades": admin_grades,
                "📅 Attendance": admin_attendance,
                "📢 Announcements": admin_announcements.show,
            }
        elif role == 'Teacher':
            pages = {
                "📊 Dashboard": teacher_dashboard,
                "👨‍🎓 My Students": teacher_students,
                "📝 Add Grades": teacher_grades,
                "📅 Mark Attendance": teacher_attendance,
                "📢 Announcements": teacher_announcements.show,
            }
        elif role == 'Student':
#            pages = {
 #               "📊 Dashboard": student_dashboard,
 #               "👤 My Profile": student_profile,
 #               "📈 My Grades": student_grades,
 #               "📅 My Attendance": student_attendance,
 #               "📢 Announcements": student_announcements.show,
 #           }
#        elif role == 'Parent':
            pages = {
                "📊 Dashboard": parent_dashboard,
                "👨‍👩‍👦 My Children": parent_children,
                "📈 Progress": parent_progress,
            }
        else:
            pages = {"📊 Dashboard": default_dashboard}
        
        selected_page = st.radio("📌 Navigation", list(pages.keys()), index=0)
        st.divider()
        
        if st.button("🚪 Logout", use_container_width=True):
            clear_session()
            st.session_state.message = "Logged out successfully!"
            st.session_state.message_type = "info"
            st.rerun()
    
    page_function = pages.get(selected_page)
    if page_function:
        page_function(user)

# ---------- ADMIN PAGES ----------
def admin_dashboard(user):
    st.header("📊 Admin Dashboard")
    
    students = db.get_all_students()
    teachers = db.get_all_users(role='Teacher')
    parents = db.get_all_users(role='Parent')
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👨‍🎓 Total Students", len(students))
    col2.metric("👨‍🏫 Total Teachers", len(teachers))
    col3.metric("👨‍👩‍👦 Total Parents", len(parents))
    col4.metric("📚 Last Update", datetime.now().strftime("%H:%M"))
    
    if students:
        col1, col2 = st.columns(2)
        
        with col1:
            grades = [s.get('grade', 'Unknown') for s in students if s.get('grade')]
            if grades:
                grade_counts = pd.Series(grades).value_counts().reset_index()
                grade_counts.columns = ['Grade', 'Count']
                fig = px.bar(grade_counts, x='Grade', y='Count', title="Students by Grade")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No grade data available yet")
        
        with col2:
            statuses = [s.get('status', 'Active') for s in students]
            if statuses:
                status_counts = pd.Series(statuses).value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                fig = px.pie(status_counts, values='Count', names='Status', title="Student Status")
                st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("📋 Recent Students")
    if students:
        df = pd.DataFrame(students[:10])
        
        if 'student_id' not in df.columns:
            df['student_id'] = 'N/A'
        if 'full_name' not in df.columns:
            df['full_name'] = 'N/A'
        if 'grade' not in df.columns:
            df['grade'] = 'N/A'
        if 'email' not in df.columns:
            df['email'] = 'N/A'
        if 'status' not in df.columns:
            df['status'] = 'Active'
        
        st.dataframe(df[['student_id', 'full_name', 'grade', 'email', 'status']], use_container_width=True)
    else:
        st.info("No students added yet. Add your first student!")

def admin_students(user):
    st.header("👨‍🎓 Student Management")
    
    tab1, tab2 = st.tabs(["➕ Add Student", "📋 All Students"])
    
    with tab1:
        with st.form("add_student_form", clear_on_submit=True):
            st.info("📌 Student ID will be auto-generated")
            
            col1, col2 = st.columns(2)
            with col1:
                full_name = st.text_input("Full Name*")
                email = st.text_input("Email*", help="Will be used for login")
                password = st.text_input("Password", type="password", value="student123")
            with col2:
                grade = st.selectbox("Grade", ['1','2','3','4','5','6','7','8','9','10','11','12'])
                section = st.text_input("Section", max_chars=5)
                phone = st.text_input("Phone")
                gender = st.selectbox("Gender", ['Male', 'Female', 'Other'])
            
            address = st.text_area("Address")
            parent_contact = st.text_input("Parent Contact")
            
            submitted = st.form_submit_button("➕ Add Student", use_container_width=True)
            
            if submitted:
                is_valid = True
                if not full_name or not email:
                    st.error("⚠️ Full Name and Email are required!")
                    is_valid = False
                elif not validate_email(email):
                    st.error("⚠️ Invalid email format!")
                    is_valid = False
                elif phone and not validate_phone(phone):
                    st.error("⚠️ Phone must be at least 10 digits!")
                    is_valid = False
                
                if is_valid:
                    student_data = {
                        'full_name': full_name.strip(),
                        'email': email.strip(),
                        'password': password,
                        'grade': grade,
                        'section': section.strip() if section else "",
                        'phone': phone.strip() if phone else "",
                        'gender': gender,
                        'address': address.strip() if address else "",
                        'parent_contact': parent_contact.strip() if parent_contact else "",
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
            search = st.text_input("🔍 Search Students", placeholder="Search by name or ID")
            df = pd.DataFrame(students)
            
            if search:
                df = df[df['full_name'].str.contains(search, case=False) | 
                       df['student_id'].str.contains(search, case=False)]
            
            st.dataframe(df, use_container_width=True, height=400)
            
            if not df.empty:
                selected = st.selectbox("Select Student to Manage", df['student_id'].tolist())
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

def admin_teachers(user):
    st.header("👨‍🏫 Teacher Management")
    
    tab1, tab2 = st.tabs(["➕ Add Teacher", "📋 All Teachers"])
    
    with tab1:
        with st.form("add_teacher_form"):
            st.info("📌 Teacher ID will be auto-generated")
            
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
                        email=email.strip(),
                        password=password,
                        full_name=full_name.strip(),
                        phone=phone.strip() if phone else "",
                        subjects=subject_list,
                        class_assigned=class_assigned.strip() if class_assigned else ""
                    )
                    if success:
                        st.success(f"✅ {msg}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
    
    with tab2:
        teachers = db.get_all_teachers()
        if teachers:
            df = pd.DataFrame(teachers)
            st.dataframe(df, use_container_width=True, height=400)
        else:
            st.info("📭 No teachers added yet.")

def admin_grades(user):
    st.header("📝 Grade Management")
    
    students = db.get_all_students()
    if not students:
        st.info("📭 Add students first to manage grades.")
        return
    
    student_list = [s.get('student_id', s.get('uid', 'N/A')) for s in students if s.get('student_id') or s.get('uid')]
    if not student_list:
        st.warning("No students with valid IDs found.")
        return
    
    selected_student = st.selectbox("Select Student", student_list)
    
    if selected_student:
        tab1, tab2 = st.tabs(["➕ Add Grade", "📊 View Grades"])
        
        with tab1:
            with st.form("add_grade_form", clear_on_submit=True):
                subject = st.text_input("Subject*")
                marks = st.slider("Marks", 0, 100, 50)
                exam_type = st.selectbox("Exam Type", ["Regular", "Mid-Term", "Final", "Quiz"])
                
                submitted = st.form_submit_button("➕ Add Grade", use_container_width=True)
                if submitted:
                    if not subject:
                        st.error("⚠️ Subject is required!")
                    else:
                        success, msg = db.add_grade(selected_student, subject, marks, exam_type)
                        if success:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
        
        with tab2:
            grades = db.get_student_grades(selected_student)
            if grades:
                df = pd.DataFrame(grades)
                st.dataframe(df, use_container_width=True)
                
                avg = df['marks'].mean()
                col1, col2, col3 = st.columns(3)
                col1.metric("Average", f"{avg:.1f}")
                col2.metric("Highest", f"{df['marks'].max()}")
                col3.metric("Lowest", f"{df['marks'].min()}")
            else:
                st.info("No grades for this student.")

def admin_attendance(user):
    st.header("📅 Attendance Management")
    
    students = db.get_all_students()
    if not students:
        st.info("📭 Add students first to mark attendance.")
        return
    
    student_list = [s.get('student_id', s.get('uid', 'N/A')) for s in students if s.get('student_id') or s.get('uid')]
    if not student_list:
        st.warning("No students with valid IDs found.")
        return
    
    selected_student = st.selectbox("Select Student", student_list)
    
    if selected_student:
        col1, col2 = st.columns(2)
        
        with col1:
            status = st.selectbox("Status", ["Present", "Absent", "Late"])
            if st.button("✅ Mark Attendance", use_container_width=True):
                success, msg = db.mark_attendance(selected_student, status)
                if success:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.warning(f"⚠️ {msg}")
        
        with col2:
            attendance = db.get_student_attendance(selected_student)
            if attendance:
                df = pd.DataFrame(attendance)
                present = len(df[df['status'] == 'Present'])
                total = len(df)
                st.metric("Attendance %", f"{(present/total)*100:.1f}%" if total > 0 else "0%")
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No attendance records yet.")

# ---------- TEACHER PAGES ----------
def teacher_dashboard(user):
    st.header("👨‍🏫 Teacher Dashboard")
    
    students = db.get_all_students()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("👨‍🎓 My Students", len(students))
    col2.metric("📊 Classes", "1")
    col3.metric("📝 Today", datetime.now().strftime("%A"))
    
    if students:
        st.subheader("📋 My Students")
        df = pd.DataFrame(students)
        display_cols = [col for col in ['student_id', 'full_name', 'grade', 'section'] if col in df.columns]
        if display_cols:
            st.dataframe(df[display_cols], use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)

def teacher_students(user):
    st.header("👨‍🎓 My Students")
    
    students = db.get_all_students()
    if students:
        df = pd.DataFrame(students)
        st.dataframe(df, use_container_width=True, height=400)
    else:
        st.info("No students assigned yet.")

def teacher_grades(user):
    st.header("📝 Add Grades")
    
    students = db.get_all_students()
    if not students:
        st.info("📭 No students available.")
        return
    
    student_list = [s.get('student_id', s.get('uid', 'N/A')) for s in students if s.get('student_id') or s.get('uid')]
    if not student_list:
        st.warning("No students with valid IDs found.")
        return
    
    selected_student = st.selectbox("Select Student", student_list)
    
    with st.form("teacher_grade_form", clear_on_submit=True):
        subject = st.text_input("Subject*")
        marks = st.slider("Marks", 0, 100, 50)
        exam_type = st.selectbox("Exam Type", ["Regular", "Mid-Term", "Final", "Quiz"])
        
        if st.form_submit_button("➕ Add Grade", use_container_width=True):
            if not subject:
                st.error("⚠️ Subject is required!")
            else:
                success, msg = db.add_grade(selected_student, subject, marks, exam_type)
                if success:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

def teacher_attendance(user):
    st.header("📅 Mark Attendance")
    
    students = db.get_all_students()
    if not students:
        st.info("📭 No students available.")
        return
    
    student_list = [s.get('student_id', s.get('uid', 'N/A')) for s in students if s.get('student_id') or s.get('uid')]
    if not student_list:
        st.warning("No students with valid IDs found.")
        return
    
    selected_student = st.selectbox("Select Student", student_list)
    
    status = st.selectbox("Status", ["Present", "Absent", "Late"])
    if st.button("✅ Mark Attendance", use_container_width=True):
        success, msg = db.mark_attendance(selected_student, status)
        if success:
            st.success(f"✅ {msg}")
            st.rerun()
        else:
            st.warning(f"⚠️ {msg}")

# ---------- STUDENT PAGES (PROFESSIONAL VERSION) ----------
def student_dashboard(user):
    st.header("📚 Student Dashboard")
    
    # Get the student's ID from their user data
    student_id = user.get('student_id') or user.get('uid')
    
    # If no student_id, try to find it from the users collection
    if not student_id:
        email = user.get('email')
        if email:
            students = db.get_all_students()
            for s in students:
                if s.get('email') == email:
                    student_id = s.get('student_id') or s.get('uid')
                    break
    
    # If still no student_id, try using uid directly
    if not student_id:
        student_id = user.get('uid')
    
    # Get student data
    student = db.get_student(student_id)
    
    if student:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👤 My Profile")
            
            # Professional profile card
            st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 12px; border: 1px solid #e9ecef;">
                <p style="margin: 8px 0; font-size: 16px;">📛 <strong>Full Name:</strong> {student.get('full_name', 'N/A')}</p>
                <p style="margin: 8px 0; font-size: 16px;">🆔 <strong>Student ID:</strong> {student.get('student_id', 'N/A')}</p>
                <p style="margin: 8px 0; font-size: 16px;">📚 <strong>Grade:</strong> {student.get('grade', 'N/A')}</p>
                <p style="margin: 8px 0; font-size: 16px;">📖 <strong>Section:</strong> {student.get('section', 'N/A')}</p>
                <p style="margin: 8px 0; font-size: 16px;">📧 <strong>Email:</strong> {student.get('email', 'N/A')}</p>
                <p style="margin: 8px 0; font-size: 16px;">📱 <strong>Phone:</strong> {student.get('phone', 'N/A')}</p>
                <p style="margin: 8px 0; font-size: 16px;">📍 <strong>Address:</strong> {student.get('address', 'N/A')}</p>
                <p style="margin: 8px 0; font-size: 16px;">👤 <strong>Gender:</strong> {student.get('gender', 'N/A')}</p>
                <p style="margin: 8px 0; font-size: 16px;">📅 <strong>Status:</strong> <span style="color: #28a745; font-weight: bold;">{student.get('status', 'N/A')}</span></p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.subheader("📊 Quick Stats")
            grades = db.get_student_grades(student_id)
            attendance = db.get_student_attendance(student_id)
            
            # Stats cards
            col_stats1, col_stats2 = st.columns(2)
            
            with col_stats1:
                if grades:
                    avg = sum([g['marks'] for g in grades]) / len(grades)
                    st.markdown(f"""
                    <div style="background-color: #d4edda; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #c3e6cb;">
                        <h2 style="margin: 0; color: #155724;">{avg:.1f}%</h2>
                        <p style="margin: 0; color: #155724;">📈 Average Grade</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("📝 No grades yet")
            
            with col_stats2:
                if attendance:
                    present = len([a for a in attendance if a['status'] == 'Present'])
                    total = len(attendance)
                    percentage = (present / total * 100) if total > 0 else 0
                    st.markdown(f"""
                    <div style="background-color: #cce5ff; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #b8daff;">
                        <h2 style="margin: 0; color: #004085;">{percentage:.1f}%</h2>
                        <p style="margin: 0; color: #004085;">📅 Attendance</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("📅 No attendance records yet")
            
            # Additional stats
            st.markdown("<br>", unsafe_allow_html=True)
            with st.container():
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.metric("📚 Total Subjects", len(set([g.get('subject') for g in grades])) if grades else 0)
                with col_info2:
                    st.metric("📝 Total Grades", len(grades) if grades else 0)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 My Grades")
            grades = db.get_student_grades(student_id)
            if grades:
                df = pd.DataFrame(grades)
                # Select and rename columns for display
                display_df = df[['subject', 'marks', 'grade', 'exam_type', 'date']].copy()
                display_df.columns = ['Subject', 'Marks', 'Grade', 'Exam Type', 'Date']
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("📭 No grades yet.")
        
        with col2:
            st.subheader("📅 My Attendance")
            attendance = db.get_student_attendance(student_id)
            if attendance:
                df = pd.DataFrame(attendance)
                # Select and rename columns for display
                display_df = df[['date', 'status']].copy()
                display_df.columns = ['Date', 'Status']
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("📭 No attendance records yet.")
    else:
        st.warning("⚠️ Student profile not found. Please contact admin.")

def student_profile(user):
    st.header("👤 My Profile")
    
    # Get student_id from user data
    student_id = user.get('student_id') or user.get('uid')
    student = db.get_student(student_id)
    
    if student:
        # Professional profile card
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 25px; border-radius: 12px; border: 1px solid #e9ecef; max-width: 600px;">
            <h3 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">👤 Student Profile</h3>
            <p style="margin: 8px 0;"><strong>📛 Full Name:</strong> {student.get('full_name', 'N/A')}</p>
            <p style="margin: 8px 0;"><strong>🆔 Student ID:</strong> {student.get('student_id', 'N/A')}</p>
            <p style="margin: 8px 0;"><strong>📚 Grade:</strong> {student.get('grade', 'N/A')}</p>
            <p style="margin: 8px 0;"><strong>📖 Section:</strong> {student.get('section', 'N/A')}</p>
            <p style="margin: 8px 0;"><strong>📧 Email:</strong> {student.get('email', 'N/A')}</p>
            <p style="margin: 8px 0;"><strong>📱 Phone:</strong> {student.get('phone', 'N/A')}</p>
            <p style="margin: 8px 0;"><strong>📍 Address:</strong> {student.get('address', 'N/A')}</p>
            <p style="margin: 8px 0;"><strong>👤 Gender:</strong> {student.get('gender', 'N/A')}</p>
            <p style="margin: 8px 0;"><strong>📅 Status:</strong> <span style="color: #28a745; font-weight: bold;">{student.get('status', 'N/A')}</span></p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Profile not found")

def student_grades(user):
    st.header("📈 My Grades")
    
    # Get student_id from user data
    student_id = user.get('student_id') or user.get('uid')
    grades = db.get_student_grades(student_id)
    
    if grades:
        df = pd.DataFrame(grades)
        # Clean display
        display_df = df[['subject', 'marks', 'grade', 'exam_type', 'date']].copy()
        display_df.columns = ['Subject', 'Marks', 'Grade', 'Exam Type', 'Date']
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Chart
        fig = px.bar(df, x='subject', y='marks', title="📊 My Grades by Subject", color='grade', text='marks')
        fig.update_traces(textposition='outside')
        fig.update_layout(showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Average", f"{df['marks'].mean():.1f}%")
        with col2:
            st.metric("🏆 Highest", f"{df['marks'].max()}%")
        with col3:
            st.metric("📉 Lowest", f"{df['marks'].min()}%")
    else:
        st.info("📭 No grades available.")

def student_attendance(user):
    st.header("📅 My Attendance")
    
    # Get student_id from user data
    student_id = user.get('student_id') or user.get('uid')
    attendance = db.get_student_attendance(student_id)
    
    if attendance:
        df = pd.DataFrame(attendance)
        # Clean display
        display_df = df[['date', 'status']].copy()
        display_df.columns = ['Date', 'Status']
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Statistics
        present = len(df[df['status'] == 'Present'])
        total = len(df)
        percentage = (present / total * 100) if total > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📅 Total Days", total)
        with col2:
            st.metric("✅ Present", present)
        with col3:
            st.metric("📊 Attendance", f"{percentage:.1f}%")
        
        # Mini chart
        status_counts = df['status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        fig = px.pie(status_counts, values='Count', names='Status', title="Attendance Breakdown", color='Status')
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📭 No attendance records.")