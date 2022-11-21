---
layout: home
---
## 简介

这个页面用于提供中国国内目前的学术报告，以方便有需求的研究者方便获取。内容由作者在网站上收集。

## 学术报告

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
