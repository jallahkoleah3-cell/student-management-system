import firebase_admin
from firebase_admin import credentials, firestore, auth
from datetime import datetime
import json
import os
from dotenv import load_dotenv
from utils.id_generator import id_generator

load_dotenv()

class FirebaseDB:
    def __init__(self):
        try:
            cred_path = os.getenv('FIREBASE_CREDENTIALS', 'firebase-key.json')
            if not os.path.exists(cred_path):
                raise FileNotFoundError(f"Credentials file not found: {cred_path}")
            
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            self.auth = auth
            print("✅ Firebase initialized successfully!")
        except Exception as e:
            print(f"❌ Firebase initialization error: {e}")
            raise

    # ---------- USER MANAGEMENT ----------
    def create_user(self, email, password, full_name, role, phone="", parent_id=None, user_id=None):
        """Create a new user in Firebase Auth and Firestore with auto-generated ID"""
        try:
            # Generate user ID if not provided
            if not user_id:
                if role == 'Admin':
                    user_id = id_generator.generate_admin_id()
                elif role == 'Teacher':
                    user_id = id_generator.generate_teacher_id()
                elif role == 'Student':
                    user_id = id_generator.generate_student_id()
                elif role == 'Parent':
                    user_id = id_generator.generate_parent_id()
                else:
                    user_id = id_generator.generate_unique_id(role)
            
            # Create user in Firebase Auth
            user = auth.create_user(
                email=email,
                password=password,
                display_name=full_name
            )
            
            # Store user data in Firestore with user_id
            user_data = {
                'uid': user.uid,
                'user_id': user_id,
                'email': email,
                'full_name': full_name,
                'role': role,
                'phone': phone,
                'created_at': datetime.now().isoformat(),
                'status': 'Active',
                'parent_id': parent_id
            }
            
            self.db.collection('users').document(user.uid).set(user_data)
            
            # If role is student, also create student profile with student_id
            if role == 'Student':
                student_data = {
                    'uid': user.uid,
                    'user_id': user_id,
                    'student_id': user_id,
                    'full_name': full_name,
                    'email': email,
                    'phone': phone,
                    'created_at': datetime.now().isoformat(),
                    'status': 'Active'
                }
                self.db.collection('students').document(user_id).set(student_data)
            
            # If role is Admin, create admin profile
            if role == 'Admin':
                admin_data = {
                    'user_id': user_id,
                    'admin_id': user_id,
                    'created_at': datetime.now().isoformat()
                }
                self.db.collection('admins').document(user.uid).set(admin_data)
            
            return True, user.uid, f"User created successfully! ID: {user_id}"
        except auth.EmailAlreadyExistsError:
            return False, None, "Email already exists!"
        except Exception as e:
            return False, None, f"Error: {str(e)}"

    def authenticate_user(self, email, password):
        """Authenticate user (using Firebase Admin SDK)"""
        try:
            users_ref = self.db.collection('users').where('email', '==', email).stream()
            for user_doc in users_ref:
                user_data = user_doc.to_dict()
                return user_data
            return None
        except Exception as e:
            print(f"Auth error: {e}")
            return None

    def get_user_by_uid(self, uid):
        """Get user data by UID"""
        try:
            doc = self.db.collection('users').document(uid).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def get_all_users(self, role=None):
        """Get all users, optionally filtered by role"""
        try:
            if role:
                users = self.db.collection('users').where('role', '==', role).stream()
            else:
                users = self.db.collection('users').stream()
            
            data = []
            for doc in users:
                user_data = doc.to_dict()
                user_data['uid'] = doc.id
                data.append(user_data)
            return data
        except Exception as e:
            print(f"Error: {e}")
            return []

    def update_user(self, uid, data):
        """Update user data"""
        try:
            self.db.collection('users').document(uid).update(data)
            return True, "User updated successfully!"
        except Exception as e:
            return False, f"Error: {e}"

    def delete_user(self, uid):
        """Delete user from Auth and Firestore"""
        try:
            auth.delete_user(uid)
            self.db.collection('users').document(uid).delete()
            return True, "User deleted successfully!"
        except Exception as e:
            return False, f"Error: {e}"

    # ---------- STUDENT MANAGEMENT ----------
    def add_student(self, student_data):
        """Add a new student with auto-generated ID"""
        try:
            # Generate unique student ID if not provided
            if not student_data.get('student_id'):
                student_id = id_generator.generate_student_id()
                student_data['student_id'] = student_id
                print(f"✅ Auto-generated Student ID: {student_id}")
            else:
                student_id = student_data['student_id']
                # Check if provided ID already exists
                existing = self.db.collection('students').where('student_id', '==', student_id).get()
                if len(list(existing)) > 0:
                    return False, f"Student ID {student_id} already exists!"
            
            # Check if student already exists by email
            if student_data.get('email'):
                existing = self.db.collection('students').where('email', '==', student_data['email']).get()
                if len(list(existing)) > 0:
                    return False, f"Student with email {student_data['email']} already exists!"
            
            # Add student data
            student_data['user_id'] = student_id
            student_data['created_at'] = datetime.now().isoformat()
            student_data['status'] = 'Active'
            self.db.collection('students').document(student_id).set(student_data)
            
            # Also create a user account for the student with the generated ID
            if student_data.get('email'):
                success, uid, msg = self.create_user(
                    email=student_data['email'],
                    password=student_data.get('password', 'student123'),
                    full_name=student_data['full_name'],
                    role='Student',
                    phone=student_data.get('phone', ''),
                    user_id=student_id  # Pass the generated ID
                )
                if not success:
                    return False, f"Student added but user creation failed: {msg}"
            
            return True, f"Student added successfully! ID: {student_id}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def get_all_students(self):
        """Get all students"""
        try:
            students = self.db.collection('students').stream()
            data = []
            for doc in students:
                student_data = doc.to_dict()
                student_data['id'] = doc.id
                data.append(student_data)
            return data
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_student(self, student_id):
        """Get a single student by ID"""
        try:
            # Method 1: Try by document ID
            doc = self.db.collection('students').document(student_id).get()
            if doc.exists:
                return doc.to_dict()
            
            # Method 2: Search by student_id field
            students = self.db.collection('students').where('student_id', '==', student_id).stream()
            for student in students:
                return student.to_dict()
            
            # Method 3: Try to find by email
            students = self.db.collection('students').where('email', '==', student_id).stream()
            for student in students:
                return student.to_dict()
            
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def update_student(self, student_id, data):
        """Update student data - FIXED!"""
        try:
            # Method 1: Try to update by document ID
            try:
                doc_ref = self.db.collection('students').document(student_id)
                doc_ref.update(data)
                return True, "Student updated successfully!"
            except:
                pass  # If that fails, try method 2
            
            # Method 2: Search by student_id field
            students = self.db.collection('students').where('student_id', '==', student_id).stream()
            doc_exists = False
            for doc in students:
                doc.reference.update(data)
                doc_exists = True
                break
            
            if doc_exists:
                return True, "Student updated successfully!"
            
            # Method 3: Try searching by email
            if data.get('email'):
                students = self.db.collection('students').where('email', '==', data['email']).stream()
                for doc in students:
                    doc.reference.update(data)
                    return True, "Student updated successfully!"
            
            return False, f"Student with ID {student_id} not found!"
        except Exception as e:
            return False, f"Error: {e}"

    def delete_student(self, student_id):
        """Delete a student"""
        try:
            # Try to delete by document ID first
            try:
                self.db.collection('students').document(student_id).delete()
            except:
                # If that fails, try by student_id field
                students = self.db.collection('students').where('student_id', '==', student_id).stream()
                for doc in students:
                    doc.reference.delete()
            
            # Delete related grades
            grades = self.db.collection('grades').where('student_id', '==', student_id).stream()
            for grade in grades:
                grade.reference.delete()
            
            # Delete related attendance
            attendance = self.db.collection('attendance').where('student_id', '==', student_id).stream()
            for att in attendance:
                att.reference.delete()
            
            return True, "Student deleted successfully!"
        except Exception as e:
            return False, f"Error: {e}"

    # ---------- TEACHER MANAGEMENT ----------
    def add_teacher(self, email, password, full_name, phone, subjects=[], class_assigned=""):
        """Add a new teacher with auto-generated ID"""
        try:
            # Generate teacher ID
            teacher_id = id_generator.generate_teacher_id()
            print(f"✅ Auto-generated Teacher ID: {teacher_id}")
            
            # Check if email already exists
            existing = self.db.collection('users').where('email', '==', email).stream()
            if len(list(existing)) > 0:
                return False, f"Email {email} already exists!"
            
            # Create teacher user with the generated ID
            success, uid, msg = self.create_user(
                email=email,
                password=password,
                full_name=full_name,
                role='Teacher',
                phone=phone,
                user_id=teacher_id
            )
            
            if not success:
                return False, msg
            
            # Add teacher-specific data
            teacher_data = {
                'user_id': teacher_id,
                'teacher_id': teacher_id,
                'subjects': subjects,
                'class_assigned': class_assigned,
                'hire_date': datetime.now().isoformat()
            }
            self.db.collection('teachers').document(uid).set(teacher_data)
            
            return True, f"Teacher added successfully! ID: {teacher_id}"
        except Exception as e:
            return False, f"Error: {e}"

    def get_all_teachers(self):
        """Get all teachers"""
        try:
            teachers = self.db.collection('users').where('role', '==', 'Teacher').stream()
            data = []
            for doc in teachers:
                teacher_data = doc.to_dict()
                teacher_data['uid'] = doc.id
                
                teacher_info = self.db.collection('teachers').document(doc.id).get()
                if teacher_info.exists:
                    teacher_data.update(teacher_info.to_dict())
                
                data.append(teacher_data)
            return data
        except Exception as e:
            print(f"Error: {e}")
            return []

    # ---------- PARENT MANAGEMENT ----------
    def add_parent(self, email, password, full_name, phone, student_ids=[]):
        """Add a parent with auto-generated ID"""
        try:
            # Generate parent ID
            parent_id = id_generator.generate_parent_id()
            print(f"✅ Auto-generated Parent ID: {parent_id}")
            
            # Create parent user with the generated ID
            success, uid, msg = self.create_user(
                email=email,
                password=password,
                full_name=full_name,
                role='Parent',
                phone=phone,
                user_id=parent_id
            )
            
            if not success:
                return False, msg
            
            # Link students to parent
            for student_id in student_ids:
                self.db.collection('parent_students').add({
                    'parent_id': uid,
                    'student_id': student_id,
                    'relationship': 'Parent'
                })
            
            # Update parent profile
            parent_data = {
                'parent_id': parent_id,
                'user_id': parent_id,
                'student_ids': student_ids
            }
            self.db.collection('parents').document(uid).set(parent_data)
            
            return True, f"Parent added successfully! ID: {parent_id}"
        except Exception as e:
            return False, f"Error: {e}"

    def get_parent_students(self, parent_uid):
        """Get all students linked to a parent"""
        try:
            links = self.db.collection('parent_students').where('parent_id', '==', parent_uid).stream()
            student_ids = [link.to_dict()['student_id'] for link in links]
            
            students = []
            for student_id in student_ids:
                student = self.get_student(student_id)
                if student:
                    students.append(student)
            return students
        except Exception as e:
            print(f"Error: {e}")
            return []

    # ---------- ADMIN MANAGEMENT ----------
    def create_admin(self, email, password, full_name, phone=""):
        """Create a new admin with auto-generated ID"""
        try:
            admin_id = id_generator.generate_admin_id()
            print(f"✅ Auto-generated Admin ID: {admin_id}")
            
            success, uid, msg = self.create_user(
                email=email,
                password=password,
                full_name=full_name,
                role='Admin',
                phone=phone,
                user_id=admin_id
            )
            
            if not success:
                return False, msg
            
            # Add admin-specific data
            admin_data = {
                'user_id': admin_id,
                'admin_id': admin_id,
                'created_at': datetime.now().isoformat()
            }
            self.db.collection('admins').document(uid).set(admin_data)
            
            return True, f"Admin created successfully! ID: {admin_id}"
        except Exception as e:
            return False, f"Error: {e}"


    # ---------- ROLE MANAGEMENT ----------
    def get_user_role(self, uid):
        """Get the role of a user"""
        try:
            doc = self.db.collection('users').document(uid).get()
            if doc.exists:
                return doc.to_dict().get('role', 'Unknown')
            return None
        except Exception as e:
            print(f"Error getting user role: {e}")
            return None

    def update_user_role(self, uid, new_role):
        """Update a user's role"""
        try:
            # Validate role
            valid_roles = ['Admin', 'Teacher', 'Student', 'Parent']
            if new_role not in valid_roles:
                return False, f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            
            # Get current user data
            user_data = self.get_user_by_uid(uid)
            if not user_data:
                return False, "User not found!"
            
            old_role = user_data.get('role')
            
            # Update in Firestore
            self.db.collection('users').document(uid).update({
                'role': new_role,
                'role_updated_at': datetime.now().isoformat()
            })
            
            # Log the change
            print(f"🔄 Role changed: {old_role} → {new_role} for user {uid}")
            
            return True, f"Role updated from {old_role} to {new_role}!"
        except Exception as e:
            return False, f"Error: {e}"

    def get_users_by_role(self, role):
        """Get all users with a specific role"""
        return self.get_all_users(role=role)

    def get_role_counts(self):
        """Get count of users by role"""
        try:
            roles = ['Admin', 'Teacher', 'Student', 'Parent']
            counts = {}
            for role in roles:
                users = self.db.collection('users').where('role', '==', role).stream()
                counts[role] = len(list(users))
            return counts
        except Exception as e:
            print(f"Error: {e}")
            return {}


    # ---------- GRADES MANAGEMENT ----------
    def add_grade(self, student_id, subject, marks, exam_type="Regular"):
        """Add a grade for a student"""
        try:
            if marks < 0 or marks > 100:
                return False, "Marks must be between 0 and 100!"
            
            # Calculate grade
            if marks >= 95:
                grade = 'A+'
            elif marks >= 90:
                grade = 'A'
            elif marks >= 85:
                grade = 'B+'
            elif marks >= 80:
                grade = 'B'
            elif marks >= 75:
                grade = 'C+'
            elif marks >= 70:
                grade = 'C'
            elif marks >= 65:
                grade = 'D+'
            elif marks >= 60:
                grade = 'D'
            elif marks >= 50:
                grade = 'E'
            else:
                grade = 'F'
            
            grade_data = {
                'student_id': student_id,
                'subject': subject,
                'marks': marks,
                'grade': grade,
                'exam_type': exam_type,
                'date': datetime.now().isoformat()
            }
            
            # Generate a unique ID
            grade_id = f"{student_id}_{subject}_{datetime.now().timestamp()}"
            self.db.collection('grades').document(grade_id).set(grade_data)
            
            return True, f"Grade added! ({grade})"
        except Exception as e:
            return False, f"Error: {e}"

    def get_student_grades(self, student_id):
        """Get all grades for a student"""
        try:
            grades = self.db.collection('grades').where('student_id', '==', student_id).stream()
            data = []
            for doc in grades:
                grade_data = doc.to_dict()
                grade_data['id'] = doc.id
                data.append(grade_data)
            return data
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_class_grades(self, class_name):
        """Get all grades for a class"""
        try:
            students = self.db.collection('students').where('class', '==', class_name).stream()
            student_ids = [doc.id for doc in students]
            
            data = []
            for student_id in student_ids:
                grades = self.get_student_grades(student_id)
                data.extend(grades)
            return data
        except Exception as e:
            print(f"Error: {e}")
            return []

    # ---------- ATTENDANCE MANAGEMENT ----------
    def mark_attendance(self, student_id, status, date=None):
        """Mark attendance for a student"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            # Check if already marked for today
            existing = self.db.collection('attendance')\
                .where('student_id', '==', student_id)\
                .where('date', '==', date)\
                .get()
            
            if len(list(existing)) > 0:
                return False, "Attendance already marked for today!"
            
            attendance_data = {
                'student_id': student_id,
                'date': date,
                'status': status,
                'timestamp': datetime.now().isoformat()
            }
            
            att_id = f"{student_id}_{date}"
            self.db.collection('attendance').document(att_id).set(attendance_data)
            
            return True, f"Attendance marked as {status}!"
        except Exception as e:
            return False, f"Error: {e}"

    def get_student_attendance(self, student_id):
        """Get attendance for a student"""
        try:
            attendance = self.db.collection('attendance')\
                .where('student_id', '==', student_id)\
                .order_by('date', direction='DESCENDING')\
                .stream()
            
            data = []
            for doc in attendance:
                att_data = doc.to_dict()
                att_data['id'] = doc.id
                data.append(att_data)
            return data
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_class_attendance(self, class_name, date=None):
        """Get attendance for a class on a specific date"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            students = self.db.collection('students').where('class', '==', class_name).stream()
            student_ids = [doc.id for doc in students]
            
            data = []
            for student_id in student_ids:
                attendance = self.db.collection('attendance')\
                    .where('student_id', '==', student_id)\
                    .where('date', '==', date)\
                    .get()
                
                for doc in attendance:
                    att_data = doc.to_dict()
                    att_data['id'] = doc.id
                    data.append(att_data)
            return data
        except Exception as e:
            print(f"Error: {e}")
            return []

    # ---------- REPORTS ----------
    def generate_student_report(self, student_id):
        """Generate a comprehensive report for a student"""
        try:
            student = self.get_student(student_id)
            if not student:
                return None
            
            grades = self.get_student_grades(student_id)
            attendance = self.get_student_attendance(student_id)
            
            total_subjects = len(set([g['subject'] for g in grades]))
            avg_marks = sum([g['marks'] for g in grades]) / len(grades) if grades else 0
            
            present = len([a for a in attendance if a['status'] == 'Present'])
            total = len(attendance)
            attendance_percentage = (present / total * 100) if total > 0 else 0
            
            report = {
                'student': student,
                'grades': grades,
                'attendance': attendance,
                'statistics': {
                    'total_subjects': total_subjects,
                    'average_marks': avg_marks,
                    'attendance_percentage': attendance_percentage,
                    'total_days': total,
                    'present_days': present
                }
            }
            
            return report
        except Exception as e:
            print(f"Error: {e}")
            return None

    # ---------- ANNOUNCEMENT MANAGEMENT ----------
    def send_announcement(self, sender_id, sender_name, sender_role, title, message, target_roles, target_user_ids=None):
        """
        Send an announcement
        
        Args:
            sender_id: UID of sender
            sender_name: Name of sender
            sender_role: Role of sender (Admin/Teacher)
            title: Announcement title
            message: Announcement content
            target_roles: List of roles to send to ['Admin', 'Teacher', 'Student', 'Parent']
            target_user_ids: Optional list of specific user UIDs
        """
        try:
            announcement_data = {
                'sender_id': sender_id,
                'sender_name': sender_name,
                'sender_role': sender_role,
                'title': title,
                'message': message,
                'target_roles': target_roles,
                'created_at': datetime.now().isoformat(),
                'is_global': target_user_ids is None or len(target_user_ids) == 0
            }
            
            # Save the announcement
            doc_ref = self.db.collection('announcements').document()
            announcement_id = doc_ref.id
            announcement_data['id'] = announcement_id
            doc_ref.set(announcement_data)
            
            # Send to targeted users
            if target_user_ids and len(target_user_ids) > 0:
                for user_id in target_user_ids:
                    self._create_notification(user_id, announcement_id, title, message, 'announcement')
            else:
                # Send to all users in target roles
                users = self.get_all_users()
                for user in users:
                    if user.get('role') in target_roles or 'All' in target_roles:
                        self._create_notification(user.get('uid'), announcement_id, title, message, 'announcement')
            
            return True, "Announcement sent successfully!"
        except Exception as e:
            return False, f"Error: {e}"

    def _create_notification(self, user_id, announcement_id, title, message, notification_type):
        """Create a notification for a user"""
        try:
            notification_data = {
                'user_id': user_id,
                'announcement_id': announcement_id,
                'title': title,
                'message': message,
                'type': notification_type,
                'is_read': False,
                'created_at': datetime.now().isoformat()
            }
            self.db.collection('notifications').add(notification_data)
        except Exception as e:
            print(f"Error creating notification: {e}")

    def get_user_notifications(self, user_id):
        """Get all notifications for a user"""
        try:
            notifications = self.db.collection('notifications')\
                .where('user_id', '==', user_id)\
                .order_by('created_at', direction='DESCENDING')\
                .stream()
            
            data = []
            for doc in notifications:
                notif_data = doc.to_dict()
                notif_data['id'] = doc.id
                data.append(notif_data)
            return data
        except Exception as e:
            print(f"Error: {e}")
            return []

    def mark_notification_read(self, notification_id):
        """Mark a notification as read"""
        try:
            self.db.collection('notifications').document(notification_id).update({
                'is_read': True,
                'read_at': datetime.now().isoformat()
            })
            return True, "Notification marked as read"
        except Exception as e:
            return False, f"Error: {e}"

    def mark_all_notifications_read(self, user_id):
        """Mark all notifications for a user as read"""
        try:
            notifications = self.db.collection('notifications')\
                .where('user_id', '==', user_id)\
                .where('is_read', '==', False)\
                .stream()
            
            for doc in notifications:
                doc.reference.update({
                    'is_read': True,
                    'read_at': datetime.now().isoformat()
                })
            return True, "All notifications marked as read"
        except Exception as e:
            return False, f"Error: {e}"

    def get_all_announcements(self, limit=100):
        """Get all announcements (for admin)"""
        try:
            announcements = self.db.collection('announcements')\
                .order_by('created_at', direction='DESCENDING')\
                .limit(limit)\
                .stream()
            
            data = []
            for doc in announcements:
                ann_data = doc.to_dict()
                ann_data['id'] = doc.id
                data.append(ann_data)
            return data
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_announcements_for_user(self, user_id, user_role):
        """Get announcements targeted for a specific user"""
        try:
            # Get announcements targeted for this role or all roles
            announcements = self.db.collection('announcements')\
                .where('target_roles', 'array_contains', user_role)\
                .order_by('created_at', direction='DESCENDING')\
                .stream()
            
            data = []
            for doc in announcements:
                ann_data = doc.to_dict()
                ann_data['id'] = doc.id
                
                # Check if user has read this announcement
                notifications = self.db.collection('notifications')\
                    .where('user_id', '==', user_id)\
                    .where('announcement_id', '==', ann_data['id'])\
                    .stream()
                
                for notif in notifications:
                    notif_data = notif.to_dict()
                    ann_data['is_read'] = notif_data.get('is_read', False)
                    ann_data['notification_id'] = notif.id
                
                data.append(ann_data)
            return data
        except Exception as e:
            print(f"Error: {e}")
            return []

# Initialize Firebase
try:
    db = FirebaseDB()
except Exception as e:
    print(f"Failed to initialize Firebase: {e}")
    db = None
