from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from collections import defaultdict
from utils import get_seminars_url_info
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from utils import get_driver, Logger, get_url
import time
import pandas as pd
import os
from copy import deepcopy
import pickle


def generate_absurl(url, base_url):
    """generate absolute url
    :param url: str, url
    :param base_url: str, base url
    :return: str, absolute url
    """
    base_url_dir = '/'.join(base_url.strip().split('/')[:-1])
    if url.startswith('http'):
        return url
    elif url.startswith('/'):
        return base_url
    else:
        return base_url_dir + '/' + url


def write_data(data: dict, output_file_path: str, head_replace: dict = None):
    """write data to csv file
    :param data: dict, key is url, value is dict
    :param output_file_path: str, output file path
    :param head_replace: dict, replace the head of the csv file, key is the old head, value is the new head.
    """
    data_head = ['page_title', 'page_url', 'title', 'href', 'person', 'time', 'address', 'info']
    data_df = pd.DataFrame(columns=data_head)
    for key, value in data.items():
        if type(value['page_info']) is pd.DataFrame:
            df = value['page_info']
            if head_replace:
                df.rename(columns=head_replace, inplace=True)
                df['href'] = df['title'].apply(lambda x: generate_absurl(x[1], value['page_url']))
                df['title'] = df['title'].apply(lambda x: x[0])
                for col, v in df.items():
                    df[col] = v.apply(lambda x: x[0] if type(x) is tuple else x)
        else:
            df = pd.DataFrame(value['page_info'])
        df['page_title'] = value['page_title']
        df['page_url'] = value['page_url']
        data_df = pd.concat([data_df, df], axis=0)
    data_df = data_df[data_head]
    data_df.to_csv(output_file_path, mode='a', header=True, index=False, encoding='utf_8')


def generate_yaml_seminars(page_info):
    """generate yaml seminars
    :param page_info: dict, key is url, value is dict
    :return: list, yaml seminars
    """
    yaml_seminars = list()
    for i, value in enumerate(page_info['href']):
        yaml_seminars.append(dict(title=page_info['title'][i],
                                  href=value,
                                  person=(page_info['person'][i] if i < len(page_info['person']) else ''),
                                  time=page_info['time'][i] if i < len(page_info['time']) else '',
                                  address=page_info['address'][i] if i < len(page_info['address']) else '',
                                  info=page_info['info'][i] if i < len(page_info['info']) else ''))
        # 取前十条记录
        if i == 10:
            break
    return yaml_seminars


def prepare_data(data: dict, head_replace: dict = None):
    for key, value in data.items():
        if type(value['page_info']) is pd.DataFrame:
            df = value['page_info']
            if head_replace:
                # 更换表头
                df.rename(columns=head_replace, inplace=True)
                # 拆分链接和标题
                df['href'] = df['title'].apply(lambda x: generate_absurl(x[1], value['page_url']))
                df['title'] = df['title'].apply(lambda x: x[0])
                for col, v in df.items():
                    df[col] = v.apply(lambda x: x[0] if type(x) is tuple else x)
            # 转换为字典
            value['page_info'] = df.to_dict()
        # 将dict转换为defaultdict
        value['page_info'] = defaultdict(list, value['page_info'])
    return data


def write_yaml(data: dict, output_file_path: str):
    import yaml
    total_list = list()
    # 将数据转换为yaml列表
    for key, value in data.items():
        value['page_info'] = generate_yaml_seminars(deepcopy(value['page_info']))
        total_list.append(value)
    # 写入文件
    with open(output_file_path, 'w', encoding='utf-8') as f:
        yaml.dump(total_list, f, allow_unicode=True)


