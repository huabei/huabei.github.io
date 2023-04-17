"""测试模块"""

from utils import get_url, get_driver, get_seminars_url_info
from main import prepare_data
import logging
import argparse


def test_get_url(driver, url: str):
    """测试网址内容获取"""
    driver.status = True
    driver = get_url(driver, url.strip())
    return driver

def test_url_analysis(driver, url: str):
    """测试网址内容分析"""
    driver.status = True
    driver = get_url(driver, url.strip())
    if not driver.status:
        print('get url error: {} \n Test exit !'.format(url))
        return driver
    page_info = get_seminars_url_info(driver)
    content = zip(page_info['title'], page_info['href'], page_info['info'])
    for t in content:
        print('\t'.join(t))


def test_data_format(driver, url: str):
    """测试网址内容格式化"""
    page_info = test_url_analysis(driver, url)
    data = prepare_data(page_info)
    print(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', help='url to test', default=None, type=str)
    parser.add_argument('-f', '--file', help='file to test', default=None, type=str)
    parser.add_argument('-l', '--log', help='log file', default=None, type=str)
    parser.add_argument('--level', help='test level: 0: test get url; 1: test content analysis; 2: test data format', choices=[0, 1, 2], default=0, type=int)
    args = parser.parse_args()
    
    # 设置日志文件，如果没有设置则输出到控制台
    logging.basicConfig(filename=args.log, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 打开浏览器
    driver = get_driver(headless=False)
    
    # 收集测试网址
    test_url = list()
    if args.url is not None: # 添加单个网址
        test_url.append(args.url)
    if args.file is not None: # 添加文件中的网址
        with open(args.file, 'r') as f:
            for url in f:
                test_url.append(url)
    if not test_url: # 如果没有添加网址，则提示
        print('please input url or file(-h for help)')

    test_f_dict = {0: test_get_url, 1: test_url_analysis, 2: test_data_format}
    
    # 根据测试级别测试网址
    for url in test_url:
        test_f_dict[args.level](driver, url)

