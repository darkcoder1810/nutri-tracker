import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from utils import (calculate_calories, calculate_macros, load_food_database,
                   save_food_to_database, calculate_calories_from_macros,
                   food_exists_in_database)
from sheets_db import load_user_info, save_user_info, save_meal_log, get_daily_logs, delete_logs_by_date_range, get_daily_summaries
import time

import pytz

# Prepare row data
ist_tz = pytz.timezone('Asia/Kolkata')  # Define the IST timezone

# Page configuration
st.set_page_config(page_title="Calorie Tracker", layout="wide")

# Add this CSS injection after page config
st.markdown("""
    <style>
    /* Ensure columns stay side by side on mobile */
    @media (max-width: 640px) {
        div[data-testid="column"] {
            width: calc(50% - 1rem) !important;
            flex: 1 1 calc(50% - 1rem) !important;
            min-width: calc(50% - 1rem) !important;
        }
    }

    /* Style metric containers */
    div[data-testid="metric-container"] {
        background-color: rgba(28, 131, 225, 0.1);
        border: 1px solid rgba(28, 131, 225, 0.1);
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.25rem 0;
    }
    /* Custom styling for metrics grid */
    .metrics-grid-container {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        padding: 1rem;
        width: 100%;
        justify-content: center;
    }

    div[data-testid="metric-container"] {
        width: 200px !important;
        flex: 0 0 200px !important;
        background-color: rgba(28, 131, 225, 0.1);
        border: 1px solid rgba(28, 131, 225, 0.1);
        border-radius: 5px;
        padding: 1rem;
        margin: 0.5rem !important;
        transition: all 0.3s ease;
    }

    div[data-testid="metric-container"]:hover {
        background-color: rgba(28, 131, 225, 0.2);
        transform: translateY(-2px);
    }

    div[data-testid="metric-container"] > div {
        text-align: center;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
        font-weight: bold !important;
    }

    div[data-testid="stMetricDelta"] {
        font-size: 0.8rem !important;
    }
    </style>
""",
            unsafe_allow_html=True)

