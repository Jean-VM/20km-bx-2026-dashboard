
import streamlit as st
import pandas as pd
import json
import re
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# --- Data Loading and Preprocessing ---

# Helper function to parse time strings like 'H:MM:SS' or 'MM:SS' and handle HTML
def parse_time_string(time_value):
    if time_value is None or (isinstance(time_value, str) and (time_value.strip() == '-' or time_value.strip() == '')):
        return None

    time_str = str(time_value) # Ensure it's a string

    # First, try to extract time from HTML like '<b>0:59:47</b><br/>...'
    # Regex adjusted to match optional hours more flexibly and correctly capture the time part
    html_time_match = re.search(r'<b>(?:(\d+):)?([0-5]?\d):([0-5]?\d)</b>', time_str)
    if html_time_match:
        h = int(html_time_match.group(1)) if html_time_match.group(1) else 0
        m = int(html_time_match.group(2))
        s = int(html_time_match.group(3))
        return f"{h:02}:{m:02}:{s:02}"

    # Then parse the time string (e.g., 'H:MM:SS' or 'MM:SS')
    parts = time_str.split(':')
    if len(parts) == 3: # H:MM:SS
        try:
            h = int(parts[0])
            m = int(parts[1])
            s = int(parts[2])
            return f"{h:02}:{m:02}:{s:02}"
        except ValueError:
            return None
    elif len(parts) == 2: # MM:SS (assuming 0 hours)
        try:
            m = int(parts[0])
            s = int(parts[1])
            return f"00:{m:02}:{s:02}"
        except ValueError:
            return None
    else:
        return None # Unrecognized format or not a time string

# Function to convert 'HH:MM:SS' string to total seconds
def time_to_seconds(time_str):
    if pd.isna(time_str) or time_str is None:
        return np.nan
    parts = str(time_str).split(':')
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return np.nan

