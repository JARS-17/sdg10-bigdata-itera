import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def render_demographics(sex_df: pd.DataFrame, emp_df: pd.DataFrame, edu_df: pd.DataFrame, age_df: pd.DataFrame):
    st.subheader("📊 Analisis Demografi")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Donut Chart: Status Ketenagakerjaan
        st.markdown("#### Status Ketenagakerjaan")
        if not emp_df.empty:
            fig_emp = px.pie(
                emp_df, 
                values='weighted_count', 
                names='empstat_label', 
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_emp.update_traces(textposition='inside', textinfo='percent+label')
            fig_emp.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=False)
            st.plotly_chart(fig_emp, use_container_width=True)
        else:
            st.info("Data tidak tersedia.")
            
        # Bar Chart: Distribusi Usia
        st.markdown("#### Distribusi Usia")
        if not age_df.empty:
            # Urutkan berdasarkan age_group
            age_df = age_df.sort_values(by="age_group")
            fig_age = px.bar(
                age_df,
                x='age_group',
                y='weighted_count',
                labels={'age_group': 'Kelompok Usia', 'weighted_count': 'Populasi (Tertimbang)'},
                color_discrete_sequence=['#4f8ef7']
            )
            fig_age.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_age, use_container_width=True)
        else:
            st.info("Data tidak tersedia.")

    with col2:
        # Bar Chart: Tingkat Pendidikan
        st.markdown("#### Tingkat Pendidikan")
        if not edu_df.empty:
            # Urutan kustom untuk pendidikan
            edu_order = ["Tdk Tamat SD", "SD/Sederajat", "SMA/Sederajat", "Perguruan Tinggi", "Lainnya"]
            edu_df['education_label'] = pd.Categorical(edu_df['education_label'], categories=edu_order, ordered=True)
            edu_df = edu_df.sort_values(by='education_label')
            
            fig_edu = px.bar(
                edu_df,
                y='education_label',
                x='weighted_count',
                orientation='h',
                labels={'education_label': 'Pendidikan', 'weighted_count': 'Populasi (Tertimbang)'},
                color_discrete_sequence=['#4cb2a2']
            )
            fig_edu.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_edu, use_container_width=True)
        else:
            st.info("Data tidak tersedia.")
            
        # Donut Chart: Jenis Kelamin
        st.markdown("#### Distribusi Jenis Kelamin")
        if not sex_df.empty:
            fig_sex = px.pie(
                sex_df, 
                values='weighted_count', 
                names='sex_label', 
                hole=0.5,
                color_discrete_sequence=['#ff9f43', '#ee5253']
            )
            fig_sex.update_traces(textposition='inside', textinfo='percent+label')
            fig_sex.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=False)
            st.plotly_chart(fig_sex, use_container_width=True)
        else:
            st.info("Data tidak tersedia.")
