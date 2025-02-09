import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from investment_model import InvestmentComparator
import io
import sys
from state_tax import StateTaxManager

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
        # Helper functions at the top
        def get_roth_limit(age):
            base_limit = 23500  # 2025 base limit
            if age >= 60 and age <= 63:
                catch_up = 11250  # Special catch-up for ages 60-63
            elif age >= 50:
                catch_up = 7500   # Regular catch-up for 50+
            else:
                catch_up = 0
            return base_limit + catch_up

        def get_total_limit(age):
            if age >= 60 and age <= 63:
                return 81250  # Special catch-up
            elif age >= 50:
                return 77500  # Regular catch-up
            return 70000     # Standard limit

        def calculate_max_employer_match(annual_income, age):
            """Calculate maximum allowed employer match percentage based on limits"""
            # Get employee and total contribution limits
            employee_limit = get_roth_limit(age)
            total_limit = get_total_limit(age)
            
            # Maximum employer contribution allowed
            max_employer_contribution = min(
                total_limit - employee_limit,  # Limited by total contribution cap
                annual_income  # Cannot exceed 100% of salary
            )
            
            # Convert to percentage of salary
            max_match_percent = (max_employer_contribution / annual_income) * 100
            
            return min(100.0, max_match_percent)  # Cap at 100% for safety

        # Get user inputs
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
        
        annual_income = st.number_input(
            "Current Pre-Tax Annual Income ($)", 
            min_value=0, 
            value=100000,
            help="Your current pre-tax annual income, will be subjected to different tax brackets"
        )

        # Now we can calculate the employer match limits
        max_match_percent = calculate_max_employer_match(annual_income, current_age)

        roth_limit = get_roth_limit(current_age)
        
        # Calculate maximum allowed percentage
        max_percent = (roth_limit / annual_income) * 100
        
        # Adjust initial value to be more reasonable based on max
        suggested_value = min(10, max_percent/2)  # Start at half of max or 10%, whichever is lower

        roth_contribution_pct = st.slider(
            "Roth 401k Contribution (%)", 
            min_value=0.00,
            max_value=float(max_percent),
            value=float(suggested_value),
            step=0.11,
            help=f"""
            2025 Roth 401(k) Contribution Limits:

            • Under 50: $23,500/year

            • Ages 50-59: $31,000/year (+$7,500 catch-up)

            • Ages 60-63: $34,750/year (+$11,250 catch-up)

            • Ages 64+: $31,000/year (+$7,500 catch-up)

            Your maximum: ${roth_limit:,.0f}/year ({max_percent:.1f}% of your income)

            Total contribution limits (employer + employee):

            • Regular: $70,000

            • Age 50+: $77,500

            • Age 60-63: $81,250

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
        
        st.subheader("Roth 401k Investment Parameters")
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
        
        # Update employer match input
        employer_match = st.number_input(
            "Employer Match (%)", 
            min_value=0.0,
            max_value=calculate_max_employer_match(annual_income, current_age),
            value=min(3.0, calculate_max_employer_match(annual_income, current_age)),
            step=0.1,
            help=f"""
            Employer matching contribution percentage:

            • Common matches: 3-6%

            • Maximum allowed: {calculate_max_employer_match(annual_income, current_age):.1f}%
              (Based on your income ${annual_income:,.0f} and 2025 limits)
            """
        ) / 100

        # Calculate actual employer contribution
        employer_contribution = annual_income * employer_match

        # Show warning if contribution would exceed limits
        if employer_contribution > (get_total_limit(current_age) - get_roth_limit(current_age)):
            st.error(f"""
            ⚠️ Employer Match Exceeds Contribution Limits!
            
            Current total: ${get_roth_limit(current_age) + employer_contribution:,.0f}
            Maximum allowed: ${get_total_limit(current_age):,.0f}
            """)
            
            if st.button("Adjust to Maximum Allowed"):
                max_match = (get_total_limit(current_age) - get_roth_limit(current_age)) / annual_income
                st.session_state.employer_match = max_match
                st.experimental_rerun()
        
        match_limit = st.number_input(
            "Match Limit (% of Salary)", 
            min_value=0.0,
            max_value=100.0,
            value=6.0,
            step=0.5,
            help="""
            Check your plan for the maximum salary percentage eligible for employer match:

            • Example: 6% means employer matches up to 6% of your salary
            """
        ) / 100

        r_401k = st.number_input(
            "401k Return Rate (%)", 
            value=10.0,
            help="Adjust with your product portfolio return rate. 10% is S&P 500 historical average (The model will adjust for inflation)"
        ) / 100
        
        st.subheader("Self-Managed Investment Parameters")

        active_return = st.number_input(
            "Active Investment Return Rate (%)", 
            min_value=0, 
            max_value=100, 
            value=12,
            help="Investments that involve frequent buying and selling (e.g., individual stocks, options, hedge funds). The model will adjust for inflation and volatility."
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
        
        
        active_trading_freq = st.number_input(
            "Portfolio Turnover Rate (%)", 
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

        st.subheader("Tax Parameters")
        # Initialize state tax manager
        state_manager = StateTaxManager()
        states = state_manager.get_state_list()

        selected_state = st.selectbox(
            "Select Your State",
            states,
            index=states.index("California"),  # Default to California
            help="""
            Select your state of residence for tax calculations:

            • State income tax rates vary from 0% to 13.3%
            • Tax brackets vary by state
            • Some states have no income tax
            """
        )

        # Get state info
        state_info = state_manager.get_state_info(selected_state)

        # Display state tax info
        st.info(f"""
        **{selected_state} Tax Information**
        • {'Has' if state_info['has_income_tax'] else 'No'} state income tax
        • Maximum rate: {state_info['max_rate']:.2%}
        • Number of brackets: {state_info['num_brackets']}
        • Standard deduction: ${state_info['standard_deduction']:,.0f}
        """)

        # Add marriage status note
        st.warning("""
        **Note on Marriage Status:**
        This model uses single filer tax rates for simplicity. Marriage status can affect:

        • Tax brackets

        • Standard deductions

        • Personal exemptions

        Consider consulting a tax professional for your specific situation.
        """)

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
        comparator.state_tax = state_info['max_rate']
        comparator.state_cg_tax = state_info['max_rate']
        
        # Calculate returns and capture debug output
        old_stdout = sys.stdout
        debug_output = io.StringIO()
        sys.stdout = debug_output

        roth_value, roth_annual, roth_contributions, roth_prob = comparator.calculate_roth_401k_returns()
        self_value, self_annual, self_contributions, self_prob = comparator.calculate_self_investment_returns()

        # Restore stdout
        sys.stdout = old_stdout

        # Display debug information in expandable sections
        st.subheader("Detailed Analysis")

        # Investment Calculations
        with st.expander("Investment Calculations"):
            st.markdown("### Detailed Calculation Steps")
            st.text(debug_output.getvalue())
            
            st.markdown("""
            **Key Tax Considerations**
            • Federal Income Tax: Progressive brackets from 10% to 37%
            • Federal Capital Gains: 0%, 15%, or 20% based on income
            • State Income Tax: Applied to contributions
            • State Capital Gains: Applied to investment gains
            
            **Growth Assumptions**
            • Salary Growth: Adjusted for inflation
            • Investment Returns: Nominal returns adjusted for inflation
            • Trading Costs: Includes commissions and tax impact
            """)

        # Risk Analysis
        with st.expander("Risk & Return Analysis"):
            st.markdown("""
            ### Portfolio Risk Metrics
            
            **Roth 401k Strategy**
            • Tax-free growth reduces uncertainty
            • Employer match provides guaranteed return
            • Limited investment options
            • Early withdrawal penalties
            
            **Self-Managed Strategy**
            • More investment flexibility
            • Higher potential returns
            • Tax implications on trades
            • Market risk exposure
            
            **Tax Risk Considerations**
            • Future tax rate uncertainty
            • State tax policy changes
            • Capital gains rate changes
            • Alternative minimum tax (AMT)
            """)

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
        st.subheader("Investment Growth Comparison")

        # Create two tabs
        tab1, tab2 = st.tabs(["Expected Growth", "Growth with Uncertainty"])

        with tab1:
            # Plot deterministic results
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            years = range(len(roth_annual))
            ax1.plot(years, roth_annual, label='Roth 401k (Expected)', linewidth=2)
            ax1.plot(years, self_annual, label='Self-managed (Expected)', linewidth=2)
            ax1.set_xlabel('Years')
            ax1.set_ylabel('Portfolio Value ($)')
            ax1.legend()
            ax1.grid(True)
            ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            st.pyplot(fig1)

        with tab2:
            # Plot probabilistic results with confidence intervals
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            
            # Plot mean trajectories
            ax2.plot(years, roth_prob[0], label='Roth 401k (Mean)', linewidth=2)
            ax2.plot(years, self_prob[0], label='Self-managed (Mean)', linewidth=2)
            
            # Add confidence intervals
            ax2.fill_between(years, roth_prob[1][0], roth_prob[1][1], 
                             alpha=0.2, label='Roth 401k 90% CI')
            ax2.fill_between(years, self_prob[1][0], self_prob[1][1], 
                             alpha=0.2, label='Self-managed 90% CI')
            
            ax2.set_xlabel('Years')
            ax2.set_ylabel('Portfolio Value ($)')
            ax2.legend()
            ax2.grid(True)
            ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            st.pyplot(fig2)

        # Add explanation
        st.markdown("""
        ### Understanding the Investment Comparison

        **Base Market Returns**
        - Both strategies experience the same underlying market movements
        - The S&P 500 historical return (10%) is used as the baseline

        **Key Differences**
        1. **Roth 401k**
           - Tax-free growth
           - Simple fee structure
           - Employer match benefit
           - Limited investment options

        2. **Self-Managed Portfolio**
           - Passive portion (80%)
             - Same market returns as Roth
             - Lower fees
             - Minimal tax impact (low turnover)
           
           - Active portion (20%)
             - Potential for higher returns
             - Higher fees and trading costs
             - More tax impact (higher turnover)
             - Greater volatility

        **Risk Factors**
        - Market risk affects both strategies equally
        - Active trading adds additional volatility
        - Tax implications vary with trading frequency
        - Wider confidence intervals show higher uncertainty
        """)

        # Add confidence interval visualization
        st.subheader("Portfolio Value Projections with Confidence Intervals")

        # Create confidence interval plot
        fig_ci, ax_ci = plt.subplots(figsize=(10, 6))

        years = range(len(roth_annual))

        # Plot Roth 401k
        ax_ci.plot(years, roth_prob[0], label='Roth 401k Mean', color='blue', linewidth=2)
        if employer_match > 0:
            ax_ci.fill_between(
                years, 
                roth_prob[1][0], 
                roth_prob[1][1], 
                alpha=0.2, 
                color='blue',
                label='Roth 401k 90% CI'
            )

        # Plot Self-managed
        ax_ci.plot(years, self_prob[0], label='Self-managed Mean', color='orange', linewidth=2)
        ax_ci.fill_between(
            years, 
            self_prob[1][0], 
            self_prob[1][1], 
            alpha=0.2, 
            color='orange',
            label='Self-managed 90% CI'
        )

        # Format axes
        ax_ci.set_xlabel('Years')
        ax_ci.set_ylabel('Portfolio Value ($)')
        ax_ci.legend()
        ax_ci.grid(True)
        ax_ci.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

        st.pyplot(fig_ci)

        # Add explanation
        st.markdown("""
        ### Understanding the Confidence Intervals
        The shaded areas show the range where portfolio values are likely to fall:
        - **90% Confidence Interval**: There's a 90% chance your actual returns will fall within this range
        - **Darker lines**: Show the expected (mean) trajectory
        - **Wider intervals**: Indicate more uncertainty/risk in the investment strategy
        """)

if __name__ == "__main__":
    main() 