# utils/pages/student_announcements.py
import streamlit as st
from datetime import datetime
from utils.firebase_db import db

def show(user):
    st.header("📢 Announcements")
    
    announcements = db.get_announcements_for_user(
        user_id=user.get('uid'),
        user_role='Student'
    )
    
    if not announcements:
        st.info("📭 No announcements yet.")
        return
    
    # Mark all as read button
    unread = [a for a in announcements if not a.get('is_read', False)]
    if unread:
        if st.button(f"✅ Mark all as read ({len(unread)} unread)"):
            for a in announcements:
                if a.get('notification_id'):
                    db.mark_notification_read(a['notification_id'])
            st.rerun()
    
    # Display announcements
    st.subheader(f"📬 {len(announcements)} Announcements")
    
    for ann in announcements:
        is_read = ann.get('is_read', False)
        
        # Show unread with different style
        if not is_read:
            st.markdown(f"**🔴 NEW:** {ann.get('title', 'No title')}")
        else:
            st.markdown(f"**📨:** {ann.get('title', 'No title')}")
        
        with st.expander(f"{ann.get('title', 'No title')} - {ann.get('created_at', '')[:10]}", expanded=not is_read):
            st.write(f"**From:** {ann.get('sender_name', 'Unknown')} ({ann.get('sender_role', 'Unknown')})")
            st.write(f"**Message:** {ann.get('message', 'No message')}")
            st.write(f"**Sent:** {ann.get('created_at', 'Unknown')}")
            
            if not is_read:
                if st.button(f"✅ Mark as Read", key=f"read_{ann['id']}"):
                    db.mark_notification_read(ann['notification_id'])
                    st.rerun()
            else:
                st.caption("✅ Read")
    
    # Stats
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Announcements", len(announcements))
    with col2:
        st.metric("Unread", len(unread))