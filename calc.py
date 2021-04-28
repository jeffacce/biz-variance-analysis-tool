import pandas as pd
import numpy as np


def agg_and_calc_mean_rate(df, idx_cols, rate_col, vol_col):
    val_col = 'val'
    result = df.copy()
    result[val_col] = result[rate_col] * result[vol_col]
    result = result.groupby(idx_cols)[[val_col, vol_col]].sum()
    
    # Note: how do you handle rate NAs/infs here resulting from sum(volume) == 0 after groupby?
    # it's probably safe to drop them,
    # since sum(volume) == 0 means no weight to calculate a weighted mean rate from;
    # rate NAs could also come from missing rates in the raw data, and we drop them here as well (because they are NAs anyway).
    result[rate_col] = (result[val_col] / result[vol_col]).replace([np.inf, -np.inf], np.nan)
    result = result[~result[rate_col].isna()]
    result = result.reset_index()
    return result


def merge_and_impute_missing(df_old, df_new, idx_cols, rate_col='rate', vol_col='vol'):
    df = pd.merge(
        df_old, df_new,
        how='outer',
        on=idx_cols,
        suffixes=('_old', '_new'),
    )
    
    # after merging df_old and df_new,
    # rows that only appear in one of the dataframes will have NA values.
    # if volume is NA, assume it is 0.
    # if rate is NA, assume it is unchanged from old to new (copy from the non-empty rate column to the empty rate column)
    df[vol_col+'_old'].replace(np.nan, 0, inplace=True)
    df[vol_col+'_new'].replace(np.nan, 0, inplace=True)
    
    # there's a shorter way to write this but it involves OR on NAs, which I find disgusting
    # so I'm just going to write this the dumb way, namely:
    # fill old rate NAs with new rates; fill new rate NAs with old rates.
    old_rate_NA_mask = df[rate_col+'_old'].isna()
    df.loc[old_rate_NA_mask, rate_col+'_old'] = df.loc[old_rate_NA_mask, rate_col+'_new']
    
    new_rate_NA_mask = df[rate_col+'_new'].isna()
    df.loc[new_rate_NA_mask, rate_col+'_new'] = df.loc[new_rate_NA_mask, rate_col+'_old']
    
    return df


def calc_rate(df_old, df_new, idx_cols=[], rate_col='rate', vol_col='vol'):
    df_old[rate_col] = df_old[rate_col].astype(float)
    df_old[vol_col] = df_old[vol_col].astype(float)
    df_new[rate_col] = df_new[rate_col].astype(float)
    df_new[vol_col] = df_new[vol_col].astype(float)
    
    df_old = df_old[~df_old[rate_col].isna()]
    df_new = df_new[~df_new[rate_col].isna()]
    
    val_col = 'val'
    if len(idx_cols) > 0:
        df_old = agg_and_calc_mean_rate(df_old, idx_cols, rate_col, vol_col)
        df_new = agg_and_calc_mean_rate(df_new, idx_cols, rate_col, vol_col)
        df = merge_and_impute_missing(df_old, df_new, idx_cols, rate_col, vol_col)    

        df[rate_col+'_impact'] = (df[rate_col+'_new'] - df[rate_col+'_old']) * df[vol_col+'_old']
        result = df[rate_col+'_impact'].sum() / df[vol_col+'_old'].sum()
    else:
        result = (
            (df_new[rate_col] * df_new[vol_col]).sum() / df_new[vol_col].sum() -
            (df_old[rate_col] * df_old[vol_col]).sum() / df_old[vol_col].sum()
        )
        if pd.isna(result) or np.isinf(result):
            result = 0  # since we dropped all rate NAs at the beginning, NAs/infs must come from sum(volume) == 0
    return result


# returns mix of the last column in `idx_cols`.
def calc_mix_one_level(df_old, df_new, idx_cols, rate_col='rate', vol_col='vol'):
    val_col = 'val'
    df_old = agg_and_calc_mean_rate(df_old, idx_cols, rate_col, vol_col)
    df_new = agg_and_calc_mean_rate(df_new, idx_cols, rate_col, vol_col)
    df = merge_and_impute_missing(df_old, df_new, idx_cols, rate_col, vol_col)
    
    idx_cols_parent_lvl = idx_cols[:-1]
    if len(idx_cols_parent_lvl) > 0:
        parent_lvl = df.groupby(idx_cols_parent_lvl)[[
            val_col+'_new', val_col+'_old',
            vol_col+'_new', vol_col+'_old',
        ]].sum()
        parent_lvl[rate_col+'_new'] = parent_lvl[val_col+'_new'] / parent_lvl[vol_col+'_new']
        parent_lvl[rate_col+'_old'] = parent_lvl[val_col+'_old'] / parent_lvl[vol_col+'_old']
        parent_lvl = parent_lvl.reset_index()
    
        result = pd.merge(
            df, parent_lvl,
            on=idx_cols_parent_lvl,
            how='left',
            suffixes=('_child', '_parent'),
        )
    else:
        parent_lvl = df[[val_col+'_new', val_col+'_old', vol_col+'_new', vol_col+'_old']].sum()
        parent_lvl[rate_col+'_new'] = parent_lvl[val_col+'_new'] / parent_lvl[vol_col+'_new']
        parent_lvl[rate_col+'_old'] = parent_lvl[val_col+'_old'] / parent_lvl[vol_col+'_old']
        
        result = df.copy()
        new_cols = []
        for col in result.columns:
            if col in idx_cols:
                new_cols.append(col)
            else:
                new_cols.append(col + '_child')
        result.columns = new_cols
        for col in [val_col+'_new', val_col+'_old', vol_col+'_new', vol_col+'_old', rate_col+'_new', rate_col+'_old']:
            result[col + '_parent'] = parent_lvl[col]
    
    result['mix_impact'] = (
        ((result[vol_col+'_new_child'] / result[vol_col+'_new_parent']) - (result[vol_col+'_old_child'] / result[vol_col+'_old_parent']))
        * (result[rate_col+'_new_child'] - result[rate_col+'_new_parent'])
        * result[vol_col+'_old_parent']
    )
    return result['mix_impact'].sum() / result[vol_col+'_old_child'].sum()


'''
- Rate mode:
    - Last period weighted average rate
    - Rate
    - Mix, each level, in order
    - This period weighted average rate
- Value mode:
    - Last period total value
    - Rate
    - Mix, each level, in order
    - Vol
    - This period total value
'''
def calc_rate_mix(df_old, df_new, idx_cols, rate_col, vol_col, mode='rate', round_digits=2):
    # mode: 'rate', 'value'
    # mode == 'rate': calculate total rate impact by rate, mix
    # mode == 'value': calculate total value impact by rate, mix, volume; note that value = volume * rate
    
    # mix(N) = rate(N-1) - rate(N)
    # rate(0) = overall weighted mean rate difference
    
    if not mode in ['rate', 'value']:
        raise ValueError("mode must be 'rate' or 'value'.")
    
    rates = []
    for i in range(len(idx_cols)+1):
        rates.append(calc_rate(df_old, df_new, idx_cols[:i], rate_col=rate_col, vol_col=vol_col))
    
    result = []
    if mode == 'rate':
        last_period_rate = (df_old[vol_col] * df_old[rate_col]).sum() / df_old[vol_col].sum()
        if pd.isna(last_period_rate) or np.isinf(last_period_rate):
            last_period_rate = 0
        result.append(['Last Period', last_period_rate])

        result.append([rate_col, rates[-1]])
        for i in range(len(idx_cols)):
            result.append([idx_cols[i], rates[i] - rates[i+1]])

        this_period_rate = (df_new[vol_col] * df_new[rate_col]).sum() / df_new[vol_col].sum()
        if pd.isna(this_period_rate) or np.isinf(this_period_rate):
            this_period_rate = 0
        result.append(['This Period', this_period_rate])
    elif mode == 'value':
        df_new_val = (df_new[rate_col] * df_new[vol_col]).sum()
        df_old_val = (df_old[rate_col] * df_old[vol_col]).sum()
        df_old_vol = df_old[vol_col].sum()
        rate = rates[-1] * df_old_vol
        vol_impact = df_new_val - df_old_val - rate
        
        result.append(['Last Period', df_old_val])
        result.append([rate_col, rate])
        for i in range(len(idx_cols)):
            this_impact = (rates[i] - rates[i+1]) * df_old_vol
            vol_impact -= this_impact  # subtract everything from the total value diff; what's left is the volume impact
            result.append([idx_cols[i], this_impact])
        
        result.append([vol_col, vol_impact])
        result.append(['This Period', df_new_val])
    
    result = [[x[0], round(float(x[1]), round_digits)] for x in result]
    return result


'''
returns:
{
    'xlabel': [x-axis labels],
    'pos': [positive or 0 values; values < 0 are filled with placeholder '-'],
    'neg': [negative values; values ≥ 0 are filled with placeholder '-'],
    'last': [last period, '-', '-', '-', ..., '-'],
    'this': ['-', '-', '-', ..., this period],
    'support': [y-value for the bottom of each waterfall bar; '-' for last period and this period],
}
x-axis index, positive, negative, last period, this period
'''
def calc_waterfall_series(rate_mix_result):
    # assumes last period value is the first element and this period value is the last element
    PLACEHOLDER = '-'
    xlabel = [x[0] for x in rate_mix_result]
    pos = [x[1] if x[1] >= 0 else PLACEHOLDER for x in rate_mix_result]
    neg = [-x[1] if x[1] < 0 else PLACEHOLDER for x in rate_mix_result]
    last = [rate_mix_result[0][1]] + [PLACEHOLDER] * (len(rate_mix_result) - 1)   
    this = [PLACEHOLDER] * (len(rate_mix_result) - 1) + [rate_mix_result[-1][1]]  
    
    # calc the bottom y-value of each waterfall bar.
    # if value ≥ 0, bottom is cumsum before this value; else bottom is cumsum before this value + this value (negative)
    support = []
    cumsum = 0
    for elem in rate_mix_result:
        if elem[1] >= 0:
            support.append(cumsum)
        else:
            support.append(cumsum + elem[1])
        cumsum += elem[1]
    
    # pos, neg, support values should be PLACEHOLDER for last, this periods
    # xlabel should be 'Last Period', 'This Period' for last, this periods
    pos[0] = PLACEHOLDER
    pos[-1] = PLACEHOLDER
    neg[0] = PLACEHOLDER
    neg[-1] = PLACEHOLDER
    support[0] = PLACEHOLDER
    support[-1] = PLACEHOLDER
    xlabel[0] = 'Last Period'
    xlabel[-1] = 'This Period'
    
    return {
        'xlabel': xlabel,
        'pos': pos,
        'neg': neg,
        'last': last,
        'this': this,
        'support': support,
    }

