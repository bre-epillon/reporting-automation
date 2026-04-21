USAGE = """
## How to use this dashboard

Latest ABE&MBE file is automatically imported for the most recent quarter.

1. Last Month Movements provides a summary of the movements in the last month.
2. Last Quarter Movements provides a summary of the movements in the last quarter.
3. Claim Analyzer allows to analyze the claims at a granular level and offers a graphical representation of the claim evolution over time.
4. Policy Analyzer allows to analyze the data at policy level and offers.
5. One Dollar Claims Analyzer Tool provides a shortcut to analyze claims-level data based on the transactions data imported in the main page.
"""

DETAILS = """
This dashboard is designed to facilitate the Monte Carlo simulation of Barents RE claims based on historical data.
The process involves the following key steps:

1. **Data Import**: Users upload the ABE&MBE file and IBNR file for the most recent quarter. The system extracts essential data, including ultimate premiums, incurred attritional claims, and incurred large claims.
2. **Sub LoB Creation**: The imported data is processed to create sub-lines of business (sub LoBs) for each underwriting year (UWY). This involves calculating incurred loss ratios for both attritional and large claims.
3. **Unearned Loss Ratio Simulation**: A Monte Carlo simulation is performed to model the unearned loss ratios for each LoB. This step uses parameters derived from the ABE&MBE file, allowing for adjustments as needed.
4. **Analysis and Visualization**: The results of the simulations are presented through various tables and visualizations, enabling users to analyze the data effectively.
"""

NAVIGATION = """
## Navigation
1. **Upload Files**: Upload the ABE&MBE file and IBNR file for the most recent quarter.
2. **Simulation**: Run the Monte Carlo simulation to model the unearned loss ratios for each LoB.
3. **Analysis**: Explore the data and analysis provided for each LoB.
"""

DISCLAIMER = """
**Disclaimer**: This tool is intended for internal use by Barents RE and should not be shared externally. 
The results are based on historical data and assumptions that may not hold in future scenarios. 
Users should exercise caution and consider additional factors when making decisions based on the simulation outcomes.

This tool is provided "as is" without warranty of any kind.
"""
