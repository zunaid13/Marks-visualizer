import pandas as pd
import numpy as np

def generate_sample_data():
    np.random.seed(42)
    
    num_students = 100
    
    data = {
        'Serial Number': range(1, num_students + 1),
        'Name': [f'Student_{i}' for i in range(1, num_students + 1)],
        'Email': [f'student{i}@example.com' for i in range(1, num_students + 1)],
        'Phone': [f'555-01{str(i).zfill(2)}' for i in range(1, num_students + 1)],
        'Section': np.random.choice(['A', 'B', 'C'], num_students),
        'CGPA': np.round(np.random.normal(3.0, 0.5, num_students), 2),
        'Mid': np.round(np.random.normal(20, 5, num_students), 1), # Out of 30
        'Final': np.round(np.random.normal(25, 8, num_students), 1), # Out of 40
        'Project': np.round(np.random.normal(25, 4, num_students), 1) # Out of 30
    }
    
    # Clip values
    data['CGPA'] = np.clip(data['CGPA'], 0.0, 4.0)
    data['Mid'] = np.clip(data['Mid'], 0, 30)
    data['Final'] = np.clip(data['Final'], 0, 40)
    data['Project'] = np.clip(data['Project'], 0, 30)
    
    df = pd.DataFrame(data)
    
    # Calculate Total initially
    df['Total'] = df['Mid'] + df['Final'] + df['Project']
    
    # Cast columns to object to allow mixing floats and strings
    df['Mid'] = df['Mid'].astype(object)
    df['Final'] = df['Final'].astype(object)
    df['Project'] = df['Project'].astype(object)
    df['Total'] = df['Total'].astype(object)
    
    # Inject some 'W' (Withdrawn) students
    w_indices = np.random.choice(df.index, 5, replace=False)
    for idx in w_indices:
        df.loc[idx, 'Mid'] = 'W'
        df.loc[idx, 'Final'] = 'W'
        df.loc[idx, 'Project'] = 'W'
        df.loc[idx, 'Total'] = 'W'
        
    # Inject some 'Absent' students
    a_indices = np.random.choice(df.index.difference(w_indices), 8, replace=False)
    for idx in a_indices:
        # Some are absent in mid
        if np.random.rand() > 0.5:
            df.loc[idx, 'Mid'] = 'Absent'
        else:
            df.loc[idx, 'Final'] = np.nan
            
    # Re-calculate Total for non-W students just in case (leaving absents/NaNs as is to let the main script handle them)
    # Actually, let's leave Total empty or pre-calculated and let the app handle it, or just provide raw data.
    # The app will recalculate total if some are missing or 'Absent'.
    
    # Inject some outliers
    outlier_indices = np.random.choice(df.index.difference(np.union1d(w_indices, a_indices)), 3, replace=False)
    
    # Outlier 1: Low CGPA, very high marks
    df.loc[outlier_indices[0], 'CGPA'] = 1.8
    df.loc[outlier_indices[0], 'Mid'] = 29
    df.loc[outlier_indices[0], 'Final'] = 39
    
    # Outlier 2: High CGPA, very low marks
    df.loc[outlier_indices[1], 'CGPA'] = 3.9
    df.loc[outlier_indices[1], 'Mid'] = 5
    df.loc[outlier_indices[1], 'Final'] = 8
    
    # Outlier 3: Another low CGPA, high marks
    df.loc[outlier_indices[2], 'CGPA'] = 2.1
    df.loc[outlier_indices[2], 'Mid'] = 30
    df.loc[outlier_indices[2], 'Final'] = 38
    
    df.to_excel('sample_data.xlsx', index=False)
    print("sample_data.xlsx generated successfully.")

if __name__ == '__main__':
    generate_sample_data()
