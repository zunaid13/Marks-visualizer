import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import norm

st.set_page_config(page_title="Marks Visualizer", layout="wide")

st.title("Marks Visualizer & Analyzer")

# --- GRADING CRITERIA ---
def get_grade_info(marks):
    # According to user's uploaded image
    criteria = [
        (90, 'A', 4.00), (86, 'A-', 3.67), (82, 'B+', 3.33), (78, 'B', 3.00),
        (74, 'B-', 2.67), (70, 'C+', 2.33), (66, 'C', 2.00), (62, 'C-', 1.67),
        (58, 'D+', 1.33), (55, 'D', 1.00), (0, 'F', 0.00)
    ]
    if pd.isna(marks) or marks == 'W':
        return ('W', 0.00, 0) if marks == 'W' else ('I', 0.00, 0)
    
    marks = float(marks)
    for i, (threshold, grade, point) in enumerate(criteria):
        if marks >= threshold:
            next_threshold = criteria[i-1][0] if i > 0 else None
            marks_needed = (next_threshold - marks) if next_threshold else 0
            return (grade, point, max(0, marks_needed))
    return ('F', 0.00, 55 - marks)

# --- SIDEBAR SETTINGS ---
st.sidebar.header("Settings")
handle_w = st.sidebar.radio("How to handle 'W' (Withdrawn) students?", ("Treat as 0", "Drop completely"))
handle_absent = st.sidebar.radio("How to handle Absents/Missing marks?", ("Treat as 0", "Drop completely"))

uploaded_file = st.sidebar.file_uploader("Upload Main Excel File (Marks)", type=["xlsx", "xls"])
secondary_file = st.sidebar.file_uploader("Upload Optional Secondary File (Phone, Email, etc.)", type=["xlsx", "xls"])

def guess_header_row(file_obj):
    try:
        temp_df = pd.read_excel(file_obj, nrows=20, header=None)
        file_obj.seek(0)
        best_row, max_score = 0, 0
        for i, row in temp_df.iterrows():
            non_empty = row.dropna().astype(str).str.strip()
            non_empty = non_empty[non_empty != ""]
            score = len(non_empty)
            if any(kw in str(x).lower() for x in non_empty for kw in ['id', 'name', 'serial', 'roll', 'mark']):
                score += 5
            if score > max_score:
                max_score, best_row = score, i
        return int(best_row)
    except:
        file_obj.seek(0)
        return 0

