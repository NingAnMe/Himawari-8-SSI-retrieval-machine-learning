#!/usr/bin/env python 
# -*- coding: utf-8 -*-
# @Time    : 2020-07-16 18:40
# @Author  : NingAnMe <ninganme@qq.com>

from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import joblib
import os


model = joblib.load('ssi.model')


def get_hour(x):
    date_time = datetime.strptime(str(x)[:14], '%Y%m%d%H%M%S') - relativedelta(days=1)
    return date_time.hour


def get_date(x):
    date_time = datetime.strptime(str(x)[:14], '%Y%m%d%H%M%S') - relativedelta(days=1)
    return date_time.strftime('%Y-%m-%d')


def ssi2mj_orbit(ssi):
    mj = ssi * 3600 / 1e6
    return mj


def h8file2x(in_file):
    data = pd.read_csv(in_file)

    data = data.drop('station_alt', axis=1)
    data[data < 0] = 0
    data = data.dropna(axis=0)
    date_time = data["datetime"]
    x = data.iloc[:, 7:23]
    x['hour'] = date_time.map(get_hour)
    return x, date_time


def predict_ssi(x):
    y = model.predict(x)
    y[y < 0] = 0
    y[y > 1500] = 1500
    return y


def h8file2mj(in_file, out_file):
    print(f"<<< :{in_file}")

    x, date_time = h8file2x(in_file)
    y = predict_ssi(x)

    result = x.copy()
    result['ssi'] = y
    result['datetime'] = date_time
    result['date'] = result['datetime'].map(get_date)
    result['mj'] = result['ssi'].map(ssi2mj_orbit)

    data1_groupby = result.groupby('date')
    data_out = []
    for i in data1_groupby:
        data_out.append([i[0], i[1]['mj'].sum()])

    data_out = pd.DataFrame(data_out)
    data_out.columns = ['date', 'MJ/m2']

    data_out.to_csv(out_file, index=False)
    print(f">>> : {out_file}")


def main(in_dir):

    in_files = list()
    for root, _, filenames in os.walk(in_dir):
        for filename in filenames:
            in_file = os.path.join(root, filename)
            in_files.append(in_file)
            print(in_file)

    if len(in_files) <= 0:
        print('没有有效数据')
        return

    out_dir = in_dir + '_out'
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    for in_file in in_files:
        filename = os.path.basename(in_file)
        out_file = os.path.join(out_dir, filename)
        h8file2mj(in_file, out_file)


def test_h8file2mj():
    in_file = os.path.join('example', 'h8data.csv')
    out_file = os.path.join('example', 'mj.csv')
    h8file2mj(in_file, out_file)


if __name__ == '__main__':
    test_h8file2mj()  # 测试用例

    in_dir_ = os.path.join('test', 'station5')
    main(in_dir_)
