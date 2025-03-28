from pathlib import Path
import pandas as pd
import json

from plotly.subplots import make_subplots
from plotly import graph_objects as go
from plotly import express as px

class FinLoad:
    def load_init_holdings(path: Path, YEAR: int):
        if path.exists():
            with open(f"{path}/{YEAR}/{YEAR}_init.json") as file:
                data = file.read()
            init_holdings = json.loads(data)
            return init_holdings
        else:
            print(f"{path} does not exist.")
            return None

    def load_cashflow(path: Path, YEAR: int):
        if path.exists():
            dfl = list()
            for i in range(1,13):
                try:
                    filepath = f"{path}/{YEAR}/cashflow/{YEAR}-{i:0=2}_cashflow.csv"
                    df = pd.read_csv(filepath, skipinitialspace=True, na_filter=False)
                except Exception as e:
                    print(e)
                    continue
                df.columns = df.columns.str.strip() # remove whitespaces from columns
                df.Category = df.Category.str.strip()
                df.Subcategory = df.Subcategory.str.strip()
                df.Type = df.Type.str.strip()
                df.Coin = df.Coin.str.strip()
                dfl.append(df)
            df_year_cashflow = pd.concat(dfl)
            df_year_cashflow['Date'] = pd.to_datetime(df_year_cashflow['Date'])
            df_year_cashflow.set_index('Date',inplace=True)
            return df_year_cashflow
        else:
            print(f"{path} does not exist.")
            return None

    def load_investments(path: Path, YEAR: int):
        if path.exists():
            dfl = list()
            for i in range(1,13):
                try:
                    filepath = f"{path}/{YEAR}/investments/{YEAR}-{i:0=2}_investments.csv"
                    df = pd.read_csv(filepath, skipinitialspace=True, na_filter=False)

                    df.columns = df.columns.str.strip() # remove whitespaces from columns
                    df.Category = df.Category.str.strip()
                    df.Subcategory = df.Subcategory.str.strip()
                    df.Type = df.Type.str.strip()
                    df.Symbol = df.Symbol.str.strip()
                    if df.empty:
                        continue
                    else:
                        dfl.append(df)
                except Exception as e:
                    print(e)
                    continue

            df_year_investments = pd.concat(dfl)
            df_year_investments['Date'] = pd.to_datetime(df_year_investments['Date'])
            df_year_investments.set_index('Date',inplace=True)
            return df_year_investments
        else:
            print(f"{path} does not exist.")
            return None

class FinCalc:
    def calc_monthly_cashflow(df_year_cashflow):
        incomes = df_year_cashflow.loc[(df_year_cashflow["Category"] != "Transfer") & (df_year_cashflow["Qty"] > 0)]
        liabilities = df_year_cashflow.loc[(df_year_cashflow["Category"] != "Transfer") & (df_year_cashflow["Qty"] <= 0)]

        m_incomes = incomes.resample(rule='ME')['Qty'].sum()
        m_liab = liabilities.resample(rule='ME')['Qty'].sum()
        m_savings = incomes.resample(rule='ME')['Qty'].sum() + liabilities.resample(rule='ME')['Qty'].sum()
        m_savingrate = df_year_cashflow.resample(rule='ME')['Qty'].sum() / incomes.resample(rule='ME')['Qty'].sum()

        zipped = zip(
            m_incomes.index,
            m_incomes.values,
            m_liab.values,
            m_savings.values,
            m_savingrate.values,
        )

        df_m_cashflow = pd.DataFrame(zipped,columns=["Date","incomes","liabilities","savings","saving_rate"])

        return df_m_cashflow

    def calc_expenses(df): # For donut plot expenses
        df_expenses = df.loc[ ((df["Category"] != "Transfer") & (df["Qty"] < 0)) ]
        expenses = df_expenses['Qty'].abs().values
        df_expenses = df_expenses.assign(Expenses = expenses) # Creates new columns "Expenses"
        
        return df_expenses

