# setup_users.py
import firebase_admin
from firebase_admin import credentials, firestore, auth
from datetime import datetime
import os

# Initialize Firebase
cred = credentials.Certificate('../firebase-key.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Define demo users
demo_users = [
    {
        'email': 'admin@school.com',
        'password': 'admin123',
        'full_name': 'System Administrator',
        'role': 'Admin',
        'phone': '+1234567890'
    },
    {
        'email': 'teacher@school.com',
        'password': 'teacher123',
        'full_name': 'Mr. Johnson',
        'role': 'Teacher',
        'phone': '+1234567891'
    },
    {
        'email': 'student@school.com',
        'password': 'student123',
        'full_name': 'John Doe',
        'role': 'Student',
        'phone': '+1234567892'
    },
    {
        'email': 'parent@school.com',
        'password': 'parent123',
        'full_name': 'Parent Name',
        'role': 'Parent',
        'phone': '+1234567893'
    }
]

def create_user(user_data):
    """Create user in Firebase Auth and Firestore"""
    try:
        # Check if user exists in Auth
        try:
            existing_user = auth.get_user_by_email(user_data['email'])
            uid = existing_user.uid
            print(f"⚠️ User {user_data['email']} already exists in Auth")
        except auth.UserNotFoundError:
            # Create user in Auth
            user = auth.create_user(
                email=user_data['email'],
                password=user_data['password'],
                display_name=user_data['full_name']
            )
            uid = user.uid
            print(f"✅ Created Auth user: {user_data['email']}")
        
        # Create/Update user in Firestore
        user_data['uid'] = uid
        user_data['created_at'] = datetime.now().isoformat()
        user_data['status'] = 'Active'
        
        # Remove password before storing in Firestore
        user_data.pop('password', None)
        
        # Store in Firestore
        db.collection('users').document(uid).set(user_data)
        print(f"✅ Stored in Firestore: {user_data['email']}")
        
        # If role is Student, also create student profile
        if user_data['role'] == 'Student':
            student_data = {
                'uid': uid,
                'student_id': user_data['email'].split('@')[0].upper(),
                'full_name': user_data['full_name'],
                'email': user_data['email'],
                'phone': user_data['phone'],
                'created_at': datetime.now().isoformat(),
                'status': 'Active'
            }
            # Check if student already exists
            existing_student = db.collection('students').document(uid).get()
            if existing_student.exists:
                db.collection('students').document(uid).update(student_data)
            else:
                db.collection('students').document(uid).set(student_data)
            print(f"✅ Created student profile for: {user_data['email']}")
        
        # If role is Teacher, also create teacher profile
        if user_data['role'] == 'Teacher':
            teacher_data = {
                'subjects': ['Math', 'Science'],
                'class_assigned': 'Class 10A',
                'hire_date': datetime.now().isoformat()
            }
            db.collection('teachers').document(uid).set(teacher_data)
            print(f"✅ Created teacher profile for: {user_data['email']}")
            
        return True, f"Successfully set up {user_data['email']}"
    
    except Exception as e:
        return False, f"Error for {user_data['email']}: {str(e)}"

# Main execution
print("🚀 Setting up demo users...")
print("=" * 50)

for user in demo_users:
    success, msg = create_user(user)
    if success:
        print(f"✅ {msg}")
    else:
        print(f"❌ {msg}")

print("=" * 50)
print("✅ Demo users setup complete!")
print("\n📝 You can now log in with:")
print("Admin: admin@school.com / admin123")
print("Teacher: teacher@school.com / teacher123")
print("Student: student@school.com / student123")
print("Parent: parent@school.com / parent123")