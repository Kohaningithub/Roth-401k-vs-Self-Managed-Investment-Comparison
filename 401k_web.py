import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from investment_model import InvestmentComparator
import io
import sys

def main():
    st.markdown("<h1 style='white-space: nowrap;'>Roth 401k vs Self-Managed Comparison</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    ### What This Tool Compares
    This calculator compares two investment strategies, assuming the same initial contribution amount for both:
    1. **Roth 401k**: Contributing to a tax-advantaged retirement account where:
       - Contributions are made with after-tax dollars
       - All growth is tax-free
       - Withdrawals in retirement are tax-free
       - Early withdrawals before 59½:
         - Contributions can be withdrawn tax- and penalty-free
         - Earnings may be subject to income tax + 10% penalty, unless an exception applies
       
    2. **Self-Managed Portfolio**: Keeping the money and investing it yourself where:
       - You manage a mix of passive and active investments
       - You pay capital gains taxes on profits
       - You have more flexibility but face tax implications
    """)

    # Left column for inputs, right column for results
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.header("Parameters")

        st.subheader("Your Information")
        current_age = st.number_input(
            "Current Age", 
            value=22, 
            min_value=18, 
            max_value=65,
            help="Your current age"
        )

        retirement_age = st.number_input(
            "Retirement Age", 
            value=65, 
            min_value=current_age + 1,
            help="Your planned retirement age"
        )
        
        # Calculate Roth limit based on age
        roth_limit = 30500 if current_age >= 50 else 23000
        
        annual_income = st.number_input(
            "Current Pre-Tax Annual Income ($)", 
            min_value=0, 
            value=100000,
            help="Your current pre-tax annual income, will be subjected to different tax brackets"
        )

        # Calculate maximum allowed percentage
        max_percent = min(20, (roth_limit/annual_income)*100)
        
        # Adjust initial value to be more reasonable based on max
        suggested_value = min(10, max_percent/2)  # Start at half of max or 10%, whichever is lower

        roth_contribution_pct = st.slider(
            "Roth 401k Contribution (%)", 
            min_value=0.00,  # Allow fractional percentages
            max_value=float(max_percent),
            value=float(suggested_value),
            step=0.11,  # Allow finer control
            help=f"""
            2024 Roth 401(k) Contribution Limits:

            • Under 50: $23,000/year

            • 50 or older: $30,500/year   

            Your maximum: ${roth_limit:,.0f}/year ({max_percent:.1f}% of your income)  

            Same contribution amount will be used for self-directed investment comparison.
            """
        ) / 100

        # Calculate and display actual contribution amount
        contribution_amount = annual_income * roth_contribution_pct
        st.write(f"Annual contribution: ${contribution_amount:,.0f}")
        
        if contribution_amount > roth_limit:
            st.error(f"⚠️ Contribution exceeds annual limit of ${roth_limit:,}!")
            contribution_amount = roth_limit
            roth_contribution_pct = roth_limit / annual_income
            st.write(f"Adjusted to maximum allowed: ${roth_limit:,}")
        
        st.subheader("Investment Parameters")
        roth_fee = st.number_input(
            "Roth 401k Management Fee (%)", 
            min_value=0.0,
            max_value=2.0,
            value=0.2,
            step=0.1,
            help="""
            Total annual management and administration fees for Roth 401(k):

            Check your Roth 401k statement for the exact fee.

            • Typical range: 0.0% to 2.0% per year. 

            • Zero fees: Some employers cover all costs

            • Lower fees (0.3-0.5%): Common in large companies

            • Higher fees (1-2%): More common in smaller plans
            """
        ) / 100
        
        employer_match = st.number_input(
            "Employer Match (%)", 
            min_value=0.0,
            max_value=100.0,
            value=3.0,
            step=0.5,
            help="""
            Percentage of salary your employer matches in 401(k):

            • Typical range: 3-6% of salary

            • Match goes into Traditional (pre-tax) 401(k)

            • Common formulas:
            
              - 100% match up to X% of salary
              - 50% match up to 2X% of salary
            
            💡 Always try to contribute enough to get full employer match!
            """
        ) / 100
        
        match_limit = st.number_input(
            "Match Limit (% of Salary)", 
            min_value=0.0,
            max_value=100.0,
            value=6.0,
            step=0.5,
            help="""
            Maximum salary percentage eligible for employer match:

            • Example: 6% means employer matches up to 6% of your salary

            • Your contributions above this don't get matched
            """
        ) / 100
        
        active_return = st.number_input(
            "Active Investment Return Rate (%)", 
            min_value=0, 
            max_value=100, 
            value=12,
            help="Expected nominal return for active investments (The model will adjust for inflation)"
        ) / 100
        
        passive_ratio = st.slider(
            "Passive Investment Ratio (%)", 
            0, 100, 80,
            help="Percentage allocated to passive investments like index funds"
        ) / 100
        
        passive_return = st.number_input(
            "Passive Return Rate (%)", 
            value=10.0,
            help="Adjust with your product portfolio return rate. 10% is S&P 500 historical average (The model will adjust for inflation)"
        ) / 100
        
        r_401k = st.number_input(
            "401k Return Rate (%)", 
            value=10.0,
            help="Adjust with your product portfolio return rate. 10% is S&P 500 historical average (The model will adjust for inflation)"
        ) / 100
        
        active_trading_freq = st.number_input(
            "Active Trading Frequency (%/year)", 
            min_value=0.0,
            max_value=100.0,
            value=30.0,
            step=5.0,
            help="""
            How often you trade your active investments per year:

            • Trading frequency = Portfolio turnover rate

            • Example: 30% means you replace 30% of holdings annually
            
            Typical ranges:

            • Buy & hold: 0-20% turnover

            • Moderate trading: 20-50%

            • Active trading: 50-100%
            
            Higher turnover → More short-term capital gains tax
            """
        ) / 100
        
        st.subheader("Economic Factors")
        inflation = st.number_input(
            "Inflation Rate (%)", 
            value=3.0,
            help="3% is default annual inflation rate"
        ) / 100
        
        salary_growth = st.number_input(
            "Annual Salary Growth (%)", 
            value=4.0,
            help="Expected annual salary increase"
        ) / 100

    # Right column for results
    with col2:
        st.header("Results")
        
        # Create investment comparator with user parameters
        comparator = InvestmentComparator()
        
        # Update all parameters
        comparator.current_age = current_age
        comparator.retirement_age = retirement_age
        comparator.initial_investment = annual_income * roth_contribution_pct
        comparator.annual_income = annual_income
        comparator.salary_growth = salary_growth
        comparator.r_active = active_return
        comparator.passive_ratio = passive_ratio
        comparator.active_ratio = 1 - passive_ratio
        comparator.r_passive = passive_return
        comparator.r_401k = r_401k
        comparator.inflation = inflation
        comparator.f_401k = roth_fee
        comparator.employer_match = employer_match
        comparator.match_limit = match_limit
        comparator.active_trading_freq = active_trading_freq
        
        # Calculate returns and capture debug output
        old_stdout = sys.stdout
        debug_output = io.StringIO()
        sys.stdout = debug_output

        roth_value, roth_annual, roth_contributions = comparator.calculate_roth_401k_returns()
        self_value, self_annual, self_contributions = comparator.calculate_self_investment_returns()

        # Restore stdout
        sys.stdout = old_stdout

        # Display debug information in an expandable section
        with st.expander("Show Calculation Details"):
            st.text(debug_output.getvalue())

        # Display key metrics
        st.subheader("Final Values (Inflation Adjusted)")
        col_metrics1, col_metrics2 = st.columns(2)
        
        with col_metrics1:
            metric_label = "Roth 401k + Employer Match" if employer_match > 0 else "Roth 401k"
            st.metric(
                metric_label, 
                f"${roth_value:,.0f}", 
                help="""
                Final portfolio value including:
                • Roth 401k (tax-free growth & withdrawals)
                """ + ("""
                • Employer match (pre-tax, taxed at withdrawal)
                """ if employer_match > 0 else "") + """
                • Adjusted for inflation
                """
            )
        
        with col_metrics2:
            st.metric(
                "Self-managed", 
                f"${self_value:,.0f}",
                help="""
                Final portfolio value including:
                • Passive investments (index funds)
                • Active investments
                • After all taxes and fees
                • Adjusted for inflation
                """
            )
        
        # Only show employer match metric if there is a match
        if employer_match > 0:
            st.metric(
                "Total Employer Match Value", 
                f"${roth_annual[-1] - roth_contributions:,.0f}",
                help="""
                Total value of employer matching contributions:
                • Includes compound growth
                • Pre-tax (will be taxed at withdrawal)
                • Adjusted for inflation
                """
            )
        
        # Add overall comparison
        st.metric(
            "Strategy Difference", 
            f"{((self_value/roth_value)-1)*100:.0f}%",
            help="Percentage difference between self-managed and Roth 401k strategies. Positive means self-managed performed better."
        )
        
        # Plot growth comparison
        st.subheader("Growth Comparison")
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Ensure both arrays have same length
        years = range(len(roth_annual))
        label = 'Roth 401k + Employer Match' if employer_match > 0 else 'Roth 401k'
        ax.plot(years, roth_annual, label=label, linewidth=2)
        ax.plot(years, self_annual[:len(years)], label='Self-managed', linewidth=2)  # Slice to match length
        
        # Format axes
        ax.set_xlabel('Years')
        ax.set_ylabel('Portfolio Value ($)')
        ax.legend()
        ax.grid(True)
        
        # Format y-axis with dollar signs and commas
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        st.pyplot(fig)
        
        # Add explanatory notes
        st.markdown("""
        ### Key Notes
        - Roth 401k: Tax-free growth & withdrawals
        - Employer match: Pre-tax contributions, taxed at withdrawal
        - Self-managed: Subject to capital gains tax & trading costs
        - Active investing carries higher risk

        ### Model Limitations
        - Assumes consistent returns without market volatility
        - Assumes employer match vests immediately
        - Tax brackets assumed constant over time
        - Does not model early withdrawal scenarios
        """)

if __name__ == "__main__":
    main() 