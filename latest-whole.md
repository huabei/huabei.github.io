---
layout: home
---
## 简介

这里是最新收集的所有的学术报告，并没有经过日期筛选，所以包含很多已过期的结果，主页面存在较新的结果。

## 学术报告

更新时间：{{ site.time | date: '%B %d, %Y' }}

### 最新全部

{% for member in site.data.seminars-latest %}
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