def compare_yesterday_and_today(yesterday_data: dict, today_data: dict):
    """compare yesterday and today
    :param yesterday_data: dict, yesterday data
    :param today_data: dict, today data
    :return: dict, new data
    """
    update_data = dict()
    for key, value in today_data.items():
        if key not in yesterday_data:
            update_data[key] = value
        elif value['page_info']['href'] != yesterday_data[key]['page_info']['href']:
            update_data[key] = value
            # 将page_info 置空
            update_data[key]['page_info'] = defaultdict(list)
            for i, href in enumerate(value['page_info']['href']):
                if href not in yesterday_data[key]['page_info']['href']:
                    update_data[key]['page_info']['title'].append(value["page_info"]["title"][i])
                    update_data[key]['page_info']['href'].append(href)
                    update_data[key]['page_info']['person'].append(value["page_info"]["person"][i])
                    update_data[key]['page_info']['time'].append(value["page_info"]["time"][i])
                    update_data[key]['page_info']['address'].append(value["page_info"]["address"][i])
                    update_data[key]['page_info']['info'].append(value["page_info"]["info"][i])
    return update_data


def main(url_file_path: str, output_file_path: str, head_replace: dict = None):
    url_iter = open(url_file_path, 'r')
    total_result = dict()

    logger = Logger('./log')
    driver = get_driver(headless=False)  # 无头会出错
    for url in url_iter:
        result_tmp = dict()
        url = url.strip()
        driver.status = True
        driver = get_url(driver, url, logger)
        if not driver.status:
            continue
        print(f'start analyze {url}')
        result_tmp['page_title'] = driver.title
        result_tmp['page_url'] = url
        try:
            result_tmp['page_info'] = get_seminars_url_info(driver, logger)
        except:
            # print(url)
            logger(f'******************{url} wrong! **********************')
            continue
        total_result[url] = result_tmp
    driver.quit()
    logger.close()
    # 准备数据，更换表头等。
    total_result = prepare_data(total_result, head_replace)
    latest_data_path = output_file_path.replace('.yaml', '.pkl')
    # 已存的latest数据作为昨天的数据，和今天的数据比较，得到update数据
    if os.path.exists(latest_data_path):
        yesterday_data = pickle.load(open(latest_data_path, 'rb'))
        os.rename(latest_data_path, f'../_data/seminars-{d}.pkl')
        update_data = compare_yesterday_and_today(yesterday_data, total_result)
        # 将update数据写入文件
        write_yaml(update_data, output_file_path.replace('.yaml', '-update.yaml'))
    with open(latest_data_path, 'wb') as f:
        pickle.dump(total_result, f)
    # write_data(total_result, output_file_path, head_replace=head_replace)
    write_yaml(total_result, output_file_path)


if __name__ == '__main__':
    # import sys
    # sys.path.extend([r"E:\Huabei\huabei.github.io\code"])
    d = time.strftime('%Y-%m-%d', time.localtime())
    output_file_path = '../_data/seminars-latest.yaml'
    if os.path.exists(output_file_path):
        os.rename(output_file_path, f'../_data/seminars-{d}.yaml')
    head_replace = {'报告题目': 'title',
                    '报告日期': 'time',
                    '时间': 'time',
                    '讲座题目': 'title',
                    '主讲人': 'person',
                    '报告人': 'person',
                    '地址': 'address',
                    '地点': 'address'}
    # main(r"E:\Huabei\huabei.github.io\code\web-site.txt", output_file_path, head_replace=head_replace)
    # with open('../_data/seminars-latest.pkl', 'rb') as f:
    #     import pickle
    #     today_result = pickle.load(f)
    # with open('../_data/seminars-2022-11-21.pkl', 'rb') as f:
    #     import pickle
    #     yesterday_result = pickle.load(f)
    # update_data = compare_yesterday_and_today(yesterday_result, today_result)
    # write_yaml(update_data, output_file_path.replace('.yaml', '-update.yaml'))
    #
    # # write_data(total_result, output_file_path, head_replace=head_replace)
    # write_yaml(total_result, '../_data/seminars-latest.yaml', head_replace=head_replace)
