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
    idx_cols = request.json['idx_cols']
    rate_col = request.json['rate_col']
    vol_col = request.json['vol_col']
    mode = request.json.get('mode', 'rate')  # default mode is calculate rate

    rate_mix_result = calc_rate_mix(df_old, df_new, idx_cols, rate_col, vol_col, mode=mode)
    waterfall_result = calc_waterfall_series(rate_mix_result)

    result = {
        'raw': rate_mix_result,
        'waterfall': waterfall_result,
    }
    print(result)
    
    return json.dumps(result), 200


if __name__ == '__main__':
    app.run(debug=True)