# Load custom CSS
with open('.streamlit/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize session states
if 'daily_log' not in st.session_state:
    st.session_state.daily_log = {
        'breakfast': [],
        'lunch': [],
        'snacks': [],
        'dinner': []
    }

if 'user_info' not in st.session_state:
    st.session_state.user_info = {}

if 'mobile_verified' not in st.session_state:
    st.session_state.mobile_verified = False

# Mobile number verification section
if not st.session_state.mobile_verified:
    st.title("Welcome to NutriTracker")
    st.subheader("Please enter your mobile number to login :")

    mobile = st.text_input("Mobile Number",
                           max_chars=10)  # Limit to 10 characters
    if st.button("Continue", key="continue_mobile"):
        if not mobile:
            st.error("Please enter a mobile number")
        elif not mobile.isdigit() or len(
                mobile) != 10:  # Ensure only digits and length
            st.error(
                "Please enter a valid mobile number with exactly 10 digits.")
        else:
            st.session_state.mobile = mobile
            user_data = load_user_info()

            if user_data:
                st.session_state.user_info = user_data
                st.session_state.mobile_verified = True
                st.rerun()
            else:
                st.warning(
                    "No existing data found. Please enter your information.")
                st.switch_page("pages/user_info.py")

# Main application
elif st.session_state.mobile_verified:
    # Add tabs for navigation
    tabs = st.tabs(
        ["🏠 Home", "➕ Add Food", "📊 Daily Log", "👨🏾‍💻 About Developer"])

    with tabs[0]:  # Home tab
        #st.header("Welcome to NutriTracker")
        st.header("🥗 Calorie & Macro Tracker")
        # Rest of the home content
        # Load food database
        food_db = load_food_database()

        # Main title
        #st.title("🥗 Calorie & Macro Tracker")

        # Sidebar for user info and goals
        with st.sidebar:
            #st.header("User Information", )
            animated_css = """
            <style>
                .hover-header:hover {
                    color: #FF4B4B;
                    transition: color 0.3s ease;
                }
            </style>
            """
            st.markdown(animated_css, unsafe_allow_html=True)
            st.markdown("<h2 class='hover-header'>💀 User Information</h2>",
                        unsafe_allow_html=True)

            full_name = st.session_state.user_info.get('full_name', 'iHacK')
            st.write(f"Name: {full_name}")  # Displaying Full Name
            weight = st.session_state.user_info.get('weight', 70.0)
            # Update mobile in user_info if not present
            if 'mobile' not in st.session_state.user_info and 'mobile' in st.session_state:
                st.session_state.user_info['mobile'] = st.session_state.mobile

            st.write(f"Weight: {weight} kg")

            # Sign Out Button
            if st.button("Sign Out"):
                # Resetting the session state
                st.session_state.mobile_verified = False
                st.session_state.mobile = None
                st.session_state.user_info = {}
                st.session_state.daily_log = {
                    'breakfast': [],
                    'lunch': [],
                    'snacks': [],
                    'dinner': []
                }
                st.success("You have been signed out.")
                time.sleep(2)
                st.rerun()  # Refresh the app

            # Initialize session state for user_info if not present
            if 'user_info' not in st.session_state:
                st.session_state.user_info = {}
            # Set default values if not already defined
            if 'calorie_mode' not in st.session_state.user_info:
                st.session_state.user_info[
                    'calorie_mode'] = 'maintenance'  # Default value
            if 'protein_per_kg' not in st.session_state.user_info:
                st.session_state.user_info[
                    'protein_per_kg'] = 1.8  # Default value
            if 'fat_percent' not in st.session_state.user_info:
                st.session_state.user_info[
                    'fat_percent'] = 0.25  # Default value
            # Load user information from the database
            loaded_user_info = load_user_info()
            if loaded_user_info:
                st.session_state.user_info.update(loaded_user_info)
            # Ensure that weight is set for calculations
            weight = st.session_state.user_info.get('weight', 70.0)
            calorie_mode = st.session_state.user_info['calorie_mode']
            protein_per_kg = st.session_state.user_info['protein_per_kg']
            fat_percent = st.session_state.user_info[
                'fat_percent']  # Accessing calorie_mode correctly

            # Calculate target calories based on mode
            target_calories = calculate_calories(weight, calorie_mode)
            protein_target, fat_target, carb_target = calculate_macros(
                target_calories, protein_per_kg, fat_percent, weight)

            # Display calculated targets
            st.markdown("### Daily Targets")
            st.write(f"Target Calories: {target_calories:.0f} kcal")
            st.write(f"Protein: {protein_target:.1f}g")
            st.write(f"Fat: {fat_target:.1f}g")
            st.write(f"Carbs: {carb_target:.1f}g")

        # Display daily totals and progress
        #st.header("Daily Progress")

        # Get today's logs from Google Sheets
        today = datetime.now(
            pytz.timezone('Asia/Kolkata')).strftime('%d-%m-%Y')
        today_logs = get_daily_logs(st.session_state.mobile, today)
        # Initialize totals
        total_calories = total_protein = total_fat = total_carbs = 0
        # Calculate totals from today's logs
        if today_logs:
            total_calories = sum(log['Calories'] for log in today_logs)
            total_protein = sum(log['Protein'] for log in today_logs)
            total_fat = sum(log['Fat'] for log in today_logs)
            total_carbs = sum(log['Carbs'] for log in today_logs)
        # Calculate differences
        calorie_difference = target_calories - total_calories
        protein_difference = protein_target - total_protein
        fat_difference = fat_target - total_fat
        carbs_difference = carb_target - total_carbs

        # Create a layout for the progress
        #st.header("🍽️ Calories Consumed for the Day:")
        st.header("Daily Progress")

        # Create two rows with two columns each for mobile-friendly layout
        row1_col1, row1_col2 = st.columns(2)
        row2_col1, row2_col2 = st.columns(2)

        # First row
        with row1_col1:
            st.metric(
                "Total Calories",
                f"{total_calories:.0f}",
                delta=
                f"{abs(calorie_difference):.0f} kcal {'remaining ↓' if calorie_difference >= 0 else 'over ↑'}",
                delta_color="normal" if calorie_difference >= 0 else "inverse")
        with row1_col2:
            st.metric(
                "Protein",
                f"{total_protein:.1f}g",
                delta=
                f"{abs(protein_difference):.1f}g {'remaining ↓' if protein_difference >= 0 else 'over ↑'}",
                delta_color="normal" if protein_difference >= 0 else "inverse")
        # Second row
        with row2_col1:
            st.metric(
                "Fat",
                f"{total_fat:.1f}g",
                delta=
                f"{abs(fat_difference):.1f}g {'remaining ↓' if fat_difference >= 0 else 'over ↑'}",
                delta_color="normal" if fat_difference >= 0 else "inverse")
        with row2_col2:
            st.metric(
                "Carbs",
                f"{total_carbs:.1f}g",
                delta=
                f"{abs(carbs_difference):.1f}g {'remaining ↓' if carbs_difference >= 0 else 'over ↑'}",
                delta_color="normal" if carbs_difference >= 0 else "inverse")

        # Food logging section
        st.header("Log Your Meals")

        meal_options = ['Breakfast', 'Lunch', 'Evening Snacks', 'Dinner']
        selected_meal_type = st.selectbox("**Select Meal Type**",
                                          options=meal_options)

        st.markdown("""
        <style>
        /* Default: display columns side by side */
        .column {
            display: flex;
            vertical-align: top;
            width: 30%; /* 3 columns in fullscreen */
            box-sizing: border-box;
            margin: 0.5rem; /* Add some margin for better spacing in fullscreen */
        }
        /* Stack columns in mobile view */
        @media and (max-width: 640px) {
            .column {
                display: block;
                width: calc(100% - 1rem); /* Full width in mobile, subtract margin */
                margin: 0; /* Remove margin to eliminate space between columns */
                padding: 0.5rem; /* Optional: Small padding for better touch targets */
            }
        }
        /* Additional styling to override Streamlit default margins */
        .stButton, .stSelectbox, .stTextInput {
            margin: 0; /* Ensure no extra spacing for controls */
        }
        </style>
        """,
                    unsafe_allow_html=True)

        # Layout configuration
        st.container()
        with st.container():
            # Column 1
            st.markdown('<div class="column">', unsafe_allow_html=True)

            if 'food_selection' not in st.session_state:
                st.session_state.food_selection = ""  # Reset initial value

            food_selection = st.selectbox(
                f"**Select food for {selected_meal_type}**",
                options=[""] + food_db['Food Name'].tolist(),
                key=f"food_select_{selected_meal_type}")

            #st.markdown('</div>', unsafe_allow_html=True)

            # Column 2
            #st.markdown('<div class="column">', unsafe_allow_html=True)

            if food_selection:  # Proceed only if food_selection is not empty
                selected_food = food_db[food_db['Food Name'] ==
                                        food_selection].iloc[0]
                basis = selected_food.get('Basis', 'gm')

                # Display portion input with dynamic unit
                portion_unit = 'p' if basis == 'p' else (
                    'ml' if basis == 'ml' else 'gm')

                if 'portion' not in st.session_state:
                    st.session_state.portion = 0.0  # Set initial value as a float

                portion = st.number_input(
                    f"**Portion ({portion_unit})**",
                    min_value=0.0,  # Float
                    max_value=1000.0,  # Float
                    step=1.0 if basis == 'p' else 10.0,  # Float
                    value=float(
                        st.session_state.portion),  # Ensure value is float
                    key=f"portion_{selected_meal_type}")
            else:
                portion = 0.0  # Reset portion input as a float

            #st.markdown('</div>', unsafe_allow_html=True)

            # Column 3
            #st.markdown('<div class="column">', unsafe_allow_html=True)

            if st.button("Add", key=f"add_{selected_meal_type}"):
                if food_selection:  # Proceed if valid food is selected
                    food_item = food_db[food_db['Food Name'] ==
                                        food_selection].iloc[0]
                    base_weight = 100 if basis != 'p' else 1
                    multiplier = portion / base_weight

                    logged_item = {
                        'name': food_item['Food Name'],
                        'calories': food_item['Calories'] * multiplier,
                        'protein': food_item['Protein'] * multiplier,
                        'fat': food_item['Fat'] * multiplier,
                        'carbs': food_item['Carbs'] * multiplier,
                        'portion': portion,
                        'unit': portion_unit
                    }

                    # Add to session state
                    st.session_state.daily_log[
                        selected_meal_type.lower()] = logged_item

                    # Save to daily log sheet
                    meal_log = {
                        'mobile': st.session_state.mobile,
                        'meal_type': selected_meal_type,
                        'weight': portion,
                        'basis': basis,
                        'food_name': food_item['Food Name'],
                        'category': food_item.get('Category', 'N/A'),
                        'calories': logged_item['calories'],
                        'protein': logged_item['protein'],
                        'carbs': logged_item['carbs'],
                        'fat': logged_item['fat']
                    }
                    save_meal_log(meal_log)

                    st.success(
                        f"{food_item['Food Name']} added for {selected_meal_type}!"
                    )

                    # Reset inputs after adding a meal
                    st.session_state.food_selection = ""  # Reset food selection
                    st.session_state.portion = 0.0  # Reset portion input

                    st.rerun()  # Refresh the UI
                else:
                    st.warning("Please select a food item.")

            st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:  # Add Food tab
        st.header("Add New Food")
        # Add new food to database

        # Check for form reset
        if 'reset_form' in st.session_state and st.session_state['reset_form']:
            for key in list(st.session_state.keys()):
                if key.startswith('new_food_'):
                    del st.session_state[key]
            del st.session_state['reset_form']

        # Initialize form fields with default values if not in session state
        default_fields = {
            'new_food_name': '',
            'new_food_protein': 0.0,
            'new_food_fat': 0.0,
            'new_food_carbs': 0.0,
            'new_food_weight': 100.0,
            'new_food_basis': 'gm',
            'new_food_category': 'veg',
            'new_food_fibre': 0.0,
            'new_food_avg_weight': '',
            'new_food_source': ''
        }

        for field, default_value in default_fields.items():
            if field not in st.session_state:
                st.session_state[field] = default_value

        with st.expander("Add New Food"):
            col1, col2, col3 = st.columns(3)

            with col1:
                new_food_name = st.text_input("Food Name",
                                              value="",
                                              key='new_food_name')
                if new_food_name and food_exists_in_database(new_food_name):
                    st.warning(
                        f"'{new_food_name}' already exists in the database")

                new_food_protein = st.number_input("Protein",
                                                   min_value=0.0,
                                                   max_value=100.0,
                                                   step=0.1,
                                                   key='new_food_protein')
                new_food_fat = st.number_input("Fat",
                                               min_value=0.0,
                                               max_value=100.0,
                                               step=0.1,
                                               key='new_food_fat')
                new_food_carbs = st.number_input("Carbs",
                                                 min_value=0.0,
                                                 max_value=100.0,
                                                 step=0.1,
                                                 key='new_food_carbs')

                # Auto-calculate calories with proper formatting
                calories = calculate_calories_from_macros(
                    new_food_protein, new_food_fat, new_food_carbs)
                st.metric("Calculated Calories",
                          f"{calories:.1f} kcal",
                          delta=None,
                          delta_color="normal")

            with col2:
                new_food_weight = st.number_input("Weight",
                                                  min_value=0.1,
                                                  max_value=1000.0,
                                                  value=100.0,
                                                  step=0.1,
                                                  key='new_food_weight')
                new_food_basis = st.selectbox("Basis",
                                              options=['gm', 'ml', 'p'],
                                              key='new_food_basis')
                new_food_category = st.selectbox("Category",
                                                 options=['veg', 'non-veg'],
                                                 key='new_food_category')
                new_food_fibre = st.number_input("Fibre",
                                                 min_value=0.0,
                                                 max_value=100.0,
                                                 step=0.1,
                                                 key='new_food_fibre')

            with col3:
                new_food_avg_weight = st.text_input(
                    "Average Weight (optional)", key='new_food_avg_weight')
                new_food_source = st.text_input("Source (optional)",
                                                key='new_food_source')

            if st.button("Add to Database"):
                if new_food_name and not food_exists_in_database(
                        new_food_name):
                    new_food = {
                        'Food Name': new_food_name,
                        'Protein': new_food_protein,
                        'Fat': new_food_fat,
                        'Carbs': new_food_carbs,
                        'Calories': calories,
                        'Weight': new_food_weight,
                        'Basis': new_food_basis,
                        'Category': new_food_category,
                        'Fibre': new_food_fibre,
                        'Avg Weight': new_food_avg_weight,
                        'Source': new_food_source
                    }
                    if save_food_to_database(new_food):
                        st.success("Food added successfully!")
                        # Set reset flag
                        st.session_state['reset_form'] = True
                        # Reload the food database
                        st.cache_data.clear()
                        st.rerun()

        # Load food database
        food_db = load_food_database()

    with tabs[2]:  # Daily Log Tab
        # st.header("Daily Log")
        # st.divider()

        # Today's date for filtering
        from datetime import datetime
        today = datetime.now(pytz.timezone('Asia/Kolkata')).strftime(
            '%d-%m-%Y')  # Ensure today's date is formatted correctly in IST

        # Get logs for today
        today_logs = get_daily_logs(st.session_state.mobile, today)

        st.subheader("Today's Calorie Intake")
        if today_logs:
            log_df = pd.DataFrame(today_logs)
            display_cols = [
                'Timestamp', 'Meal Type', 'Food Name', 'Category', 'Calories',
                'Protein', 'Carbs', 'Fat'
            ]

            # Format timestamp to show only time
            log_df['Timestamp'] = pd.to_datetime(
                log_df['Timestamp']).dt.strftime('%I:%M %p')

            st.dataframe(log_df[display_cols], hide_index=True)
        else:
            st.info("No meals logged today")

        st.divider()

        # Daily Summary View
        st.subheader("Daywise Total Calorie Intake Summary")
        summaries = get_daily_summaries(st.session_state.mobile)
        if summaries:
            summary_df = pd.DataFrame(summaries)

            # Convert the 'date' column to datetime format for correct sorting
            summary_df['date'] = pd.to_datetime(summary_df['date'],
                                                format='%d-%m-%Y')
            # Sort the summary by date in descending order
            summary_df.sort_values(by='date', ascending=False, inplace=True)
            # Convert 'date' back to string if needed for display
            summary_df['date'] = summary_df['date'].dt.strftime('%d-%m-%Y')

            st.dataframe(summary_df, hide_index=True)
        else:
            st.info("No meal history available")

        st.divider()

        # Delete Logs Section
        st.subheader("Clear Specific Logs")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Select **start date** to clear logs",
                                       value=datetime.now().date(),
                                       key="start_date")
        with col2:
            end_date = st.date_input("Select **end date** to clear logs",
                                     value=datetime.now().date(),
                                     key="end_date")
        if st.button("Delete Logs in Range", type="secondary"):
            if start_date > end_date:
                st.error("Start date must be before end date.")
            else:
                if delete_logs_by_date_range(st.session_state.mobile,
                                             start_date, end_date):
                    st.success(
                        f"Logs deleted successfully between {start_date} and {end_date}!"
                    )
                    st.rerun()
                else:
                    st.error("Failed to delete logs.")

    with tabs[3]:  # Developer Details Tab
        st.header("AI: The genius 🤖")
        st.subheader("""
            Dhiraj: The one who takes credit (and the blame) 😎
        """)
        st.divider()
        st.markdown("""
         **Need Help ?**   
        _-please do email me at dhiraj1810.db@gmail.com if you have any questions or feedback. I’m open to new ideas and collaborations._   
          
       **_-Thank you for using this app! ✌🏽_**  
            """)
        #st.write("Email : darkcoders2016@gmail.com")

    #with tabs[4]:
