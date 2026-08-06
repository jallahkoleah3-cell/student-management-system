import streamlit as st
import pandas as pd
from utils.firebase_db import db

def show(user):
    st.header("👤 Role Management")
    st.write("Manage user roles and permissions")
    
    tab1, tab2 = st.tabs(["📋 View Users", "🔄 Change Role"])
    
    with tab1:
        st.subheader("All Users")
        
        users = db.get_all_users()
        if users:
            df = pd.DataFrame(users)
            
            # Select columns to display
            display_cols = ['email', 'full_name', 'role', 'status', 'created_at']
            display_cols = [col for col in display_cols if col in df.columns]
            
            st.dataframe(df[display_cols], use_container_width=True, height=400)
            
            # Summary stats
            col1, col2, col3, col4 = st.columns(4)
            role_counts = db.get_role_counts()
            col1.metric("👨‍💼 Admins", role_counts.get('Admin', 0))
            col2.metric("👨‍🏫 Teachers", role_counts.get('Teacher', 0))
            col3.metric("👨‍🎓 Students", role_counts.get('Student', 0))
            col4.metric("👨‍👩‍👦 Parents", role_counts.get('Parent', 0))
        else:
            st.info("No users found.")
    
    with tab2:
        st.subheader("Change User Role")
        
        # Get all users
        users = db.get_all_users()
        if not users:
            st.info("No users available.")
            return
        
        # Create user selection
        user_options = {}
        for u in users:
            if u.get('email'):
                user_options[f"{u.get('email')} ({u.get('full_name', 'Unknown')})"] = u.get('uid')
        
        selected_user = st.selectbox("Select User", list(user_options.keys()))
        
        if selected_user:
            uid = user_options[selected_user]
            current_user = db.get_user_by_uid(uid)
            
            if current_user:
                current_role = current_user.get('role', 'Unknown')
                st.info(f"Current Role: **{current_role}**")
                
                # Role selection
                roles = ['Admin', 'Teacher', 'Student', 'Parent']
                new_role = st.selectbox("New Role", roles, index=roles.index(current_role) if current_role in roles else 0)
                
                if st.button("🔄 Update Role", use_container_width=True):
                    if new_role == current_role:
                        st.warning("⚠️ User already has this role.")
                    else:
                        success, msg = db.update_user_role(uid, new_role)
                        if success:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
