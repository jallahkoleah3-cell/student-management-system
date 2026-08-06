import streamlit as st
from utils.firebase_db import db
import plotly.express as px
import pandas as pd

def show(user):
    st.header("📊 Admin Dashboard")
    
    # Get statistics
    students = db.get_all_students()
    teachers = db.get_all_users(role='Teacher')
    parents = db.get_all_users(role='Parent')
    
    # Statistics cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👨‍🎓 Total Students", len(students))
    col2.metric("👨‍🏫 Total Teachers", len(teachers))
    col3.metric("👨‍👩‍👦 Total Parents", len(parents))
    col4.metric("📚 Total Classes", "0")  # Add class count later
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        if students:
            # Grade distribution
            grades = [s.get('grade', 'Unknown') for s in students if s.get('grade')]
            if grades:
                grade_counts = pd.Series(grades).value_counts().reset_index()
                grade_counts.columns = ['Grade', 'Count']
                fig = px.bar(grade_counts, x='Grade', y='Count', title="Student Distribution by Grade")
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if students:
            # Gender distribution
            genders = [s.get('gender', 'Unknown') for s in students if s.get('gender')]
            if genders:
                gender_counts = pd.Series(genders).value_counts().reset_index()
                gender_counts.columns = ['Gender', 'Count']
                fig = px.pie(gender_counts, values='Count', names='Gender', title="Gender Distribution")
                st.plotly_chart(fig, use_container_width=True)
    
    # Recent activity
    st.subheader("📋 Recent Activity")
    st.info("Activity log coming soon!")