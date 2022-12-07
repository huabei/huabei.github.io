---
layout: home
title: 国内学术报告汇总主页
---
## 简介

这个页面用于提供中国国内目前的学术报告，以方便有需求的研究者获取。内容由程序在各研究单位发布学术报告的网站上自动收集，如果有需要添加的网站链接，欢迎使用邮件发送给我。

此网站正在测试阶段，数据可能并不完善，请谅解。

## 学术报告

更新时间：{{ site.time | date: '%R，%B %d, %Y' }}

### 今日更新
<table>
  <tbody>
    <tr>
        <td><p>单位</p></td>
		<td><p>题目</p></td>
		<td><p>报告人</p></td>
		<td><p>时间</p></td>
		<td><p>地点</p></td>
		<td><p>详细信息</p></td>
    </tr>
{% for member in site.data.seminars-latest-update-d %}
    {% for seminars in member.page_info %}
    <tr>
        <td><a href="{{ member.page_url }}">{{ member.page_title }} </a></td>
    	<td><a href="{{ seminars.href }}">{{ seminars.title }}</a></td>
        <td><p>{{seminars.person}}</p></td>
        <td><p>{{ seminars.time }}</p></td>
		<td><p>{{ seminars.address }}</p></td>
		<td><p>{{ seminars.info }}</p></td>
    </tr>
    {% endfor %}
{% endfor %}
    </tbody>
</table>

### 七日内更新

{% for member in site.data.seminars-latest-update-w %}
<a href="{{ member.page_url }}">{{ member.page_title }} </a>
<table>
  <tbody>
    <tr>
		<td><p>题目</p></td>
		<td><p>报告人</p></td>
		<td><p>时间</p></td>
		<td><p>地点</p></td>
		<td><p>详细信息</p></td>
    </tr>
    {% for seminars in member.page_info %}
    <tr>
    	<td><a href="{{ seminars.href }}">{{ seminars.title }}</a></td>
        <td><p>{{seminars.person}}</p></td>
        <td><p>{{ seminars.time }}</p></td>
		<td><p>{{ seminars.address }}</p></td>
		<td><p>{{ seminars.info }}</p></td>
    </tr>
    {% endfor %}
        </tbody>
</table>
{% endfor %}

#### [最新全部]( {{ site.url }}/latest-whole)
