import pandas as pd
from bs4 import BeautifulSoup
import requests
from selenium.webdriver.common.by import By
from collections import defaultdict


def find_max_div(ele):
    """give a element, find the max sub div element, if not found, return the element itself with size 1"""
    divs = ele.find_elements(By.TAG_NAME, 'div')
    if len(divs) == 0:
        print("div no child div")
        return ele, 1
    all_div_size = [i.size['height'] * i.size['width'] for i in divs]
    highest_div_index = all_div_size.index(max(all_div_size))
    return divs[highest_div_index], max(all_div_size)


def get_max_child_ele(ele):
    child = ele.find_elements(By.XPATH, './*')
    if len(child) == 0:
        return ele
    all_child_size = [i.size['height'] * i.size['width'] for i in child]
    highest_child_index = all_child_size.index(max(all_child_size))
    return child[highest_child_index], all_child_size[highest_child_index]


def compare_elements_size(ele1, ele2):
    if ele1.size['width'] * ele1.size['height'] > ele2.size['width'] * ele2.size['height']:
        return ele1
    else:
        return ele2


def get_min_max_region(ele):
    max_div, max_div_size = find_max_div(ele)
    parent = max_div_size
    child = parent
    while True:
        parent = child
        print('div class:', max_div.get_attribute('class'), max_div_size)
        max_div_tmp, child = get_max_child_ele(max_div)
        if max_div_tmp.tag_name == 'table':
            return max_div
        # 如果最大子区域小于父区域的1/2.则返回父区域
        if parent/(child+1) > 2:
            # print(parent, child)
            return max_div
        max_div = max_div_tmp


def get_uli(ele):
    # ul_elements = ele.find_element(By.TAG_NAME, 'ul')
    # li_elements = ul_elements.find_elements(By.TAG_NAME, 'li')
    li_elements = ele.find_elements(By.XPATH, './li')
    return li_elements


def get_a(ele):
    a = ele.find_elements(By.TAG_NAME, 'a')
    # assert len(a) > 0, 'no a tag'
    if len(a) == 0:
        return False
    if len(a) == 1:
        return a[0]
    else:
        if a[0].get_attribute('href') == a[1].get_attribute('href'):
            return a[0]
        else:
            return compare_elements_size(a[0], a[1])


def get_dli(ele):
    li_elements = ele.find_elements(By.TAG_NAME, 'dd')
    return li_elements


def get_divli(ele):
    li_elements = ele.find_elements(By.XPATH, 'div')
    return li_elements


def get_seminars_list(ele):
    mode = ['ul', 'dl', 'div']
    mode_dict = {'ul': get_uli, 'dl': get_dli, 'div': get_divli}
    mode_list = list()
    for m in mode:
        mode_list.append(mode_dict[m](ele))
    mode_cont = [len(i) for i in mode_list]
    return mode_list[mode_cont.index(max(mode_cont))]


def get_seminars_table_info(ele):
    return pd.read_html(ele.get_attribute('outerHTML'))


def get_seminars_url_info(ele):
    # if ele.find_elements(By.TAG_NAME, 'main'):
    #     ele = ele.find_element(By.TAG_NAME, 'main')
    min_max_div = get_min_max_region(ele)
    if min_max_div.find_elements(By.TAG_NAME, 'table'):
        return get_seminars_table_info(min_max_div)
    seminars_list = get_seminars_list(min_max_div)
    result = defaultdict(list)
    for li in seminars_list:
        a = get_a(li)
        if not a:
            href = li.parent.current_url
            try:
                title = li.find_element(By.CLASS_NAME, 'title').text
            except:
                print('no title')
                if li.find_elements(By.TAG_NAME, 'ul'):
                    continue
                title = li.text
        else:
            href = a.get_attribute('href')
            title = a.get_attribute('title')
            title = a.text if title == '' else title
        # href = a.get_attribute('href')

        # 判断是否是最底层的页码
        if len(title) == 1:
            continue
        result['href'].append(href)
        result['title'].append(title)
        result['info'].append(li.text)

    return result

