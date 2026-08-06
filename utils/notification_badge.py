# utils/notification_badge.py
import streamlit as st
from utils.firebase_db import db

def show_notification_badge(user_id):
    """Show notification badge in sidebar"""
    try:
        notifications = db.get_user_notifications(user_id)
        unread = [n for n in notifications if not n.get('is_read', False)]
        
        if unread:
            st.markdown(f"""
            <div style="background-color: #ff4b4b; color: white; padding: 5px 10px; 
                        border-radius: 20px; display: inline-block; font-size: 12px;
                        font-weight: bold;">
                {len(unread)} new 📨
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("📨 No new notifications")
    except Exception as e:
        st.markdown("📨 Notifications")

def show_notifications(user_id):
    """Show notifications page"""
    st.header("📨 Notifications")
    
    notifications = db.get_user_notifications(user_id)
    
    if not notifications:
        st.info("No notifications.")
        return
    
    # Mark all as read button
    unread = [n for n in notifications if not n.get('is_read', False)]
    if unread:
        if st.button("✅ Mark all as read"):
            db.mark_all_notifications_read(user_id)
            st.rerun()
    
    # Display notifications
    for notif in notifications:
        with st.expander(f"{notif.get('title', 'Notification')} - {notif.get('created_at', '')[:10]}", expanded=not notif.get('is_read', True)):
            st.write(f"**Message:** {notif.get('message', 'No message')}")
            st.write(f"**Sent:** {notif.get('created_at', 'Unknown')}")
            if not notif.get('is_read', False):
                st.caption("🔴 Unread")
            else:
                st.caption("✅ Read")