class FinPlot:
    def plot_cashflow(df_cashflow):
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Bar(
                x=df_cashflow["Date"],
                y=df_cashflow["incomes"],
                name='incomes',
                marker_color='indianred'
            ),
            secondary_y = False
        )
        fig.add_trace(
            go.Bar(
                x=df_cashflow["Date"],
                y=df_cashflow["liabilities"].abs(),
                name='liabilities',
                marker_color='lightsalmon'
            ),
            secondary_y = False
        )
        fig.add_trace(
            go.Scatter(x=df_cashflow["Date"],y=df_cashflow["saving_rate"]*100, line=dict(color='red'), name='% Saving Rate'),
            secondary_y = True
        )
        
        fig.update_layout(
            #title = "Cashflow",
            title = {'text': 'Cashflow  Graph', 'x': 0.4, 'y': 0.85},
            barmode='group', xaxis_tickangle=0,
            width=1000, height=400,
            yaxis=dict(
                title=dict(text="<b>Social Credits</b>"),
                side="left",
                tickmode = 'array',
                tickvals = [0, 500, 1000, 1500, 2000, 2500],
                ticktext = ['0€', '500€', '1000€', '1500€', '2000€', '2500€'],
                showgrid = False
            ),
            yaxis2=dict(
                title=dict(text="<b>Saving Rate</b>"),
                side="right",
                range=[0, 100],
                overlaying="y",
                tickmode = 'array',
                tickvals = [40, 60, 80],
                ticktext = ['40%', '60%', '80%']
            ),
        )

        return fig



    def plot_expenses_donut(df_expenses, plot_categories = False):
        pxfig = px.sunburst(df_expenses, path=['Category', 'Subcategory'], values='Expenses')
        
        labels = pxfig['data'][0]['labels'].tolist()
        parents = pxfig['data'][0]['parents'].tolist()
        ids = pxfig['data'][0]['ids'].tolist()
        if plot_categories:
            values = None
        else:
            values = pxfig['data'][0]['values'].tolist()
    
        colors = ['#FF5733', '#33FF57', '#3357FF', '#F1C40F', '#8E44AD', '#E67E22']
        
        fig = go.Figure(
            go.Sunburst(
                labels = labels,
                parents = parents,
                values = values,
                ids = ids,
                branchvalues = "total",
                marker=dict(colors=colors)
            )
        )
        fig.update_layout(
            title = dict(text="Expenses", x=0.5, y=0.95),
            margin = dict(t=60, l=10, r=10, b=10),
            height = 500, width = 500
        )
        return fig
    
    def plot_hist_expenses_month(df_months, months):
        specs = [[dict(type="domain") for i in range(3)] for j in range(4)]
        fig = make_subplots(
            4, 3, # n rows, n cols
            specs=specs,
            subplot_titles=months,
            horizontal_spacing = 0.05,
            vertical_spacing = 0,
        )
        
        for n in range(0, len(df_months)):
            row_pos = 1 if n < 3 else 2 if n < 6 else 3 if n < 9 else 4
            col_pos = n+1 if n < 3 else n+1-3 if n < 6 else n+1-6 if n < 9 else n+1-9
            
            df_expenses = PF_Basic.extract_hist_expenses(df_months[n])
            pxfig = px.sunburst(df_expenses, path=['Category', 'Subcategory'], values='Expenses')
            
            labels = pxfig['data'][0]['labels'].tolist()
            parents = pxfig['data'][0]['parents'].tolist()
            ids = pxfig['data'][0]['ids'].tolist()
            values = pxfig['data'][0]['values'].tolist()
    
            fig.add_trace(
                go.Sunburst(
                    labels = labels,
                    parents = parents,
                    values = values,
                    ids = ids,
                    branchvalues = "total",
                    insidetextorientation='radial'
                ),
                row_pos, col_pos # row position, col position
            )
        #fig.update_traces(hole=.5, hoverinfo="label+percent+value")
        
        y_annot_row1 = 0.970; y_annot_row2 = 0.720; y_annot_row3 = 0.470; y_annot_row4 = 0.220
        x_annot_col1 = 0.147; x_annot_col2 = 0.50; x_annot_col3 = 0.856; 
        
        fig.update_layout(
            title = dict(text='Monthly Expenses 2024', x=0.5,y=0.98),
            width = 800,
            height = 1200,
            autosize=False,
            margin=dict(l=50,r=50,b=50,t=50),
            #uniformtext_minsize=10,
            #uniformtext_mode='hide',
            annotations=[
                dict(text="January  ", x=x_annot_col1, y=y_annot_row1, font_size=14, showarrow=False),
                dict(text="February ", x=x_annot_col2, y=y_annot_row1, font_size=14, showarrow=False),
                dict(text="March    ", x=x_annot_col3, y=y_annot_row1, font_size=14, showarrow=False),
                dict(text="April    ", x=x_annot_col1, y=y_annot_row2, font_size=14, showarrow=False),
                dict(text="May      ", x=x_annot_col2, y=y_annot_row2, font_size=14, showarrow=False),
                dict(text="June     ", x=x_annot_col3, y=y_annot_row2, font_size=14, showarrow=False),
                dict(text="July     ", x=x_annot_col1, y=y_annot_row3, font_size=14, showarrow=False),
                dict(text="August   ", x=x_annot_col2, y=y_annot_row3, font_size=14, showarrow=False),
                dict(text="September", x=x_annot_col3, y=y_annot_row3, font_size=14, showarrow=False),
                dict(text="October  ", x=x_annot_col1, y=y_annot_row4, font_size=14, showarrow=False),
                dict(text="November ", x=x_annot_col2, y=y_annot_row4, font_size=14, showarrow=False),
                dict(text="December ", x=x_annot_col3, y=y_annot_row4, font_size=14, showarrow=False),
            ]
        )
        return fig
