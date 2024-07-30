import numpy as np
import plotly.graph_objects as go


#
# definitions
#

class Pivot:
    LOW    = 2
    HIGH   = 1
    NONE   = 0
    WINDOW = 6
    



#
#   detects if a candle is a pivot point
#
#   ------|------
#   ^   window   ^
#    
#   args: 
#       candle index: index of candle 
#       pivot_window: before and after candle to test if pivot
#        
#   returns: 
#       Pivot.LOW, 
#       Pivot.HIGH, 
#       Pivot.LOW | Pivot.HIGH if both 
#       Pivot.NONE if no pivot
#
def pivot_candle(data, candle_idx, pivot_window):
    
    if candle_idx < pivot_window or (candle_idx + pivot_window) >= len(data):
        return Pivot.NONE
    
    window = range(candle_idx - pivot_window, candle_idx + pivot_window +1)
    
    pivot_low = Pivot.LOW  
    for i in window:     # if current candle low is not window min, it's not a pivot
        if data.iloc[i].Low < data.iloc[candle_idx].Low:
            pivot_low = Pivot.NONE
            break
            
    pivot_high = Pivot.HIGH 
    for i in window:     # if curr. candle high is not windows max, it's not a pivot         
        if data.iloc[i].High > data.iloc[candle_idx].High:
            pivot_high = Pivot.NONE
            break
            
    return pivot_high | pivot_low        



def pivot(data, pivot_window):
    return data.apply(lambda x: pivot_candle(data, x.name, pivot_window), axis=1)   
 

#
# alternative to pivot_candle with Close instead of extreme
#
def pivot_candle_alt(data, candle_idx, pivot_window):
    
    if candle_idx < pivot_window or (candle_idx + pivot_window) >= len(data):
        return Pivot.NONE
    
    r = range(candle_idx - pivot_window, candle_idx + pivot_window +1)
    
    pivot_low = Pivot.LOW  
    for i in r:     # if current low < candle low, it's not a pivot
        if data.iloc[i].Close < data.iloc[candle_idx].Close:
            pivot_low = Pivot.NONE
            break
            
    pivot_high = Pivot.HIGH
    for i in r:     # if current high > candle high, it's not a pivot         
        if data.iloc[i].Close > data.iloc[candle_idx].Close:
            pivot_high = Pivot.NONE
            break
            
    return pivot_high | pivot_low        


def pivot_alt(data, pivot_window = Pivot.WINDOW):
    return data.apply(lambda x: pivot_candle_alt(data, x.name, pivot_window), axis=1)   
  


#
# plot
#
def pivot_plot(data):
    
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



