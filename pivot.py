from pandas import DataFrame, Series

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
def pivot_candle(data: DataFrame, candle_idx: int, pivot_window: int) -> int:
    
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



def pivot(data: DataFrame, pivot_window: int) -> Series:
    return data.apply(lambda x: pivot_candle(data, x.name, pivot_window), axis=1)   
 

