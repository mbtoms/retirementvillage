import streamlit as st
import pandas as pd 
import pdb
from streamlit import session_state as ss

from model import Model





def group_monthly_to_yearly(monthly_values):
    """
    Groups monthly values into yearly totals.

    Parameters:
    - monthly_values: list or array-like, monthly values

    Returns:
    - list: yearly totals
    """
    # Calculate the number of years based on the length of the monthly values
    num_years = len(monthly_values) // 12  # Assuming complete years of monthly data
    yearly_totals = []

    for year in range(num_years):
        # Calculate the start and end index for the current year
        start_index = year * 12
        end_index = start_index + 12
        
        # Sum the monthly values for the current year
        yearly_total = sum(monthly_values[start_index:end_index])
        yearly_totals.append(yearly_total)

    return yearly_totals


units = pd.read_csv('units.csv')


if 'model' not in ss:
    ss['model'] = Model(units)   


# Set up the Streamlit page
st.title("Retirement Village Model")
# st.write("""
# This app calculates expected cashflows and profitability metrics for different retirement village packages:
# 1. Rental
# 2. Purchase
# 3. Life Rights
# """)



with st.sidebar:

    # User Input Section
    st.header('Input Parameters')

    mortality_table_label = st.selectbox('Mortality table', ['SAIFL98_SAIML98', 'CUSTOM', 'SA8590_light', 'SA8590_heavy'], 0)



    longevity_loading_pct = st.slider('Longevity loading %', min_value=0, max_value=20, value=10)




    investment_return = st.slider('Property Investment Return (annual %)', min_value=-10, max_value=10, value=0)




    discount_rate = st.slider('Discount rate (annual %)', min_value=0, max_value=15, value=10)

    investment_term = st.slider('Projection term (years)', min_value=0, max_value=40, value=40)

    single_double = st.selectbox('Single or double', ['Single', 'Double'], 0)

    package = st.selectbox('Package type', ['Life Rights', 'Rental'], 0)


    purchase_price = st.number_input("Purchase Price", min_value=0, max_value=None, step=1000, value=125000)
    monthly_fee = st.number_input("Monthly Fee", min_value=0, max_value=None, step=100, value=1000)
    monthly_expense = st.number_input("Monthly Expense", min_value=0, max_value=None, step=100, value=1000)
    
    replacement = st.checkbox("Replacement", value=False)


    refund_on_early_exit = False    
    refund_on_resale = 0
    refund_on_resale_duration = 0

    if package == 'Life Rights':

        refund_on_early_exit = st.checkbox("Refund on early exit", value=False)

        if refund_on_early_exit:
            refund_on_resale = st.slider('Refund (%)', min_value=0, max_value=100, value=80)

            refund_on_resale_duration = st.slider('Early exit term (years)', min_value=0, max_value=20, value=10)

    if st.button('Generate Results'):
        excel_data = ss.model.generate_excel()
        #print(excel_data)
        st.download_button(
            label="Download Results",
            data=excel_data,
            file_name="retirement_village_model_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )




#st.write(longevity_loading_pct)
mortality_tables = pd.read_csv(f'mortality_table_{mortality_table_label}.csv')

#packages = ['Life Rights Single', 'Life Rights Double', 'Rental Single', 'Rental Double']
#tab1, tab2, tab3, tab4, tab5 = st.tabs(["Life Expectancies"] + packages)

tab000, tab2, tab1, tab00, tab0 = st.tabs(['User Guide', 'Results', 'Life Expectancies', 'Model Points', 'Mortality Rates'])

with tab000:
    st.header('Overview')
    st.write('This model calculates life expectancies and projects expected future cashflows arising for different packages (Life Rights and Rental) for a retirement village.')
    st.write('Input parameters can be specified using the sidebar on the left. The model shows the following tabs:')
    st.markdown('- User Guide')
    st.markdown('- Results')
    st.markdown('- Life Expectancies')
    st.markdown('- Model Points')
    st.markdown('- Mortality Rates')
    st.write('Results can be downloaded using the "Generate Results" and "Download Results" buttons at the bottom of the sidebar.')
    st.write('The input parameters will be described in more detail below.')
    st.header('Input Parameters')
      # User guide for each input parameter
    st.write("""
    ### Mortality Table
    - **Description**: Select the mortality table to use in the model. This table is used to estimate life expectancies based on different mortality rates. Unfortunately data for estimating longevity in Zambia is limmited, the best we can do for now is use these South African mortality rates with the adjustment for uncertainty (to increase longevity) described in the next section.
    - **Options**:
        - 'SAIFL98_SAIML98': A standard South African mortality table.
        - 'CUSTOM': A custom mortality table.
        - 'SA8590_light' & 'SA8590_heavy': Mortality tables based on South African assumptions for various population demographics. The rates in this table are not split by gender.
    - **Recommended Value**: SAIFL98_SAIML98.

    ### Longevity Loading %
    - **Description**: This parameter allows you to adjust the mortality rates used in the model. Increasing this parameter will decrease the mortality rates used in the model, resulting in longer life expectancies and reduced profitability of the Life Rights Package.
    - **Recommended Value**: To allow for uncertainty and prudence in the mortality rates, recommend applying a 10% longevity loading to the mortality rates.

    ### Property Investment Return (annual %)
    - **Description**: Represents the annual return on property investments as a percentage. This is used to project future investment returns for the retirement village.
    - **Range**: -10% to 10%.
    - **Recommended Value**: 0% (for prudence and to allow for the extreme uncertainty in trying to project expected investment returns in the future)

    ### Discount Rate (annual %)
    - **Description**: The discount rate represents the interest rate used to calculate the present value of future cashflows. A higher discount rate means future cashflows are worth less today. This value could be based on the shareholders required rate of return for the project. One method for determing the shareholders required rate of return is to use the weighted avarage cost of capital (WACC) for the project. Eg, if the project is 100% funded by debt that carries a 10% interest rate, then the shareholders required rate of return would need to be 10% or higher in order for the project to be profitable.
    - **Range**: 0% to 15% (default 10%).

    ### Projection Term (years)
    - **Description**: The number of years years of future cashflows to allow for in the model. The uncertainty associated with expected cashflows increases the further the cashflows are into the future.
    - **Range**: 0 to 40 years (default 40 years).

    ### Single or Double
    - **Description**: Choose between a single or double occupancy for the unit.
    - **Options**: 'Single' or 'Double' (default 'Single').

    ### Package Type
    - **Description**: Select the type of financial package for the retirement village:
        - **Life Rights**: This option gives residents the right to live in the unit until the death of the main member or the last surving member (for a Double package).
        - **Rental**: A typical rental arrangement for the units.
    - **Options**: 'Life Rights' or 'Rental' (default 'Life Rights').

    ### Purchase Price
    - **Description**: The initial price for purchasing a unit in the retirement village (applies to 'Life Rights' packages).
    - **Range**: 0 to unlimited (default 125,000).

    ### Monthly Fee
    - **Description**: The regular monthly fee charged to residents for their stay, covering services and maintenance.
    - **Range**: 0 to unlimited (default 1,000).

    ### Monthly Expense
    - **Description**: The monthly operational expense of running the retirement village.
    - **Range**: 0 to unlimited (default 1,000).

    ### Replacement
    - **Description**: Checkbox to enable or disable starting a new package once the original package ends. The new package is assumed to be sold to residents of the same age / gender / package type as the original package.
    - **Options**: `True` or `False` (default `False`).

    ### Refund on Early Exit
    - **Description**: If enabled, residents can receive a refund of their initial purchase price if they leave the village before their term expires.
    - **Options**: `True` or `False` (default `False`).

    ### Refund on Early Exit (%) 
    - **Description**: Percentage refund for early exit if the "Refund on Early Exit" option is selected.
    - **Range**: 0-100% (default 80%).

    ### Early Exit Term (years)
    - **Description**: Defines the number of years during which the refund applies for residents exiting early.
    - **Range**: 0-20 years (default 10 years).
    """)  

with tab00:
    df = units.set_index('ID', drop=True)
    st.dataframe(df)

with tab0:
    st.write('Mortality rates before longevity loading adjustment')
    df = mortality_tables.set_index('Age', drop=True)
    st.dataframe(df)

with tab1:
    st.header('Life Expectancy from various ages')

    df, fig = ss['model'].remaining_life_expectancies(mortality_tables, longevity_loading_pct)
    st.plotly_chart(fig)
    st.write('**Life Expectancy from Various Ages Data**')
    df = df.set_index('Age', drop=True)
    st.dataframe(df)




with tab2:

    df = ss['model'].main(units, mortality_tables, longevity_loading_pct, discount_rate, investment_term, investment_return, refund_on_resale, replacement, refund_on_resale_duration, single_double, package, purchase_price, monthly_fee, monthly_expense)
    df = df.set_index('ID', drop=True)

    st.header("Summary Graph")
    st.bar_chart(df['NPV'], y_label="net present value")
    

#    with 
    #units_package = units[units['Package'] == package]
    st.header("Summary Cashflows")
    
    st.dataframe(df)

    #  col1, col2 = st.columns(2)

    #  with col1:
        # st.w(f'No Replacement')



   # st.subheader('Discounted cashflows')

    # for index in df.index:
    #     values_to_plot = df.loc[index, 'Discounted Cashflows']

    #  #   print(values_to_plot)

    #     values_to_plot = group_monthly_to_yearly(values_to_plot)
    #    # pdb.set_trace()
    #     st.write(f'**{index}**')
    #     # Create a DataFrame for plotting
    #     #plot_df = pd.DataFrame({'Year': [int(x / 12) for x in range(len(values_to_plot))], 'Discounted Cashflows': values_to_plot})
    #     plot_df = pd.DataFrame({'Year': [x for x in range(len(values_to_plot))], 'Discounted Cashflows': values_to_plot})
    #     # Display the bar chart
    #     st.bar_chart(plot_df.set_index('Year'), x_label='years', y_label='present value')



    data = ss.model.all_workings
#    # Create tabs based on the keys of the dictionary
#    tabs = st.tabs(list(data.keys()))


    st.subheader("Graphs")
    # Display each tab's content
    for i, (key, content) in enumerate(data.items()):
       # with tabs[i]:



        values_to_plot = content['All Discounted Cashflows']
        values_to_plot = group_monthly_to_yearly(values_to_plot)
    # pdb.set_trace()
        st.write(f'**{key}**')
        # Create a DataFrame for plotting
        #plot_df = pd.DataFrame({'Year': [int(x / 12) for x in range(len(values_to_plot))], 'Discounted Cashflows': values_to_plot})
        plot_df = pd.DataFrame({'Year': [x for x in range(len(values_to_plot))], 'Discounted Cashflows': values_to_plot})
        # Display the bar chart
        st.bar_chart(plot_df.set_index('Year'), x_label='years', y_label='present value of cashflows')

    st.subheader("Cashflows Breakdown")
    for i, (key, content) in enumerate(data.items()):
        st.write(f'**{key}**')
        content = content.set_index('Month')
        st.write(content)