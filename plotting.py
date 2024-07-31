#
# plot
#

import plotly.graph_objects as go
import numpy as np


from pandas import DataFrame


def pivot_plot(data: DataFrame) -> None:
    
    def ypos(x):
        return x['Low']-1e-3 if x['pivot']==2 else x['High']+1e-3 if x['pivot']==1 else np.nan

    data['delta-y'] = data.apply(lambda row: ypos(row), axis=1)

    fig = go.Figure(data=[go.Candlestick(x=data.index,
                open  = data['Open'],
                high  = data['High'],
                low   = data['Low'],
                close = data['Close'])])

    fig.add_scatter(
            x      = data.index, 
            y      = data['delta-y'], 
            mode   = "markers",
            marker = 
                dict(
                    size  = 5, 
                    color = "MediumPurple"
                    ),
            name="pivot"
        )

    fig.update_layout(xaxis_rangeslider_visible=False)
    fig.show()



