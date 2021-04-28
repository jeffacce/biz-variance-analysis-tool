from flask import Flask, request, abort, render_template
from flask_cachebuster import CacheBuster
import pandas as pd
import numpy as np
import time
import json
from calc import calc_rate_mix, calc_waterfall_series


app = Flask(__name__)
config = {
    'extensions': ['.js', '.html', '.css'],
    'hash_size': 5,
}
cache_buster = CacheBuster(config=config)
cache_buster.init_app(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/variance-analysis/api/v1/raw', methods=['POST'])
def handle_raw():
    valid = (
        request.json
        and True  # placeholder
    )
    if not valid:
        abort(400)
    
    df_old = pd.DataFrame(request.json['df_old'])
    df_new = pd.DataFrame(request.json['df_new'])
    warnings = ''
    idx_cols = request.json['idx_cols']
    rate_col = request.json['rate_col']
    vol_col = request.json['vol_col']
    mode = request.json.get('mode', 'rate')  # default mode is calculate rate
    round_digits = request.json.get('round_digits', 2)

    df_old_rate_col_NAs = df_old[rate_col].isna().sum()
    df_new_rate_col_NAs = df_new[rate_col].isna().sum()
    
    if (df_old_rate_col_NAs > 0) or (df_new_rate_col_NAs > 0):
        warnings = 'Warning: '
        if df_old_rate_col_NAs > 0:
            warnings += 'Last period rate column contains %s NAs. ' % df_old_rate_col_NAs
        if df_new_rate_col_NAs > 0:
            warnings += 'This period rate column contains %s NAs. ' % df_new_rate_col_NAs
        warnings += 'Rows with NA rates have been dropped. ' 
    
    df_old = df_old[~df_old[rate_col].isna()]
    df_new = df_new[~df_new[rate_col].isna()]

    rate_mix_result = calc_rate_mix(df_old, df_new, idx_cols, rate_col, vol_col, mode=mode, round_digits=round_digits)
    waterfall_result = calc_waterfall_series(rate_mix_result)

    result = {
        'raw': rate_mix_result,
        'waterfall': waterfall_result,
        'warnings': warnings,
    }
    print(result)
    
    return json.dumps(result), 200


if __name__ == '__main__':
    app.run(debug=True)