if uploaded_file is not None:
    guessed_header = guess_header_row(uploaded_file)
    header_row = st.sidebar.number_input(
        "Header Row Index", 
        min_value=0, max_value=20, value=guessed_header, step=1, 
        help="Increase this if your Excel sheet has titles or metadata before the actual column names. If your columns say 'Unnamed: 1', increase this number until the real column names appear."
    )
    
    df_raw = pd.read_excel(uploaded_file, header=header_row)
    # Drop annoying 'Unnamed' and 'Photo' columns
    df_raw = df_raw.loc[:, ~df_raw.columns.astype(str).str.contains('^Unnamed', case=False)]
    df_raw = df_raw.loc[:, ~df_raw.columns.astype(str).str.contains('photo', case=False)]
    
    is_max_marks = False
    if not df_raw.empty:
        first_row_str = " ".join(str(x).lower() for x in df_raw.iloc[0].values)
        if 'max' in first_row_str or 'full' in first_row_str or 'total' in first_row_str:
            is_max_marks = True
            
    drop_first_row = st.sidebar.checkbox("Drop first data row (e.g., if it contains 'Max Marks' instead of a student)", value=is_max_marks)
    
    if drop_first_row and not df_raw.empty:
        df_raw = df_raw.iloc[1:].reset_index(drop=True)
        
    if secondary_file is not None:
        guessed_sec_header = guess_header_row(secondary_file)
        sec_header_row = st.sidebar.number_input(
            "Secondary File Header Row Index", 
            min_value=0, max_value=20, value=guessed_sec_header, step=1,
            help="If your secondary file (e.g., Phone/Email/CGPA) has titles at the top, increase this."
        )
        sec_drop_first_row = st.sidebar.checkbox("Drop first data row of secondary file", value=False)
        
        df_sec = pd.read_excel(secondary_file, header=sec_header_row)
        # Drop annoying 'Unnamed' and 'Photo' columns
        df_sec = df_sec.loc[:, ~df_sec.columns.astype(str).str.contains('^Unnamed', case=False)]
        df_sec = df_sec.loc[:, ~df_sec.columns.astype(str).str.contains('photo', case=False)]
        
        if sec_drop_first_row and not df_sec.empty:
            df_sec = df_sec.iloc[1:].reset_index(drop=True)
        
        st.sidebar.subheader("Merge Files Settings")
        left_merge_col_default = next((c for c in df_raw.columns if 'id' in str(c).lower() or 'serial' in str(c).lower()), df_raw.columns[0])
        right_merge_col_default = next((c for c in df_sec.columns if 'id' in str(c).lower() or 'serial' in str(c).lower()), df_sec.columns[0])
        
        left_merge_col = st.sidebar.selectbox("Main File ID Column", df_raw.columns.tolist(), index=df_raw.columns.tolist().index(left_merge_col_default))
        right_merge_col = st.sidebar.selectbox("Secondary File ID Column", df_sec.columns.tolist(), index=df_sec.columns.tolist().index(right_merge_col_default))
        
        if left_merge_col and right_merge_col:
            # Ensure both merge columns are of the same type (string) and robust against Excel's float formatting (e.g. 1234.0)
            def clean_id(x):
                if pd.isna(x): return ""
                try:
                    return str(int(float(x))).strip()
                except ValueError:
                    return str(x).strip()
                    
            df_raw[left_merge_col] = df_raw[left_merge_col].apply(clean_id)
            df_sec[right_merge_col] = df_sec[right_merge_col].apply(clean_id)
            
            df_raw = pd.merge(df_raw, df_sec, left_on=left_merge_col, right_on=right_merge_col, how='left')
            if left_merge_col != right_merge_col:
                df_raw = df_raw.drop(columns=[right_merge_col])
            st.sidebar.success(f"Merged successfully on {left_merge_col} = {right_merge_col}")
    
    cols = df_raw.columns.tolist()
    
    st.sidebar.subheader("Build Total Marks")
    st.sidebar.markdown("*(e.g., Best 3 of 4 CTs + Mid + Final)*")
    
    st.sidebar.markdown("**1. Class Tests (CT)**")
    default_ct_cols = [c for c in cols if 'ct' in str(c).lower() or 'class test' in str(c).lower()]
    ct_cols = st.sidebar.multiselect("Select CT Columns", cols, default=default_ct_cols)
    best_n_ct = st.sidebar.number_input("Consider Best N CTs", min_value=1, max_value=10, value=3, step=1)
    ct_agg_method = st.sidebar.radio("CT Aggregation Method", ("Average", "Sum"))
    
    st.sidebar.markdown("**2. Other Marks**")
    default_other_cols = [c for c in cols if any(kw in str(c).lower() for kw in ['mid', 'final', 'attendance', 'project', 'assignment']) and c not in default_ct_cols]
    other_cols = st.sidebar.multiselect("Select Other Marks (Mid, Final, Attendance, etc.)", cols, default=default_other_cols)
    
    st.sidebar.subheader("Additional Columns")
    default_cgpa = next((c for c in cols if 'cgpa' in str(c).lower() or 'gpa' in str(c).lower()), None)
    cgpa_col = st.sidebar.selectbox("CGPA Column (for Outlier Detection)", [None] + cols, index=cols.index(default_cgpa) + 1 if default_cgpa else 0)
    
    default_id = next((c for c in cols if 'id' in str(c).lower() or 'serial' in str(c).lower() or 'roll' in str(c).lower()), cols[0])
    id_col = st.sidebar.selectbox("Student ID Column (for Display)", cols, index=cols.index(default_id) if default_id in cols else 0)

    if not (ct_cols or other_cols):
        st.warning("Please select at least one CT column or Other Marks column in the sidebar to calculate Total Marks.")
    else:
        # --- DATA PREPROCESSING ---
        df = df_raw.copy()
        mark_cols = ct_cols + other_cols
        
        df['Status'] = 'Regular'
        
        # Clean 'W' and 'Absent'
        for col in mark_cols:
            if df[col].dtype == object:
                # Handle W first before coercing to numeric
                w_mask = df[col].astype(str).str.lower().str.strip() == 'w'
                df.loc[w_mask, 'Status'] = 'W'
                
                if handle_w == "Treat as 0":
                    df.loc[w_mask, col] = 0
                else:
                    df = df[~w_mask]
                    
            # Coerce everything to numeric. Any random text ('Absent', 'sick', 'A', etc.) becomes NaN.
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Now handle all the NaNs (which includes empty cells and the text we just coerced)
            if handle_absent == "Treat as 0":
                df[col] = df[col].fillna(0)
            else:
                nan_count = df[col].isna().sum()
                if nan_count > 0.8 * len(df) and len(df) > 0:
                    st.warning(f"Column '{col}' is mostly empty (has this exam taken place yet?). Treating as 0 to avoid deleting everyone from the list.")
                    df[col] = df[col].fillna(0)
                else:
                    df = df.dropna(subset=[col])

        # Calculate CT Component
        if ct_cols:
            def calc_ct(row):
                vals = row[ct_cols].dropna().tolist()
                if len(vals) == 0: return 0
                vals.sort()
                top_n = vals[-int(best_n_ct):] # Get best N
                if ct_agg_method == "Average":
                    return sum(top_n) / len(top_n) if len(top_n) > 0 else 0
                else:
                    return sum(top_n)
            
            df['CT_Component'] = df.apply(calc_ct, axis=1)
        else:
            df['CT_Component'] = 0
            
        # Calculate Calculated_Total
        df['Calculated_Total'] = df['CT_Component']
        for col in other_cols:
            df['Calculated_Total'] += df[col].fillna(0)
            
        total_col = 'Calculated_Total'
        
        # If user selected CTs, we want to show the CT component in the stats as well
        if ct_cols:
            mark_cols.append('CT_Component')
        mark_cols.append(total_col)

        # Calculate Grades based on Total
        if total_col:
            def get_grade_with_status(row):
                if row['Status'] == 'W':
                    return ('W', 0.00, 0)
                return get_grade_info(row[total_col])
                
            grade_info = df.apply(get_grade_with_status, axis=1)
            df['Grade'] = grade_info.apply(lambda x: x[0])
            df['Grade Point'] = grade_info.apply(lambda x: x[1])
            df['Marks Needed For Next Grade'] = grade_info.apply(lambda x: x[2]).round(2)
        
        # --- UI DISPLAY ---
        st.header("1. Overview Data")
        st.dataframe(df.head(10))
        
        st.header("2. Statistics Summary")
        stats_df = pd.DataFrame(index=['Mean', 'Median', 'Max', 'Min', 'Variance', 'Std Dev'])
        for col in mark_cols:
            stats_df[col] = [
                df[col].mean(), df[col].median(), df[col].max(), df[col].min(),
                df[col].var(), df[col].std()
            ]
        st.dataframe(stats_df.round(2).T)
        
        st.header("3. Student Rankings")
        ranking_col = st.selectbox("Select Column for Rankings", mark_cols, index=len(mark_cols)-1)
        col1, col2 = st.columns(2)
        if ranking_col:
            with col1:
                st.subheader(f"Top 5 ({ranking_col})")
                st.dataframe(df.nlargest(5, ranking_col)[[id_col, ranking_col] + (['Grade'] if ranking_col == total_col else [])])
            with col2:
                st.subheader(f"Bottom 5 ({ranking_col})")
                st.dataframe(df.nsmallest(5, ranking_col)[[id_col, ranking_col] + (['Grade'] if ranking_col == total_col else [])])
                
            st.subheader(f"Closest to Average ({ranking_col})")
            avg_val = df[ranking_col].mean()
            df['Dist_From_Avg_Temp'] = abs(df[ranking_col] - avg_val)
            st.dataframe(df.nsmallest(5, 'Dist_From_Avg_Temp')[[id_col, ranking_col] + (['Grade'] if ranking_col == total_col else [])])
            
        # --- STUDENT LOOKUP ---
        st.header("4. Specific Student Lookup")
        search_id = st.text_input("Enter Student ID to view their full profile")
        if search_id:
            student_data = df[df[id_col].astype(str).str.strip().str.lower() == str(search_id).strip().lower()]
            if not student_data.empty:
                st.success(f"Found Data for Student: {search_id}")
                st.dataframe(student_data)
                
                # Render comparative bar chart
                student_marks = student_data[mark_cols].iloc[0]
                class_avgs = df[mark_cols].mean()
                comp_df = pd.DataFrame({
                    'Exam/Test': mark_cols,
                    'Student Score': student_marks.values,
                    'Class Average': class_avgs.values
                })
                comp_melted = comp_df.melt(id_vars='Exam/Test', var_name='Metric', value_name='Marks')
                fig_comp = px.bar(comp_melted, x='Exam/Test', y='Marks', color='Metric', barmode='group', title=f"Performance of {search_id} vs Class Average", text_auto='.1f')
                st.plotly_chart(fig_comp, use_container_width=True)
            else:
                st.error("Student ID not found.")
            
        # --- VISUALIZATIONS ---
        st.header("5. Visualizations")
        
        # CT Averages Visualization
        if ct_cols:
            st.subheader("Class Average per Class Test")
            ct_avgs = df[ct_cols].mean().reset_index()
            ct_avgs.columns = ['Class Test', 'Average Mark']
            fig_ct = px.bar(ct_avgs, x='Class Test', y='Average Mark', title="Class Average for Each CT", text_auto='.2f')
            st.plotly_chart(fig_ct, use_container_width=True)
            
        st.subheader("Distribution Analysis")
        viz_col = st.selectbox("Select Column for Bell Curve", mark_cols)
        
        if viz_col:
            data = df[viz_col].dropna()
            mean = data.mean()
            std = data.std()
            
            fig = go.Figure()
            # Histogram
            fig.add_trace(go.Histogram(x=data, histnorm='probability density', name='Data Distribution', opacity=0.7))
            
            # Bell Curve (Normal Distribution)
            if std > 0:
                x_axis = np.linspace(data.min(), data.max(), 100)
                y_axis = norm.pdf(x_axis, mean, std)
                fig.add_trace(go.Scatter(x=x_axis, y=y_axis, mode='lines', name='Normal Distribution (Bell Curve)'))
                
            fig.update_layout(title=f"Distribution of {viz_col}", xaxis_title=viz_col, yaxis_title="Density")
            st.plotly_chart(fig, use_container_width=True)
            
        # --- OUTLIER DETECTION ---
        st.header("6. Outlier Detection (Unnatural Performance)")
        st.info("Highlights students whose current marks significantly deviate from their historical CGPA trend.")
        if cgpa_col and total_col:
            # Ensure CGPA is strictly numeric to avoid crashes during Outlier Detection math
            df[cgpa_col] = pd.to_numeric(df[cgpa_col], errors='coerce')
            
            # Only calculate outliers for students who actually have a valid CGPA
            valid_df = df.dropna(subset=[cgpa_col, total_col]).copy()
            
            if not valid_df.empty:
                cgpa_std = valid_df[cgpa_col].std()
                total_std = valid_df[total_col].std()
                
                if cgpa_std > 0 and total_std > 0:
                    # Simple Outlier detection using Z-Scores
                    valid_df['Z_CGPA'] = (valid_df[cgpa_col] - valid_df[cgpa_col].mean()) / cgpa_std
                    valid_df['Z_Total'] = (valid_df[total_col] - valid_df[total_col].mean()) / total_std
                    
                    # If Z_Total is much higher than Z_CGPA (e.g., diff > 1.5) => suspicious improvement
                    # If Z_Total is much lower than Z_CGPA => suspicious drop
                    valid_df['Outlier Score'] = valid_df['Z_Total'] - valid_df['Z_CGPA']
                    
                    valid_df['Status'] = 'Normal'
                    valid_df.loc[valid_df['Outlier Score'] > 1.5, 'Status'] = 'Suspiciously High'
                    valid_df.loc[valid_df['Outlier Score'] < -1.5, 'Status'] = 'Suspiciously Low'
                    
                    outliers = valid_df[valid_df['Status'] != 'Normal']
                    if not outliers.empty:
                        st.warning(f"Found {len(outliers)} students with anomalous performance!")
                        st.dataframe(outliers[[id_col, cgpa_col, total_col, 'Outlier Score', 'Status']].sort_values('Outlier Score', ascending=False))
                        
                        # Highlight in Scatter Plot
                        fig_out = px.scatter(valid_df, x=cgpa_col, y=total_col, color='Status', 
                                             hover_data=[id_col], title="Outliers in Total Marks vs CGPA",
                                             color_discrete_map={'Normal': 'gray', 'Suspiciously High': 'red', 'Suspiciously Low': 'orange'})
                        st.plotly_chart(fig_out, use_container_width=True)
                    else:
                        st.success("No significant outliers detected.")
                else:
                    st.info("Not enough variation in data to detect outliers (Standard Deviation is 0).")
            else:
                st.warning("No valid CGPA data found to perform outlier detection.")
else:
    st.info("Please upload an Excel file to get started.")
