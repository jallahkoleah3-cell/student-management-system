# utils/pages/teacher_announcements.py
import streamlit as st
from datetime import datetime

def show(user):
    st.header("📢 Announcements")
    
    tab1, tab2 = st.tabs(["📨 Send to Students", "📋 My Announcements"])
    
    with tab1:
        st.subheader("Send Announcement to Students")
        
        # Get students
        from utils.firebase_db import db
        students = db.get_all_students()
        
        if not students:
            st.warning("No students available to send announcements to.")
            return
        
        with st.form("teacher_announcement_form"):
            title = st.text_input("Title*", placeholder="Enter announcement title")
            message = st.text_area("Message*", placeholder="Enter your announcement message", height=150)
            
            # Select specific students or all
            send_to_all = st.checkbox("Send to all students", value=True)
            
            selected_students = []
            if not send_to_all:
                student_options = [f"{s.get('full_name', 'Unknown')} ({s.get('student_id', 'No ID')})" for s in students]
                selected = st.multiselect("Select students", student_options)
                
                for s_str in selected:
                    for s in students:
                        if f"{s.get('full_name', 'Unknown')} ({s.get('student_id', 'No ID')})" == s_str:
                            # Get the user UID for this student
                            if s.get('uid'):
                                selected_students.append(s.get('uid'))
            
            submitted = st.form_submit_button("📤 Send to Students", use_container_width=True)
            
            if submitted:
                if not title or not message:
                    st.error("⚠️ Please enter both title and message!")
                elif not send_to_all and not selected_students:
                    st.error("⚠️ Please select at least one student!")
                else:
                    target_users = None if send_to_all else selected_students
                    success, msg = db.send_announcement(
                        sender_id=user.get('uid'),
                        sender_name=user.get('full_name', 'Teacher'),
                        sender_role=user.get('role', 'Teacher'),
                        title=title,
                        message=message,
                        target_roles=['Student'] if send_to_all else [],
                        target_user_ids=target_users
                    )
                    
                    if success:
                        st.success(f"✅ {msg}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
    
    with tab2:
        st.subheader("My Announcements")
        
        from utils.firebase_db import db
        announcements = db.get_announcements_for_user(
            user_id=user.get('uid'),
            user_role='Student'
        )
        
        if announcements:
            for ann in announcements:
                with st.expander(f"📩 {ann.get('title', 'No title')} - {ann.get('created_at', '')[:10]}"):
                    st.write(f"**From:** {ann.get('sender_name', 'Unknown')} ({ann.get('sender_role', 'Unknown')})")
                    st.write(f"**Message:** {ann.get('message', 'No message')}")
                    st.write(f"**Sent:** {ann.get('created_at', 'Unknown')}")
                    
                    # Mark as read button
                    if not ann.get('is_read', False) and ann.get('notification_id'):
                        if st.button(f"✅ Mark as Read", key=f"read_{ann['id']}"):
                            db.mark_notification_read(ann['notification_id'])
                            st.success("Marked as read!")
                            st.rerun()
        else:
            st.info("No announcements yet.")