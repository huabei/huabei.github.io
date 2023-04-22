import pandas as pd
from selenium.webdriver.common.by import By
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.common.by import By
from collections import defaultdict
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
import time
import os
import logging


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
    """找到最大的子元素"""
    # 找到所有的子元素
    childs = ele.find_elements(By.XPATH, './*')
    # 如果没有子元素，则报错
    assert len(childs) > 0, 'no child'
    # 计算所有子元素的大小
    all_child_size = [i.size['height'] * i.size['width'] for i in childs]
    # 如果所有子元素的大小都是0，则返回第一个元素
    if all_child_size == [0] * len(all_child_size):
        logging.warning('all child size is 0, find next level')
        # raise Exception('all child size is 0')
        # 寻找子元素
        child_sub = []
        for child in childs:
            child_sub += child.find_elements(By.XPATH, './*')
        all_child_size = [i.size['height'] * i.size['width'] for i in child_sub]
        childs = child_sub
        # all_child_size = [len(ele.find_elements(By.XPATH, './*')) for i in childs]
    highest_child_index = all_child_size.index(max(all_child_size))
    return childs[highest_child_index], all_child_size[highest_child_index]


def compare_elements_subcontent(ele1, ele2):
    """compare two elements, return the element with more sub content"""
    if len(ele1.find_elements(By.XPATH, './*')) > len(ele2.find_elements(By.XPATH, './*')):
        return ele1
    else:
        return ele2


def compare_elements_size(ele1, ele2):
    """compare two elements, return the element with more sub content"""
    if ele1.size['height'] * ele1.size['width'] > ele2.size['height'] * ele2.size['width']:
        return ele1
    else:
        return ele2


def get_min_max_region(ele):
    """使用迭代的方式，获取网页的最大区域，其中包含多个小区域，用以提取主要内容"""
    
    # 首先找到最大的div区域
    max_div, max_div_size = find_max_div(ele)
    logging.info('max div : {}'.format(max_div.get_attribute('class')))
    parent = max_div_size
    
    # 进行迭代，找到最大的子区域，并判断是否小于父区域的1/2，如果是，则返回父区域
    while True:
        # 找到最大的子区域
        max_div_tmp, child = get_max_child_ele(max_div)
        
        logging.info('div class: {}, {}\n\t, {}, {}'.format(max_div.get_attribute('class'), parent,
                                                          max_div_tmp.get_attribute('class'), child))
        # 如果最大子区域是table，则返回父区域
        if max_div_tmp.tag_name == 'table':
            return max_div
        
        # 如果最大子区域小于10000
        if child < 10000:
            pass
        
        # 如果最大子区域小于父区域的1/2.则返回父区域
        elif parent / child > 2:
            # print(parent, child)
            return max_div
        # 否则，继续迭代
        max_div = max_div_tmp
        parent = child


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
    li_elements = ele.find_elements(By.TAG_NAME, './dd')
    return li_elements


def get_divli(ele):
    li_elements = ele.find_elements(By.XPATH, './div')
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
    df = pd.read_html(ele.get_attribute('innerHTML'), extract_links='body')[0]
    return df


def get_seminars_url_info(ele):
    """解析网页内容"""
    # if ele.find_elements(By.TAG_NAME, 'main'):
    #     ele = ele.find_element(By.TAG_NAME, 'main')
    
    # 获取网页的最大区域
    min_max_div = get_min_max_region(ele)
    if min_max_div.find_elements(By.TAG_NAME, 'table'):
        return get_seminars_table_info(min_max_div)
    seminars_list = get_seminars_list(min_max_div)
    result = defaultdict(list)
    for li in seminars_list:
        a = get_a(li)
        # 如果没有a标签，则表示其是用js跳转的
        if not a:
            href = li.parent.current_url
            try:
                title = li.find_element(By.CSS_SELECTOR, '[title]').text
            except:
                logging.info('no title')
                if li.find_elements(By.TAG_NAME, 'ul'):
                    continue
                title = li.text
        else:
            href = a.get_attribute('href')
            title = a.get_attribute('title')
            try:
                title = li.find_element(By.CSS_SELECTOR, '[title]').get_attribute('title')
            except:
                pass
            if title == '':
                title = a.text
        # 判断是否是最底层的页码
        if len(title) == 1:
            continue
        # result['page_name'].append(ele.title)
        result['href'].append(href)
        result['title'].append(title.replace('>', ')').replace('<', '('))
        result['info'].append(li.text.replace('>', ')').replace('<', '('))

    return result


def get_driver(headless=True, **kwargs) -> webdriver:
    """get url driver"""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument("--window-size=1440,900")
    driver = webdriver.Chrome(options=options, **kwargs)
    # 载入页面等待10秒
    driver.set_page_load_timeout(10)
    driver.maximize_window()
    driver.implicitly_wait(1)
    return driver


def get_url(driver, url, headless=True, **kwargs):
    """get url并返回打开网页的driver"""
    logging.info('get url: {}'.format(url))
    try:
        driver.get(url)
    except TimeoutException:
        logging.warning(f'get {url} time out')
    # time.sleep(3)
    # 判断是否无法打开网址
    if driver.title in ['', url.split('//')[1].split('/')[0]]:
        logging.warning(f'\n********* {url} could not get! **************\n')
        driver.status = False
        return driver
    try:
        WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.TAG_NAME, "div"))
    except TimeoutException:
        logging.warning(f'{url} wait time out')
    return driver


class Logger:
    def __init__(self, log_dir):
        d = time.strftime('%Y-%m-%d', time.localtime())
        self.log_path = os.path.join(log_dir, f'log-{d}.txt')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self.writer = open(self.log_path, 'a')

    def log(self, msg):
        assert isinstance(msg, str)
        print(msg)
        self.writer.write(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '\t' + msg + '\n')
        self.writer.flush()

    def close(self):
        self.writer.close()

    def __del__(self):
        self.close()

    def __call__(self, msg):
        self.log(msg)
