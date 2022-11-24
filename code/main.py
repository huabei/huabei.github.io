from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from collections import defaultdict
from utils import get_seminars_url_info
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from utils import get_driver, Logger, get_url
import time
import datetime
import pandas as pd
import os
from copy import deepcopy
import pickle
import yaml


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
        # print(base_url_dir + '/' + url)
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
    data_df.to_csv(output_file_path, mode='a', header=True, index=False, encoding='utf-8-sig')


def generate_yaml_seminars(page_info, filter_href: set = None):
    """generate yaml seminars
    :param page_info: dict, key is url, value is dict
    :param filter_href: set, filter href
    :return: list, yaml seminars
    """
    yaml_seminars = list()
    for i, value in enumerate(page_info['href']):
        if filter_href and value in filter_href:
            continue
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
                # print(df['href'])
                # raise Exception
                df['title'] = df['title'].apply(lambda x: x[0])
                for col, v in df.items():
                    df[col] = v.apply(lambda x: x[0] if type(x) is tuple else x)
            # 转换为字典
            value['page_info'] = df.to_dict(orient='list')
            # print(value['page_info'])
            # raise Exception
        # 将dict转换为defaultdict
        value['page_info'] = defaultdict(list, value['page_info'])
    return data


def write_yaml(data: dict, output_file_path: str, filter_href: set = None):
    import yaml
    total_list = list()
    # 将数据转换为yaml列表
    for key, value in data.items():
        value['page_info'] = generate_yaml_seminars(deepcopy(value['page_info']), filter_href)
        if value['page_info']:
            total_list.append(value)
    # 写入文件
    with open(output_file_path, 'w', encoding='utf-8-sig') as f:
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


def generate_href(result):
    """generate href
    :param result: dict, key is url, value is dict
    :return: list, href
    """
    href = list()
    for key, value in result.items():
        href.extend(value['page_info']['href'])
    return set(href)


def main(url_file_path: str, output_file_path: str, head_replace: dict = None):
    total_result = get_data_from_internet(url_file_path)
    # with open('../_data/seminars-test.pkl', 'rb') as f:
    #     import pickle
    #     total_result = pickle.load(f)
    # 准备数据，更换表头等。
    total_result = prepare_data(total_result, head_replace)
    # 生成href集合
    href_set_today = generate_href(total_result)
    # 写入今天的文件并计算今日更新
    latest_data_path = output_file_path.replace('.yaml', '.pkl')
    day_update_path = output_file_path.replace('.yaml', '-update-d.yaml')
    if os.path.exists(day_update_path):
        os.rename(day_update_path, f'../_data/seminars-update-{d}.yaml')
    # 已存的latest数据作为昨天的数据，和今天的数据比较，得到update数据
    if os.path.exists(latest_data_path):
        yesterday_total_href = pickle.load(open(latest_data_path, 'rb'))
        write_yaml(deepcopy(total_result), day_update_path, yesterday_total_href)
        # 并集覆写最新你href
        with open(latest_data_path, 'wb') as f:
            pickle.dump(href_set_today | yesterday_total_href, f)
    else:
        # 今天是第一次运行，直接写入
        with open(latest_data_path, 'wb') as f:
            pickle.dump(href_set_today, f)
    # 合并前七天的数据
    week_update_path = output_file_path.replace('.yaml', '-update-w.yaml')
    week_update_data_total = get_week_update(output_file_path)
    with open(week_update_path, 'w', encoding='utf-8-sig') as f:
        yaml.dump(week_update_data_total, f, allow_unicode=True)
    # write_data(total_result, output_file_path, head_replace=head_replace)
    write_yaml(total_result, output_file_path)


def get_week_update(output_file_path) -> list:
    week_update_data_total = defaultdict(dict)
    for i in range(1, 7):
        day = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
        if os.path.exists(f'../_data/seminars-update-{day}.yaml'):
            # print(day)
            with open(f'../_data/seminars-update-{day}.yaml', 'r', encoding='utf-8-sig') as f:
                data_u = yaml.load(f, Loader=yaml.FullLoader)
                for d in data_u:
                    week_update_data_total[d['page_url']]['page_title'] = d['page_title']
                    week_update_data_total[d['page_url']]['page_url'] = d['page_url']
                    for e in d['page_info']:
                        try:
                            week_update_data_total[d['page_url']]['page_info'].append(e)
                        except:
                            week_update_data_total[d['page_url']]['page_info'] = [e]
    return list(week_update_data_total.values())


def get_data_from_internet(url_file_path):
    url_iter = open(url_file_path, 'r')
    total_result = dict()
    logger = Logger('./log')
    driver = get_driver(headless=True)  # 无头会出错
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
    return total_result


if __name__ == '__main__':
    # import sys
    # sys.path.extend([r"E:\Huabei\huabei.github.io\code"])
    os.chdir(r"E:\Huabei\huabei.github.io\code")
    # 今天的时间d
    d = time.strftime('%Y-%m-%d', time.localtime())
    # 七天前的时间
    # w_l7 = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    output_file_path = '../_data/seminars-latest.yaml'
    # if os.path.exists(output_file_path):
    #     os.rename(output_file_path, f'../_data/seminars-{d}.yaml')

    head_replace = {'报告题目': 'title',
                    '报告日期': 'time',
                    '时间': 'time',
                    '讲座题目': 'title',
                    '主讲人': 'person',
                    '报告人': 'person',
                    '地址': 'address',
                    '地点': 'address'}

    main(r"E:\Huabei\huabei.github.io\code\web-site.txt", output_file_path, head_replace=head_replace)
    # main(r"E:\Huabei\huabei.github.io\code\test-site.txt", output_file_path, head_replace=None)
    # with open('../_data/seminars-test.pkl', 'rb') as f:
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
