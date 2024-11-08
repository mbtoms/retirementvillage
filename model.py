import pandas as pd 
import numpy as  np 
import pdb 
import plotly.express as px
from io import BytesIO
import io

def expand_array_columns(df):
    """
    Expands any columns in the DataFrame that contain lists into separate columns.
    
    Parameters:
    df (pd.DataFrame): Input DataFrame potentially containing list columns.
    
    Returns:
    pd.DataFrame: New DataFrame with expanded columns.
    """
    # Create a new DataFrame to hold the expanded data
    expanded_df = pd.DataFrame()

    for column in df.columns:
        # Check if the column contains lists
        if df[column].apply(lambda x: isinstance(x, list)).any():
            # Expand the column and create new columns
            list_expanded_df = df[column].apply(pd.Series)
            list_expanded_df.columns = [f"{column}_{i}" for i in range(list_expanded_df.shape[1])]
            expanded_df = pd.concat([expanded_df, list_expanded_df], axis=1)
        else:
            # If not a list, just add the column to the new DataFrame
            expanded_df[column] = df[column]

    return expanded_df


class Model:

    def __init__(self, model_points):
        self.model_points = model_points
        self.life_expectancies = pd.DataFrame()
        self.cashflows = pd.DataFrame()

        self.charts = {}

        self.all_workings = {}









    def generate_excel(self):

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:

            
            self.model_points.to_excel(writer, index=False, sheet_name='Model Points')
            self.life_expectancies.to_excel(writer, index=False, sheet_name='Life Expectancies')
            self.cashflows.to_excel(writer, index=False, sheet_name='Cashflows')


            for key in self.all_workings:
                self.all_workings[key].to_excel(writer, index=False, sheet_name=key)
            # pd.DataFrame().to_excel(writer, 'Charts')
            # # workbook = writer.book
            # # workbook.add_worksheet("Charts")
            # charts_sheet = writer.sheets['Charts']
            # for chart_label in self.charts:
            #     fig = self.charts[chart_label]

            #     pdb.set_trace()
            #     img_bytes = io.BytesIO()
            #     fig.savefig(img_bytes, format='png')
            #     #plt.close(fig)  # Close the figure to avoid displaying it in notebooks
            #     img_bytes.seek(0)  # Move to the beginning of the BytesIO object


            #     # Convert it to a BytesIO stream.
            #     #image_data = BytesIO(fig.to_image(format="png"))

            #     # Write the image to the same sheet as the data.
            #     charts_sheet.insert_image('D2', 'plot.png', {'image_data': img_bytes})

            #                 # # Create a new worksheet and add the image to it.
            #                 # worksheet = workbook.add_worksheet()
            #                 # worksheet.insert_image(2, 3, 'plotly.png', {'image_data': image_data})

        output.seek(0)


        return output.read()

    def calculate_life_expectancy(self, mortality_tables, age, gender, longevity_loading_pct):
        '''
            calculate life expectancy in months.
        '''
    # assert 60 <= age <= 100
        assert gender in ('Male', 'Female')
        assert 0 <= longevity_loading_pct <= 100

        # Example: Calculate life expectancy for someone aged 30
        # age = 70
        # gender = 'Male'
        #mortality_improvement_loading = 0.0

        if gender == 'Male':
            mortality_table = mortality_tables[['Age', 'MaleMortality_qx']].copy()
        else:
            mortality_table = mortality_tables[['Age', 'FemaleMortality_qx']].copy()
        mortality_table.columns = ['age', 'qx']

        mortality_table['qx'] = mortality_table['qx'] 

        # Filter the table for ages greater than or equal to the input age
        table = mortality_table[mortality_table['age'] >= age].copy()
        
        # Calculate survival probability px = 1 - qx
        table['px'] = 1 - table['qx']

        # table['px'] = table['px'] * (1 + longevity_loading_pct/100)
        # table.loc[table['px'] > 1, 'px'] = 1
        #table['px'][table['px'] > 1] = 1

        # Calculate cumulative survival probability from the input age
        table['survival_prob'] = table['px'].cumprod()
        
        # Calculate life expectancy by summing up survival probabilities for each year
        life_expectancy = table['survival_prob'].sum()

        life_expectancy = life_expectancy * (1 + longevity_loading_pct/100)

        life_expectancy = int(life_expectancy * 12) # convert to months

        return life_expectancy


    def discount_cashflows(self, cashflows, discount_factors):
        discounted_cashflows = [a * b for a, b in zip(cashflows, discount_factors)]

        return discounted_cashflows, np.sum(discounted_cashflows), discount_factors



    def main(self, units, mortality_tables, longevity_loading_pct, discount_rate, investment_term, investment_return, refund_on_resale_pct, replacement, refund_on_resale_duration, single_double, package, purchase_price_input, monthly_fee, monthly_expense):
        '''
            note that cashflows and life expectancy are in months.
        '''



        
        main_life_expectancies = []
        spouse_life_expectancies = []
        purchase_cashflows = []
        discount_cashflows_list = []
        npvs = []


        discount_sale_cf_list = []
        discount_monthly_fee_cf_list = []
        discount_monthly_expense_cf_list = []
        discount_refund_cf_list = []

        sale_npvs = []
        refund_npvs = []
        monthly_fee_npvs = []
        monthly_expense_npvs = []

        last_life_expectancies = []

        discs = []
        invs = []
        discount_factors = [1/(1 + discount_rate/(100*12)) ** (month) for month in range(investment_term * 12)]
        inv_return_factors = [(1 + investment_return/(100*12)) ** (month) for month in range(investment_term * 12)]


        all_workings = {}


        for _, unit in units.iterrows():



            unit_workings = pd.DataFrame()
            unit_workings['Month'] = [month for month in range(investment_term * 12)]
            unit_workings['Investment Return Factors'] = inv_return_factors
            unit_workings['Discount Factors'] = discount_factors

            discs.append(discount_factors)
            invs.append(inv_return_factors)

            main_age = unit['Main Member Age']
            main_gender = unit['Main Member Gender']
            main_life_expectancy = self.calculate_life_expectancy(mortality_tables, main_age, main_gender, longevity_loading_pct)
            last_life_expectancy = main_life_expectancy
            spouse_age = 'NA'
            spouse_gender = 'NA'
            spouse_life_expectancy = 'NA'
            if single_double == 'Double':
                spouse_age = unit['Spouse Age']
                spouse_gender = unit['Spouse Gender']
                spouse_life_expectancy = self.calculate_life_expectancy(mortality_tables, spouse_age, spouse_gender, longevity_loading_pct)

                last_life_expectancy = max(last_life_expectancy, spouse_life_expectancy)

            last_life_expectancies.append(self.convert_age_to_years_months(last_life_expectancy))
            initial_purchase_price = purchase_price_input #unit['Purchase Price']
            #monthly_fee = unit['Monthly Fee']
            #monthly_expense = unit['Monthly Expense']


            sale_cf = [0] * investment_term * 12
            monthly_fee_cf = [0] * investment_term * 12
            monthly_expense_cf = [0] * investment_term * 12
            refund_cf = [0] * investment_term * 12
            # net_purchase_price_cf = [0] * investment_term * 12
            # net_purchase_price_cf = [0] * investment_term * 12
            # net_purchase_price_cf = [0] * investment_term * 12
            # expected_cashflows = [0] * investment_term * 12
            #start_month = 0



       
            orig_intial_purchase_price = initial_purchase_price
            purchase_price = orig_intial_purchase_price 

            #print(1/x for x in discount_factors[-5:])
            #print(inv_return_factors[-5:])

            counts = [''] * investment_term * 12
            count = 0

            start_month = 0
            for i in range(investment_term * 12):
                if (package == 'Life Rights') and (i == start_month):
                    sale_cf[i] = purchase_price 
                    count = count + 1

                if i >= start_month:
                    monthly_fee_cf[i] += monthly_fee 
                    monthly_expense_cf[i] -= monthly_expense

                if (package == 'Life Rights') and (i == last_life_expectancy+start_month):
                    if i < refund_on_resale_duration*12+start_month:
                        refund_on_resale = purchase_price * (refund_on_resale_pct/100) # TODO: confirm if refund on resale is related on initial purchase price or sale price?
                        refund_cf[i] -= refund_on_resale

                    purchase_price = orig_intial_purchase_price * inv_return_factors[i]

                    # print(f"month: {i}, inv ret fact: {((1+investment_return/(100*12))**i)}")
                    
                if (i == last_life_expectancy+start_month):

                    if not replacement:
                        counts[i] = count
                        break

                    start_month = i + 1
                 

                counts[i] = count




            expected_cashflows = [x + y + z + a for x, y, z, a in zip(sale_cf, monthly_fee_cf, monthly_expense_cf, refund_cf)]

           # pdb.set_trace()
            unit_workings['Count'] = counts
            unit_workings['Expected Sale Cashflows'] = sale_cf
            unit_workings['Expected Fee Cashflows'] = monthly_fee_cf
            unit_workings['Expected Expense Cashflows'] = monthly_expense_cf
            unit_workings['Expected Refund Cashflows'] = refund_cf
            unit_workings['All Expected Cashflows'] = expected_cashflows

            disc_sale_cf, sale_pv, _ = self.discount_cashflows(sale_cf, discount_factors)
            disc_refund_cf, refund_pv, _ = self.discount_cashflows(refund_cf, discount_factors)
            disc_monthly_fee_cf, monthly_fee_pv, _ = self.discount_cashflows(monthly_fee_cf, discount_factors)
            disc_monthly_expense_cf, monthly_expense_pv, _ = self.discount_cashflows(monthly_expense_cf, discount_factors)
            discounted_cashflows, npv, discount_factors = self.discount_cashflows(expected_cashflows, discount_factors)


            unit_workings['Discounted Sale Cashflows'] = disc_sale_cf
            unit_workings['Discounted Fee Cashflows'] = disc_monthly_fee_cf
            unit_workings['Discounted Expense Cashflows'] = disc_monthly_expense_cf
            unit_workings['Discounted Refund Cashflows'] = disc_refund_cf
            unit_workings['All Discounted Cashflows'] = discounted_cashflows



            main_life_expectancies.append(self.convert_age_to_years_months(main_life_expectancy))
            spouse_life_expectancies.append(self.convert_age_to_years_months(spouse_life_expectancy))


            # unit_workings['Main Life'] = disc_refund_cf
            # unit_workings['All Discounted Cashflows'] = discounted_cashflows


            purchase_cashflows.append(sale_cf)
            # cashflows.append(expected_cashflows)
            # cashflows.append(expected_cashflows)
            # cashflows.append(expected_cashflows)

            discount_cashflows_list.append(discounted_cashflows)
            discount_sale_cf_list.append(disc_sale_cf)
            discount_refund_cf_list.append(disc_refund_cf)
            discount_monthly_fee_cf_list.append(disc_monthly_fee_cf)
            discount_monthly_expense_cf_list.append(disc_monthly_expense_cf)
            
            npvs.append(npv)
            sale_npvs.append(sale_pv)
            refund_npvs.append(refund_pv)
            monthly_fee_npvs.append(monthly_fee_pv)
            monthly_expense_npvs.append(monthly_expense_pv)


            unit_workings['Sale NPV'] = ''
            unit_workings['Fee NPV'] = ''
            unit_workings['Expense NPV'] = ''
            unit_workings['Refund NPV'] = ''
            unit_workings['NPV'] = ''
            unit_workings.loc[0, 'Sale NPV'] = sale_pv
            unit_workings.loc[0, 'Fee NPV'] = monthly_fee_pv
            unit_workings.loc[0, 'Expense NPV'] = monthly_expense_pv
            unit_workings.loc[0, 'Refund NPV'] = refund_pv
            unit_workings.loc[0, 'NPV'] = npv
            # unit_workings['Discounted Fee Cashflows'] = disc_monthly_fee_cf
            # unit_workings['Discounted Expense Cashflows'] = disc_monthly_expense_cf
            # unit_workings['Discounted Refund Cashflows'] = disc_refund_cf
            # unit_workings['All Discounted Cashflows'] = discounted_cashflows



            all_workings[unit['ID']] = unit_workings
            # if main_age == 90:
            #     pdb.set_trace()

        results = pd.DataFrame()
        results['ID'] = units['ID']
        results['Last Life Expectancy'] = last_life_expectancies
        results['NPV'] = npvs
        results['Purchase NPV'] = sale_npvs
        results['Refund NPV'] = refund_npvs
        results['Fee NPV'] = monthly_fee_npvs
        results['Expense NPV'] = monthly_expense_npvs
        results['Main Member Age'] = units['Main Member Age']
        results['Main Member Gender'] = units['Main Member Gender']
        results['Spouse Age'] = units['Spouse Age']
        results['Spouse Gender'] = units['Spouse Gender']
        results['Main Life Expectancy'] = main_life_expectancies
        results['Spouse Life Expectancy'] = spouse_life_expectancies
        results['Purchase Cashflows'] = purchase_cashflows
        results['Discounted Cashflows'] = discount_cashflows_list
        results['Discount Factors'] = discs
        results['Investment Return Factors'] = invs


        self.cashflows = results
        self.all_workings = all_workings

        return results
        

    def convert_age_to_years_months(self, age_in_months):

        if isinstance(age_in_months, (int, float)):

            years = int(age_in_months / 12)
            months = age_in_months - years * 12

            return f"{years} years {months} months"

        else:
            return ""

    def remaining_life_expectancies(self, mortality_tables, longevity_loading_pct):

        results = pd.DataFrame()
        age = []
        remaining_life_expectancy_male = []
        remaining_life_expectancy_female = []
        

        for x in range(60, 95, 5):
            age.append(x)

            remaining_life_expectancy_male.append(self.calculate_life_expectancy(mortality_tables, x, 'Male', longevity_loading_pct)/ 12.0) 
            remaining_life_expectancy_female.append(self.calculate_life_expectancy(mortality_tables, x, 'Female', longevity_loading_pct)/ 12.0) 

        results['Age'] = age 
        results['Male'] = remaining_life_expectancy_male
        results['Female'] = remaining_life_expectancy_female

        fig = px.line(
            results,
            x="Age",
            y=["Male", "Female"],
            labels={"value": "Remaining Life Expectancy (years)", "variable": "Gender"},
            title="Life Expectancy from Various Ages",
        )

        self.charts["Life Expectancy from Various Ages"] = fig

        results['Male'] = results['Male'] * 12
        results['Female'] = results['Female'] * 12

        results['Male'] = results['Male'].apply(self.convert_age_to_years_months)
        results['Female' ] = results['Female'].apply(self.convert_age_to_years_months)

        self.life_expectancies = results

        return results, fig

# if __name__ == '__main__':
#     longevity_loading_pct = 10
#     main(longevity_loading_pct)
#     remaining_life_expectancies(longevity_loading_pct)



