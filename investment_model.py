import numpy as np
import matplotlib.pyplot as plt

class InvestmentComparator:
    def __init__(self):
        # 基础参数
        self.current_age = 22
        self.retirement_age = 65
        self.investment_years = self.retirement_age - self.current_age
        
        # 投资组合配置
        self.passive_ratio = 0.80  # 80%配置到SPY/QQQ
        self.active_ratio = 0.20   # 20%配置到主动交易
        
        # 交易特征
        self.passive_trading_freq = 0.02  # 被动部分每年2%的换手率
        self.active_trading_freq = 0.30   # 主动部分每年30%的换手率
        self.active_st_ratio = 0.60      # 主动交易中60%是短期
        self.active_lt_ratio = 0.40      # 主动交易中40%是长期

        # 收益率和费用
        self.r_401k = 0.10      # Both use S&P 500 average
        self.r_passive = 0.10   # Both use S&P 500 average
        self.r_active = 0.12   # 主动投资回报率(假设12%)
        self.f_401k = 0.003    # Default 0.3% total fees
        self.f_passive = 0.001  # ETF fee
        self.f_active = 0.002   # Active management fee
        
        # 通货膨胀和增长
        self.inflation = 0.03
        self.salary_growth = 0.04
        
        # 税率
        self.current_tax_rate = 0.24  # 当前所得税率
        self.lt_capital_gains_tax = 0.15  # 长期资本利得税率
        self.st_capital_gains_tax = 0.24  # 短期资本利得税率
        self.dividend_tax = 0.15  # 股息税率
        
        # 股息收益率
        self.passive_dividend_yield = 0.015  # SPY股息率
        self.active_dividend_yield = 0.02   # 主动投资股息率
        
        self.initial_investment = 10000  # 每年投资金额（税前）
        
        self.real_salary_growth = (1 + self.salary_growth) / (1 + self.inflation) - 1
        self.real_return_401k = (1 + self.r_401k) / (1 + self.inflation) - 1
        
        # 添加波动率参数
        self.passive_volatility = 0.15  # SPY历史波动率约15%
        self.active_volatility = 0.25   # 主动投资波动率约25%
        self.correlation = 0.5    # 主动和被动投资的相关性
        self.risk_free_rate = 0.03  # 无风险利率（如美国国债）
        
        self.tax_brackets = [
            (0, 44725, 0.10),      # 2023年税率表
            (44726, 95375, 0.12),
            (95376, 182100, 0.22),
            (182101, 231250, 0.24),
            (231251, 578125, 0.35),
            (578126, float('inf'), 0.37)
        ]
        
        self.annual_income = 100000  # Default annual income
        self.salary_growth = 0.04    # Default salary growth rate
        
        # Add employer match parameters
        self.employer_match = 0.03  # 3% default match
        self.match_limit = 0.06    # Up to 6% of salary
    
    def calculate_investment_years(self):
        """Recalculate investment years when age changes"""
        return self.retirement_age - self.current_age

    def calculate_marginal_tax(self, income):
        """计算累进所得税"""
        total_tax = 0
        remaining_income = income
        
        for lower, upper, rate in self.tax_brackets:
            if remaining_income <= 0:
                break
            taxable_amount = min(upper - lower, remaining_income)
            total_tax += taxable_amount * rate
            remaining_income -= taxable_amount
        
        return total_tax / income  # 返回有效税率

    def calculate_roth_401k_returns(self):
        """Calculate combined Roth + employer match returns"""
        roth_value = 0  # After-tax Roth portion
        trad_value = 0  # Pre-tax employer match portion
        annual_values = []
        total_contributions = 0
        total_employer_match = 0
        investment_years = self.calculate_investment_years()
        
        print("\nDEBUG: Roth 401k Calculation")
        for year in range(investment_years):
            # Calculate real salary growth (adjusted for inflation)
            real_salary_growth = (1 + self.salary_growth) / (1 + self.inflation) - 1
            
            # Calculate inflation-adjusted contribution
            real_contribution = self.initial_investment * (1 + real_salary_growth)**year
            pre_tax_contribution = real_contribution * (1 + self.inflation)**year
            
            # Calculate projected income with real growth
            projected_income = self.annual_income * (1 + real_salary_growth)**year
            total_income = projected_income * (1 + self.inflation)**year
            
            # Calculate true marginal tax on this contribution
            marginal_tax = self.calculate_true_marginal_tax(total_income, pre_tax_contribution)
            tax_impact = pre_tax_contribution * marginal_tax
            
            # Calculate employer match (handle zero case)
            match_eligible_amount = min(
                pre_tax_contribution,
                total_income * self.match_limit
            )
            employer_contribution = match_eligible_amount * self.employer_match
            total_employer_match += employer_contribution
            
            # Full pre-tax amount goes into Roth
            roth_contribution = pre_tax_contribution
            total_contributions += roth_contribution
            
            # Grow both portions separately
            old_roth = roth_value
            old_trad = trad_value
            
            # Handle zero fees correctly
            growth_rate = 1 + self.r_401k - (self.f_401k if self.f_401k is not None else 0)
            
            # Grow Roth portion (tax-free)
            roth_value = (roth_value + roth_contribution) * growth_rate
            
            # Grow employer match portion (pre-tax)
            trad_value = (trad_value + employer_contribution) * growth_rate
            
            if year < 3 or year > investment_years - 3:
                print(f"Year {year}:")
                print(f"  Nominal Income: ${total_income:,.2f}")
                print(f"  Real Income: ${projected_income:,.2f}")
                print(f"  Nominal Contribution: ${pre_tax_contribution:,.2f}")
                print(f"  Real Contribution: ${real_contribution:,.2f}")
                print(f"  Active Trading: {self.active_trading_freq*100:.1f}% turnover")
                print(f"  True Marginal Tax Rate: {marginal_tax:.1%}")
                print(f"  Your Contribution: ${roth_contribution:,.2f}")
                if self.employer_match > 0:
                    print(f"  Employer Match: ${employer_contribution:,.2f} ({self.employer_match*100:.0f}% up to {self.match_limit*100:.0f}%)")
                print(f"  Growth Rate: {growth_rate:.3%}")
                print(f"  Your Account Growth: ${roth_value - old_roth - roth_contribution:,.2f}")
                if self.employer_match > 0:
                    print(f"  Employer Account Growth: ${trad_value - old_trad - employer_contribution:,.2f}")
                print(f"  Your Account Value: ${roth_value:,.2f}")
                if self.employer_match > 0:
                    print(f"  Employer Account Value: ${trad_value:,.2f}")
                print(f"  Combined Value: ${roth_value + trad_value:,.2f}")
            
            # Calculate real value (inflation-adjusted)
            real_value = (roth_value + trad_value) / (1 + self.inflation)**(year + 1)
            annual_values.append(real_value)
        
        # Apply retirement tax to traditional portion (only if there is employer match)
        final_real_value = roth_value  # Start with Roth portion
        if trad_value > 0:  # Only calculate tax if there's employer match
            retirement_tax = self.calculate_true_marginal_tax(
                total_income * (1 + self.salary_growth)**investment_years,
                trad_value
            )
            after_tax_trad = trad_value * (1 - retirement_tax)
            final_real_value += after_tax_trad
            
            print(f"\nRetirement Analysis:")
            print(f"  Total Roth Value: ${roth_value:,.2f}")
            print(f"  Total Traditional Value: ${trad_value:,.2f}")
            print(f"  Tax on Traditional: ${trad_value * retirement_tax:,.2f}")
            print(f"  After-tax Traditional: ${after_tax_trad:,.2f}")
            print(f"  Final Combined Value: ${roth_value + after_tax_trad:,.2f}")
            print(f"  Total Employer Match: ${total_employer_match:,.2f}")
        
        final_real_value = final_real_value / (1 + self.inflation)**investment_years
        return final_real_value, annual_values, total_contributions

    def calculate_true_marginal_tax(self, income, contribution, year=0):
        """Calculate true marginal tax rate on contribution, adjusted for future growth"""
        # Project income growth
        projected_income = income * (1 + self.salary_growth)**year
        
        # Calculate tax without and with contribution
        tax_without = self.calculate_total_tax(projected_income)
        tax_with = self.calculate_total_tax(projected_income + contribution)
        
        # True marginal rate is the difference
        return (tax_with - tax_without) / contribution

    def calculate_total_tax(self, income):
        """Calculate total tax (not rate) for a given income"""
        total_tax = 0
        remaining_income = income
        
        for lower, upper, rate in self.tax_brackets:
            if remaining_income <= 0:
                break
            taxable_amount = min(upper - lower, remaining_income)
            total_tax += taxable_amount * rate
            remaining_income -= taxable_amount
        
        return total_tax

    def calculate_portfolio_return(self):
        """计算投资组合的综合净收益率"""
        passive_return = self.r_passive - self.f_passive
        active_return = self.r_active - self.f_active
        
        portfolio_return = (
            self.passive_ratio * passive_return +
            self.active_ratio * active_return
        )
        return portfolio_return

    def calculate_self_investment_returns(self, liquidation_percent=100):
        """Calculate self-managed returns with proper tax treatment"""
        passive_value = 0
        active_value = 0
        total_contributions = 0
        annual_values = []
        
        # Track cost basis and unrealized gains
        passive_cost_basis = 0
        active_cost_basis = 0
        passive_unrealized_gains = 0
        active_unrealized_gains = 0
        
        print("\nDEBUG: Self-Managed Calculation")
        print(f"DEBUG: Initial passive_ratio = {self.passive_ratio:.1%}, active_ratio = {1 - self.passive_ratio:.1%}")
        print(f"DEBUG: Active trading frequency = {self.active_trading_freq:.1%}/year")
        
        for year in range(self.calculate_investment_years()):
            # Calculate real salary growth (adjusted for inflation)
            real_salary_growth = (1 + self.salary_growth) / (1 + self.inflation) - 1
            
            # Calculate inflation-adjusted contribution
            real_contribution = self.initial_investment * (1 + real_salary_growth)**year
            pre_tax_contribution = real_contribution * (1 + self.inflation)**year
            
            # Calculate projected income with real growth
            projected_income = self.annual_income * (1 + real_salary_growth)**year
            total_income = projected_income * (1 + self.inflation)**year
            
            # Calculate true marginal tax based on projected income
            marginal_tax = self.calculate_true_marginal_tax(projected_income, pre_tax_contribution, year)
            tax_impact = pre_tax_contribution * marginal_tax
            
            # Only invest after-tax amount
            contribution = pre_tax_contribution * (1 - marginal_tax)
            total_contributions += contribution
            
            # Split between passive and active
            passive_contribution = contribution * self.passive_ratio
            active_contribution = contribution * (1 - self.passive_ratio)
            
            # Update cost basis with after-tax contributions
            passive_cost_basis += passive_contribution
            active_cost_basis += active_contribution
            
            old_passive = passive_value
            old_active = active_value

            # Passive portion (buy and hold)
            if passive_value > 0 or passive_contribution > 0:
                passive_value = (passive_value + passive_contribution) * (1 + self.r_passive - self.f_passive)
                passive_growth = passive_value - (old_passive + passive_contribution)
                passive_unrealized_gains += passive_growth
                
                # Only dividends are taxed annually
                passive_dividend = passive_value * self.passive_dividend_yield
                passive_dividend_tax = passive_dividend * self.dividend_tax
                passive_value = passive_value - passive_dividend_tax
            else:
                passive_value = passive_contribution

            # Active portion (with trading) - only if active ratio > 0
            if self.active_ratio > 0:
                if active_value > 0 or active_contribution > 0:
                    active_value = (active_value + active_contribution) * (1 + self.r_active - self.f_active)
                    active_growth = active_value - (old_active + active_contribution)
                    
                    # Tax realized gains from trading
                    realized_gains = active_value * self.active_trading_freq
                    unrealized_gains = active_growth - realized_gains
                    active_unrealized_gains += unrealized_gains
                    
                    realized_gains_tax = realized_gains * (
                        0.6 * self.st_capital_gains_tax + 
                        0.4 * self.lt_capital_gains_tax
                    )
                    
                    active_dividend = active_value * self.active_dividend_yield
                    active_dividend_tax = active_dividend * self.dividend_tax
                    
                    active_value = active_value - realized_gains_tax - active_dividend_tax
                else:
                    active_value = active_contribution

            total_value = passive_value + active_value

            if year < 3 or year > self.calculate_investment_years() - 3:
                print(f"\nYear {year}:")
                print(f"  Nominal Income: ${total_income:,.2f}")
                print(f"  Real Income: ${projected_income:,.2f}")
                print(f"  Nominal Contribution: ${pre_tax_contribution:,.2f}")
                print(f"  Real Contribution: ${real_contribution:,.2f}")
                print(f"  Active Trading: {self.active_trading_freq*100:.1f}% turnover")
                print(f"  True Marginal Tax Rate: {marginal_tax:.1%}")
                print(f"  Pre-tax Amount: ${pre_tax_contribution:,.2f}")
                print(f"  Tax Paid: ${tax_impact:,.2f}")
                print(f"  After-tax Investment: ${contribution:,.2f}")
                print(f"  Passive Growth: ${passive_growth:,.2f}")
                print(f"  Active Growth: ${active_growth:,.2f}")
                print(f"  Dividends: ${passive_dividend + active_dividend:,.2f}")
                print(f"  Dividend Tax: ${passive_dividend_tax + active_dividend_tax:,.2f}")
                print(f"  Realized Gains Tax: ${realized_gains_tax:,.2f}")
                print(f"  Total Value: ${total_value:,.2f}")

            real_value = total_value / (1 + self.inflation)**(year + 1)
            annual_values.append(real_value)

        # Calculate projected retirement income for capital gains tax
        final_income = self.annual_income * (1 + self.salary_growth)**(self.calculate_investment_years())
        retirement_cg_tax = self.projected_capital_gains_tax(final_income)
        
        # Apply final liquidation tax using projected rate
        if passive_unrealized_gains + active_unrealized_gains > 0:
            liquidation_ratio = liquidation_percent / 100
            taxable_gains = (passive_unrealized_gains + active_unrealized_gains) * liquidation_ratio
            final_tax = taxable_gains * retirement_cg_tax
            total_value -= final_tax
            
            print(f"\nFinal Liquidation at Retirement ({liquidation_percent:.0f}%):")
            print(f"  Projected Retirement Income: ${final_income:,.2f}")
            print(f"  Projected Capital Gains Rate: {retirement_cg_tax:.1%}")
            print(f"  Total Unrealized Gains: ${passive_unrealized_gains + active_unrealized_gains:,.2f}")
            print(f"  Taxable Gains: ${taxable_gains:,.2f}")
            print(f"  Capital Gains Tax: ${final_tax:,.2f}")
            print(f"  Final After-tax Value: ${total_value:,.2f}")
            
            real_value = total_value / (1 + self.inflation)**(self.calculate_investment_years())

        return real_value, annual_values, total_contributions

    def sensitivity_analysis(self):
        """Extended sensitivity analysis with realistic scenarios"""
        plt.figure(figsize=(15, 10))
        
        # 1. Active returns including underperformance
        plt.subplot(2, 2, 1)
        active_returns = [0.08, 0.09, 0.10, 0.11, 0.12]  # 10% is market return
        values_by_return = []
        
        original_active_return = self.r_active
        for r in active_returns:
            self.r_active = r
            value, _, _ = self.calculate_self_investment_returns()
            values_by_return.append(value)
        
        self.r_active = original_active_return
        
        plt.plot(active_returns, values_by_return, marker='o')
        plt.axvline(x=0.10, color='r', linestyle='--', label='Market Return')
        plt.title('Impact of Active Return (Including Underperformance)')
        plt.xlabel('Active Investment Return')
        plt.ylabel('Final Real Value ($)')
        plt.grid(True)
        plt.legend()
        
        # 2. 主动交易频率的敏感性
        plt.subplot(2, 2, 2)
        active_freqs = [0.1, 0.2, 0.3, 0.4, 0.5]
        values_by_freq = []
        
        original_active_freq = self.active_trading_freq
        for freq in active_freqs:
            self.active_trading_freq = freq
            value, _, _ = self.calculate_self_investment_returns()
            values_by_freq.append(value)
        
        self.active_trading_freq = original_active_freq
        
        plt.plot(active_freqs, values_by_freq, marker='s', color='red')
        plt.title('Impact of Active Trading Frequency')
        plt.xlabel('Active Trading Frequency')
        plt.ylabel('Final Real Value ($)')
        plt.ylim(min(values_by_freq) * 0.95, max(values_by_freq) * 1.05)  # Normalize Y-axis
        plt.grid(True)

        # 3. 主动交易频率的敏感性
        plt.subplot(2, 2, 3)
        active_ratios = [0.1, 0.2, 0.3, 0.4, 0.5]
        values_by_active_ratio = []
        
        original_active_ratio = self.active_ratio
        original_passive_ratio = self.passive_ratio
        
        for ratio in active_ratios:
            self.active_ratio = ratio
            self.passive_ratio = 1 - ratio
            value, _, _ = self.calculate_self_investment_returns()
            values_by_active_ratio.append(value)
        
        self.active_ratio = original_active_ratio
        self.passive_ratio = original_passive_ratio
        
        plt.plot(active_ratios, values_by_active_ratio, marker='d', color='green')
        plt.title('Impact of Active Investment Allocation')
        plt.xlabel('Active Investment Allocation')
        plt.ylabel('Final Real Value ($)')
        plt.ylim(min(values_by_active_ratio) * 0.95, max(values_by_active_ratio) * 1.05)  # Normalize Y-axis
        plt.grid(True)
        
        plt.tight_layout()
        plt.show()

    def calculate_returns_with_volatility(self, is_roth=False):
        """Monte Carlo with fat-tailed distributions for more realistic modeling"""
        num_simulations = 1000
        simulation_results = []
        annual_values_all = []
        
        investment_years = self.calculate_investment_years()
        
        # Use Student's t-distribution for fat tails
        degrees_of_freedom = 5  # Lower = fatter tails
        
        for _ in range(num_simulations):
            total_value = 0
            annual_values = []
            
            # Generate returns from t-distribution
            if is_roth:
                returns = (np.random.standard_t(degrees_of_freedom, investment_years) * 
                          self.passive_volatility + self.r_401k)
            else:
                passive_returns = (np.random.standard_t(degrees_of_freedom, investment_years) * 
                                 self.passive_volatility + self.r_passive)
                active_returns = (np.random.standard_t(degrees_of_freedom, investment_years) * 
                                self.active_volatility + self.r_active)
                
                for year in range(investment_years):
                    # 计算当年供款
                    contribution = self.initial_investment * (1 + self.salary_growth)**year
                    
                    # 投资组合增长
                    if total_value > 0:
                        passive_growth = total_value * self.passive_ratio * passive_returns[year]
                        active_growth = total_value * self.active_ratio * active_returns[year]
                        total_growth = passive_growth + active_growth
                        
                        # 考虑费用
                        total_value = (total_value + total_growth) * (1 - self.f_passive * self.passive_ratio - self.f_active * self.active_ratio)
                    
                    total_value += contribution
                    annual_values.append(total_value)
            
            # 考虑通货膨胀
            real_final_value = total_value / (1 + self.inflation)**investment_years
            simulation_results.append(real_final_value)
            annual_values_all.append(annual_values)
        
        mean_final_value = np.mean(simulation_results)
        percentile_5 = np.percentile(simulation_results, 5)
        percentile_95 = np.percentile(simulation_results, 95)
        
        return mean_final_value, annual_values_all, simulation_results

    def calculate_risk_metrics(self):
        """计算综合风险指标"""
        mean_value, _, returns = self.calculate_returns_with_volatility()
        
        # 计算年化收益率
        years = self.investment_years
        annual_returns = [(r / self.initial_investment)**(1/years) - 1 for r in returns]
        
        # 计算风险指标
        returns_array = np.array(annual_returns)
        mean_return = np.mean(returns_array)
        std_dev = np.std(returns_array)
        negative_returns = returns_array[returns_array < 0]
        
        metrics = {
            'mean_return': mean_return,
            'volatility': std_dev,
            'sharpe_ratio': (mean_return - self.risk_free_rate) / std_dev if std_dev != 0 else 0,
            'sortino_ratio': (mean_return - self.risk_free_rate) / np.std(negative_returns) if len(negative_returns) > 0 else 0,
            'max_drawdown': abs(np.min(returns_array)) if len(returns_array) > 0 else 0,
            'var_95': np.percentile(returns_array, 5)
        }
        
        return metrics

    def calculate_rebalancing_costs(self, passive_value, active_value):
        """Calculates rebalancing tax when asset allocation drifts beyond threshold"""
        total_value = passive_value + active_value
        current_passive_ratio = passive_value / total_value
        target_passive_ratio = self.passive_ratio

        if abs(current_passive_ratio - target_passive_ratio) > 0.05:  # 5% drift threshold
            rebalancing_amount = abs(target_passive_ratio - current_passive_ratio) * total_value
            rebalancing_tax = rebalancing_amount * self.lt_capital_gains_tax  # Assume long-term
            return rebalancing_tax
        return 0

    def simulate_market_cycles(self):
        """改进的市场周期模拟，考虑通货膨胀和税收影响"""
        investment_years = self.calculate_investment_years()
        
        market_cycles = {
            'bull': {'prob': 0.6, 'return': 0.15, 'volatility': 0.12},
            'bear': {'prob': 0.3, 'return': -0.10, 'volatility': 0.25},
            'crash': {'prob': 0.1, 'return': -0.30, 'volatility': 0.40}
        }
        
        cycle_returns = []
        real_returns = []
        after_tax_returns = []
        
        for year in range(investment_years):
            # 选择市场周期
            cycles = list(market_cycles.keys())
            probabilities = [market_cycles[c]['prob'] for c in cycles]
            cycle = np.random.choice(cycles, p=probabilities)
            
            # 生成名义回报
            nominal_return = np.random.normal(
                market_cycles[cycle]['return'],
                market_cycles[cycle]['volatility']
            )
            
            # 计算实际回报（考虑通货膨胀）
            real_return = (1 + nominal_return) / (1 + self.inflation) - 1
            
            # 计算税后回报（简化处理，假设50%收益需要缴税）
            if nominal_return > 0:
                taxable_portion = nominal_return * 0.5
                tax = taxable_portion * self.lt_capital_gains_tax
                after_tax_return = nominal_return - tax
            else:
                after_tax_return = nominal_return
            
            cycle_returns.append(nominal_return)
            real_returns.append(real_return)
            after_tax_returns.append(after_tax_return)
        
        return {
            'nominal': cycle_returns,
            'real': real_returns,
            'after_tax': after_tax_returns
        }

    def simulate_withdrawal_phase(self):
        """Simulates retirement withdrawal and checks portfolio longevity."""
        withdrawal_rates = [0.03, 0.04, 0.05]  # Different withdrawal rates
        success_rates = {}
    
        for rate in withdrawal_rates:
            successes = 0
            for _ in range(1000):  # 1000 Monte Carlo simulations
                portfolio = self.calculate_self_investment_returns()[0]
                years_sustained = 0
                withdrawal = portfolio * rate  # Initial withdrawal

                while portfolio > 0 and years_sustained < 30:
                    portfolio -= withdrawal  # Withdraw funds
                    portfolio *= (1 + np.random.normal(self.calculate_portfolio_return(), 0.12))  # Random return
                    withdrawal *= (1 + self.inflation)  # Adjust for inflation
                    years_sustained += 1

                if years_sustained >= 30:
                    successes += 1
            
            success_rates[rate] = successes / 1000  # Probability of success
        
        return success_rates

    def print_comprehensive_analysis(self):
        """打印综合分析结果"""
        print("\n=== 综合投资分析 ===")
        
        # 基础回报分析
        roth_value, _, roth_contributions = self.calculate_roth_401k_returns()
        self_value, _, self_contributions = self.calculate_self_investment_returns()
        
        # 风险指标
        risk_metrics = self.calculate_risk_metrics()
        
        # 退休提取分析
        withdrawal_success = self.simulate_withdrawal_phase()
        
        print("\n1. 基础回报分析:")
        print(f"Roth 401k 最终价值: ${roth_value:,.2f}")
        print(f"自主投资最终价值: ${self_value:,.2f}")
        print(f"相对收益差异: {((self_value/roth_value)-1)*100:.1f}%")
        print(f"Roth 401k 总供款: ${roth_contributions:,.2f}")
        print(f"自主投资总供款: ${self_contributions:,.2f}")
        
        print("\n2. 风险指标:")
        print(f"年化平均回报率: {risk_metrics['mean_return']*100:.1f}%")
        print(f"年化波动率: {risk_metrics['volatility']*100:.1f}%")
        print(f"夏普比率: {risk_metrics['sharpe_ratio']:.2f}")
        print(f"索提诺比率: {risk_metrics['sortino_ratio']:.2f}")
        print(f"最大回撤: {risk_metrics['max_drawdown']*100:.1f}%")
        print(f"95%置信区间下限年化回报: {risk_metrics['var_95']*100:.1f}%")
        
        print("\n3. 退休提取分析:")
        for rate, success in withdrawal_success.items():
            print(f"{rate*100}%提取率的成功概率: {success*100:.1f}%")

    def calculate_effective_tax_rate(self, value, gains, trading_freq, is_active=False):
        """计算投资的实际税负"""
        trading_gains = value * trading_freq * gains
        
        if is_active:
            st_tax = trading_gains * 0.6 * self.st_capital_gains_tax
            lt_tax = trading_gains * 0.4 * self.lt_capital_gains_tax
            return st_tax + lt_tax
        else:
            return trading_gains * self.lt_capital_gains_tax

    def projected_capital_gains_tax(self, retirement_income):
        """Estimate capital gains tax rate at retirement based on projected income"""
        # Basic capital gains brackets (2024)
        cg_brackets = [
            (0, 44625, 0.0),       # 0% bracket
            (44626, 492300, 0.15), # 15% bracket
            (492301, float('inf'), 0.20)  # 20% bracket
        ]
        
        # Add 3.8% NIIT for high incomes
        niit_threshold = 200000
        base_rate = 0.0
        
        # Find applicable capital gains rate
        for lower, upper, rate in cg_brackets:
            if retirement_income > lower and retirement_income <= upper:
                base_rate = rate
                break
        
        # Add NIIT if applicable
        if retirement_income > niit_threshold:
            base_rate += 0.038
        
        return base_rate
