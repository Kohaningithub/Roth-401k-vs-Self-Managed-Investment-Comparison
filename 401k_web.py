import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from investment_model import InvestmentComparator

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
        
        # Calculate Roth limit based on age
        roth_limit = 30500 if current_age >= 50 else 23000
        
        annual_income = st.number_input(
            "Current Annual Income ($)", 
            min_value=0, 
            value=100000,
            help="Your current annual income"
        )

        # Calculate maximum allowed percentage
        max_percent = min(20, (roth_limit/annual_income)*100)
        
        # Adjust initial value to be more reasonable based on max
        suggested_value = min(10, max_percent/2)  # Start at half of max or 10%, whichever is lower

        roth_contribution_pct = st.slider(
            "Roth 401k Contribution (%)", 
            min_value=0.0,  # Allow fractional percentages
            max_value=float(max_percent),
            value=float(suggested_value),
            step=0.1,  # Allow finer control
            help=f"""
            2024 Roth 401(k) Contribution Limits:
            
            • Under 50: $23,000/year

            • 50 or older: $30,500/year (includes $7,500 catch-up)
            
            Your maximum: ${roth_limit:,}/year ({max_percent:.1f}% of your income)
            
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
        
        retirement_age = st.number_input(
            "Retirement Age", 
            value=65, 
            min_value=current_age + 1,
            help="Your planned retirement age"
        )
        
        st.subheader("Investment Parameters")
        active_return = st.number_input(
            "Active Investment Return Rate (%)", 
            min_value=5, 
            max_value=20, 
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
            help="10% is S&P 500 historical average (The model will adjust for inflation)"
        ) / 100
        
        r_401k = st.number_input(
            "401k Return Rate (%)", 
            value=10.0,
            help="10% is S&P 500 historical average (The model will adjust for inflation)"
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
        
        # Calculate returns
        roth_value, roth_annual, roth_contributions = comparator.calculate_roth_401k_returns()
        self_value, self_annual, self_contributions = comparator.calculate_self_investment_returns()
        
        # Display key metrics
        st.subheader("Final Values (Inflation Adjusted)")
        col_metrics1, col_metrics2 = st.columns(2)
        
        with col_metrics1:
            st.metric(
                "Roth 401k", 
                f"${roth_value:,.0f}", 
                help="Final portfolio value after tax and inflation adjustment. All growth is tax-free."
            )
            st.metric(
                "Roth Contributions", 
                f"${roth_contributions:,.0f}",
                help="Total amount contributed to Roth 401k over the investment period. This is lower because Roth contributions are made with after-tax dollars (you pay taxes first, then contribute)."
            )
        
        with col_metrics2:
            st.metric(
                "Self-managed", 
                f"${self_value:,.0f}",
                help="Final portfolio value after taxes, fees, and inflation adjustment. Includes both passive and active investments."
            )
            st.metric(
                "Self-managed Contributions", 
                f"${self_contributions:,.0f}",
                help="Total amount invested in self-managed portfolio over the investment period. This is higher because you're investing the pre-tax amount, but you'll pay capital gains taxes on the growth."
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
        ax.plot(years, roth_annual, label='Roth 401k', linewidth=2)
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
        - Self-managed: Subject to capital gains tax & trading costs
        - Active investing carries higher risk

        ### Model Limitations
        - Assumes consistent returns without market volatility
        - Does not consider employer matching contributions
        - Tax brackets assumed constant over time
        - Does not model early withdrawal scenarios
        """)

if __name__ == "__main__":
    main() 