# Function to convert seconds back to 'HH:MM:SS' for display
def seconds_to_hms(total_seconds):
    if pd.isna(total_seconds):
        return 'N/A'
    total_seconds = int(total_seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"


@st.cache_data # Cache data loading and processing
def load_and_process_data(file_path):
    # FIX: Specify utf-8 encoding to handle UnicodeDecodeError
    with open(file_path, 'r', encoding='utf-8') as f:
        json_content = json.load(f)

    if 'Groups' in json_content and isinstance(json_content['Groups'], list):
        df = pd.DataFrame(json_content['Groups'])
    else:
        st.error("Could not find 'Groups' key or its content is not a list. Please inspect the JSON structure manually.")
        st.stop()

    if not df.empty and 'SlaveRows' in df.columns and len(df['SlaveRows'].iloc[0]) > 0:
        all_runners_data = df['SlaveRows'].iloc[0]

        processed_data = []
        for runner_entry in all_runners_data:
            if len(runner_entry) >= 14:
                gender = runner_entry[2]
                html_data_name_age = runner_entry[3]

                name_match = re.search(r'<b>(.*?)</b>', html_data_name_age)
                name = name_match.group(1) if name_match else None

                year_match = re.search(r'<small>.*?(\b\d{4})\b.*?</small>', html_data_name_age)
                if not year_match:
                     year_match = re.search(r'\b(\d{4})\b', html_data_name_age)

                year_of_birth = int(year_match.group(1)) if year_match else None

                time_5km_raw = runner_entry[7]
                time_10km_raw = runner_entry[9]
                time_15km_raw = runner_entry[11]
                finish_time_raw = runner_entry[13]

                processed_data.append({
                    'Name': name,
                    'Gender': gender,
                    'Year_of_Birth': year_of_birth, # Still extract, but won't be used for age filter
                    'Time_5km': parse_time_string(time_5km_raw),
                    'Time_10km': parse_time_string(time_10km_raw),
                    'Time_15km': parse_time_string(time_15km_raw),
                    'Finish_Time': parse_time_string(finish_time_raw)
                })

        runners_df = pd.DataFrame(processed_data)

        runners_df['Time_5km_sec'] = runners_df['Time_5km'].apply(time_to_seconds)
        runners_df['Time_10km_sec'] = runners_df['Time_10km'].apply(time_to_seconds)
        runners_df['Time_15km_sec'] = runners_df['Time_15km'].apply(time_to_seconds)
        runners_df['Finish_Time_sec'] = runners_df['Finish_Time'].apply(time_to_seconds)

        # Removed: Age calculation and Year_of_Birth cleanup

        # Calculate gender-specific average times
        average_times_by_gender = runners_df.groupby('Gender')[['Time_5km_sec', 'Time_10km_sec', 'Time_15km_sec', 'Finish_Time_sec']].mean()
        
        return runners_df, average_times_by_gender
    else:
        st.error("Could not process SlaveRows. DataFrame might be empty or 'SlaveRows' column is missing/empty.")
        st.stop()


# --- Streamlit App Layout ---
st.set_page_config(layout="wide", page_title="Brussels 20km Race Analysis")

st.title("🏃‍♀️ Brussels 20km Race Analysis Dashboard 🏃‍♂️")
st.markdown("---")

# Load data (cached for performance)
file_path = 'brussels_20km_2026.json'
runners_df, average_times_by_gender = load_and_process_data(file_path)

# Removed: Age Filter section
# Removed: filtered_runners_df and filtered_average_times_by_gender
# All subsequent operations will use the main runners_df and average_times_by_gender


# --- Runner Comparison Section ---
st.header("Individual Runner Performance Comparison")
st.write("Enter a runner's name to see how they compare against the gender average for each split.")

runner_name_input = st.text_input("Enter Runner's Name:", placeholder="e.g., Patrick NIMUBONA")

if runner_name_input:
    # Use the main runners_df, no age filter applied
    runner_data = runners_df[runners_df['Name'].str.lower() == runner_name_input.lower()]

    if runner_data.empty:
        st.warning(f"Runner '{runner_name_input}' not found. Please check spelling.")
    else:
        # Handle multiple runners with the same name
        if len(runner_data) > 1:
            st.info(f"Multiple runners found for '{runner_name_input}'. Displaying the first match.")
            for index, row in runner_data.iterrows():
                st.write(f"- **Name:** {row['Name']}, **Gender:** {row['Gender']}, **Year of Birth:** {row['Year_of_Birth'] if pd.notna(row['Year_of_Birth']) else 'N/A'}")
            st.markdown("--- This comparison uses the first listed runner. ---")
            runner = runner_data.iloc[0]
        else:
            runner = runner_data.iloc[0]
        
        gender = runner['Gender']
        st.subheader(f"Comparison for {runner['Name']} ({'Male' if gender == 'M' else 'Female'})")

        if gender not in average_times_by_gender.index:
            st.error(f"Average times for gender '{gender}' not available.")
        else:
            avg_times = average_times_by_gender.loc[gender]

            comparison_data = []
            times_to_compare = {
                '5km': ('Time_5km', 'Time_5km_sec'),
                '10km': ('Time_10km', 'Time_10km_sec'),
                '15km': ('Time_15km', 'Time_15km_sec'),
                'Finish': ('Finish_Time', 'Finish_Time_sec')
            }

            for label, (time_col, sec_col) in times_to_compare.items():
                runner_time_hms = runner[time_col]
                runner_time_sec = runner[sec_col]
                avg_time_sec = avg_times[sec_col]

                diff_display = 'N/A'
                
                if not pd.isna(runner_time_sec) and not pd.isna(avg_time_sec):
                    difference_sec = runner_time_sec - avg_time_sec
                    
                    # Convert absolute difference to HH:MM:SS format
                    abs_diff_sec = abs(difference_sec)
                    diff_hms = seconds_to_hms(abs_diff_sec)

                    if difference_sec < 0: # Runner is faster (better)
                        diff_display = f"- {diff_hms} (Faster)"
                    elif difference_sec > 0: # Runner is slower (worse)
                        diff_display = f" (+{diff_hms} Slower)"
                    else:
                        diff_display = "No Difference"
                
                avg_time_hms = seconds_to_hms(avg_time_sec)
                
                comparison_data.append({
                    'Distance': label,
                    'Your Time': runner_time_hms if pd.notna(runner_time_hms) else 'N/A',
                    f'Avg. {gender} Time': avg_time_hms,
                    'Difference': diff_display
                })
            
            st.table(pd.DataFrame(comparison_data))

            st.markdown("---")

            # --- New section for Bell Curve and Performance Comments ---
            st.subheader("Your Performance on the Distribution Curve")

            # Filter data for the runner's gender only
            gender_filtered_df = runners_df[runners_df['Gender'] == gender].copy()

            # Columns for analysis
            time_cols_for_bell_curve = {
                '5km': 'Time_5km_sec',
                '10km': 'Time_10km_sec',
                '15km': 'Time_15km_sec',
                'Finish (20km)': 'Finish_Time_sec'
            }

            for distance_label, sec_col in time_cols_for_bell_curve.items():
                runner_time_sec = runner[sec_col]

                if pd.isna(runner_time_sec):
                    st.info(f"Cannot plot for {distance_label} as your time is not available.")
                    continue

                # Drop NaNs for the current distance to calculate percentile correctly
                distribution = gender_filtered_df[sec_col].dropna()

                if distribution.empty:
                    st.info(f"No data available for {distance_label} for your gender to create a distribution plot.")
                    continue

                # Calculate percentile rank (smaller time = better)
                faster_runners_count = (distribution < runner_time_sec).sum()
                total_runners = len(distribution)
                percentage_faster = (faster_runners_count / total_runners) * 100 if total_runners > 0 else 0
                percentage_slower = 100 - percentage_faster

                # Plotting the distribution
                fig, ax = plt.subplots(figsize=(10, 5))
                sns.histplot(distribution.apply(lambda x: x / 60), kde=True, bins=30, ax=ax, color='skyblue', stat='density', alpha=0.7)
                
                # Mark runner's time
                runner_time_min = runner_time_sec / 60
                ax.axvline(runner_time_min, color='red', linestyle='--', label=f'Your Time: {seconds_to_hms(runner_time_sec)}')
                
                # Add shaded area for faster runners
                min_dist_val = distribution.min() / 60
                ax.fill_betweenx([0, ax.get_ylim()[1]], min_dist_val, runner_time_min, color='red', alpha=0.1, label=f'In the top {percentage_faster:.1f}%')

                ax.set_title(f'{distance_label} Time Distribution for {gender} Runners')
                ax.set_xlabel(f'{distance_label} Time (Minutes)')
                ax.set_ylabel('Density')
                ax.legend()
                st.pyplot(fig)

                # Performance comment
                st.write(f"**{distance_label} Performance:**")
                if percentage_faster <= 10:
                    st.success(f"🎉 Excellent! You were in the top {percentage_faster:.1f}% of  fastest {gender} runners at {distance_label}.")
                elif percentage_faster <= 25:
                    st.success(f"💪 Great Job! You were in the top {percentage_faster:.1f}% fastest {gender} runners at {distance_label}.")
                elif percentage_faster <= 50:
                    st.info(f"👍 Solid performance! You were in the top {percentage_faster:.1f}% fastest {gender} runners at {distance_label}.")
                else:
                    st.warning(f"Keep pushing!")
                st.markdown("---")


# --- Overall Performance Visualizations ---
st.header("Overall Race Performance Visualizations")

# Overall Distribution of Finish Times
st.subheader("Distribution of Finish Times")
fig1, ax1 = plt.subplots(figsize=(12, 6))
sns.histplot(runners_df['Finish_Time_sec'].dropna().apply(lambda x: x / 60), kde=True, bins=50, ax=ax1)
ax1.set_title('Distribution of Finish Times (Minutes)')
ax1.set_xlabel('Finish Time (Minutes)')
ax1.set_ylabel('Number of Runners')
st.pyplot(fig1)

# Distribution by Gender
st.subheader("Finish Time Distribution by Gender")
fig2, ax2 = plt.subplots(figsize=(14, 7))
sns.histplot(data=runners_df, x=runners_df['Finish_Time_sec'].apply(lambda x: x / 60), hue='Gender', kde=True, bins=50, palette='viridis', alpha=0.7, ax=ax2)
ax2.set_title('Distribution of Finish Times by Gender (Minutes)')
ax2.set_xlabel('Finish Time (Minutes)')
ax2.set_ylabel('Number of Runners')
ax2.legend(title='Gender')
st.pyplot(fig2)

# Box Plot of Split Times by Gender
st.subheader("Split Times by Gender")
fig3, axes3 = plt.subplots(1, 3, figsize=(20, 6), sharey=True)

sns.boxplot(data=runners_df, x='Gender', y=runners_df['Time_5km_sec'].apply(lambda x: x / 60), ax=axes3[0], palette='pastel')
axes3[0].set_title('5km Split Time (Minutes)')
axes3[0].set_xlabel('Gender')
axes3[0].set_ylabel('Time (Minutes)')

sns.boxplot(data=runners_df, x='Gender', y=runners_df['Time_10km_sec'].apply(lambda x: x / 60), ax=axes3[1], palette='pastel')
axes3[1].set_title('10km Split Time (Minutes)')
axes3[1].set_xlabel('Gender')
axes3[1].set_ylabel('') # Share y-axis label with first plot

sns.boxplot(data=runners_df, x='Gender', y=runners_df['Time_15km_sec'].apply(lambda x: x / 60), ax=axes3[2], palette='pastel')
axes3[2].set_title('15km Split Time (Minutes)')
axes3[2].set_xlabel('Gender')
axes3[2].set_ylabel('') # Share y-axis label with first plot

plt.tight_layout()
st.pyplot(fig3)
