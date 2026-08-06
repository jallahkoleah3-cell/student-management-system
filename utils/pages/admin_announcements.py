# utils/pages/admin_announcements.py
import streamlit as st
from datetime import datetime

def show(user):
    st.header("📢 Announcements")
    
    tab1, tab2 = st.tabs(["📨 Send Announcement", "📋 All Announcements"])
    
    with tab1:
        st.subheader("Send New Announcement")
        
        with st.form("send_announcement_form"):
            title = st.text_input("Title*", placeholder="Enter announcement title")
            message = st.text_area("Message*", placeholder="Enter your announcement message", height=150)
            
            # Target selection
            st.subheader("Send To:")
            target_options = st.multiselect(
                "Select target roles",
                ['All', 'Admin', 'Teacher', 'Student', 'Parent'],
                default=['Teacher', 'Student']
            )
            
            # Optional: Specific user selection
            send_to_specific = st.checkbox("Send to specific users (instead of all users in roles)")
            
            specific_users = []
            if send_to_specific:
                # Get all users
                from utils.firebase_db import db
                all_users = db.get_all_users()
                user_options = [f"{u.get('full_name', 'Unknown')} ({u.get('email', 'No email')})" for u in all_users]
                selected_users = st.multiselect("Select specific users", user_options)
                
                # Extract user UIDs
                for user_str in selected_users:
                    for u in all_users:
                        if f"{u.get('full_name', 'Unknown')} ({u.get('email', 'No email')})" == user_str:
                            specific_users.append(u.get('uid'))
                            break
            
            submitted = st.form_submit_button("📤 Send Announcement", use_container_width=True)
            
            if submitted:
                if not title or not message:
                    st.error("⚠️ Please enter both title and message!")
                elif not target_options:
                    st.error("⚠️ Please select at least one target role!")
                elif send_to_specific and not specific_users:
                    st.error("⚠️ Please select specific users!")
                else:
                    # Send announcement
                    from utils.firebase_db import db
                    success, msg = db.send_announcement(
                        sender_id=user.get('uid'),
                        sender_name=user.get('full_name', 'Admin'),
                        sender_role=user.get('role', 'Admin'),
                        title=title,
                        message=message,
                        target_roles=target_options if 'All' not in target_options else ['All'],
                        target_user_ids=specific_users if send_to_specific else None
                    )
                    
                    if success:
                        st.success(f"✅ {msg}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
    
    with tab2:
        st.subheader("All Announcements")
        
        from utils.firebase_db import db
        announcements = db.get_all_announcements()
        
        if announcements:
            for ann in announcements:
                with st.expander(f"📩 {ann.get('title', 'No title')} - {ann.get('created_at', '')[:10]}"):
                    st.write(f"**From:** {ann.get('sender_name', 'Unknown')} ({ann.get('sender_role', 'Unknown')})")
                    st.write(f"**Message:** {ann.get('message', 'No message')}")
                    st.write(f"**Target Roles:** {', '.join(ann.get('target_roles', []))}")
                    st.write(f"**Sent:** {ann.get('created_at', 'Unknown')}")
        else:
            st.info("No announcements sent yet.")