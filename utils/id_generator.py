import random
import string

class IDGenerator:
    def __init__(self):
        # Don't initialize Firestore here - wait until it's needed
        self._db = None
    
    @property
    def db(self):
        """Lazy-load Firestore client when first accessed"""
        if self._db is None:
            import firebase_admin
            from firebase_admin import firestore
            # Use the existing Firebase app
            self._db = firestore.client()
        return self._db
    
    def generate_unique_id(self, role, length=5):
        """
        Generate a unique ID for a specific role
        
        Args:
            role: 'Admin', 'Teacher', 'Student', 'Parent'
            length: Number of digits (default 5)
        
        Returns:
            Unique ID string
        """
        prefixes = {
            'Admin': 'ADM',
            'Teacher': 'TCH',
            'Student': 'STU',
            'Parent': 'PRT'
        }
        
        prefix = prefixes.get(role, 'USR')
        
        # Try up to 100 times to generate a unique ID
        for attempt in range(100):
            # Generate random numbers
            number_part = ''.join(random.choices(string.digits, k=length))
            new_id = f"{prefix}-{number_part}"
            
            # Check if ID already exists
            if not self._id_exists(new_id, role):
                return new_id
        
        # If we couldn't generate a unique ID, use timestamp
        import time
        timestamp = str(int(time.time()))[-length:]
        return f"{prefix}-{timestamp}"
    
    def _id_exists(self, id_value, role):
        """Check if an ID already exists in the system"""
        try:
            # Check in users collection
            users_ref = self.db.collection('users').where('user_id', '==', id_value).get()
            if len(list(users_ref)) > 0:
                return True
            
            # Check in role-specific collection
            collection_map = {
                'Admin': 'admins',
                'Teacher': 'teachers',
                'Student': 'students',
                'Parent': 'parents'
            }
            
            collection = collection_map.get(role, 'users')
            
            # Check in the specific collection
            role_ref = self.db.collection(collection).where('user_id', '==', id_value).get()
            if len(list(role_ref)) > 0:
                return True
            
            return False
        except Exception as e:
            print(f"Error checking ID existence: {e}")
            return False
    
    def generate_student_id(self):
        """Generate a unique Student ID"""
        return self.generate_unique_id('Student')
    
    def generate_teacher_id(self):
        """Generate a unique Teacher ID"""
        return self.generate_unique_id('Teacher')
    
    def generate_parent_id(self):
        """Generate a unique Parent ID"""
        return self.generate_unique_id('Parent')
    
    def generate_admin_id(self):
        """Generate a unique Admin ID"""
        return self.generate_unique_id('Admin')

# Singleton instance - will be created when first accessed
id_generator = IDGenerator()