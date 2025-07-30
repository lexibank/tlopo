{% set num, cmt, labels, ex = get_eg(ctx['ID']) %}
{% if num %}<ol start="{{ num }}">{% else %}<ul style="list-style: none;">{% endif %}
<li>{% if cmt %} {{ cmt }}{% endif %}

{% if labels %}<ol type="a">{% else %} <ul style="list-style: none">{% endif %}
{% for lname, lgroup, text, gloss, mgloss, translation, cmt, src, reflabel in ex: %}
<li>
{{ lname }}{% if lgroup %} ({{ lgroup }}){% endif %}{% if src %}: ([{{ reflabel }}]({{ href_source(src) }})){% endif %}
<table style="padding-left: 2em;" class="igt{% if label %} labeled{% endif %}">
<caption>‘{{ translation }}’{% if cmt %} ({{ cmt }}){% endif %}</caption>
<tr>
{% for i in text: %}
<td><i>{{ i }}</i></td>
{% endfor %}
<td style="width: 100%"> </td>
</tr>
<tr>
{% for i in gloss: %}
<td>{{ i }}</td>
{% endfor %}
<td style="width: 100%"> </td>
</tr>
{% if mgloss %}
<tr>
{% for i in mgloss: %}
<td>{{ i }}</td>
{% endfor %}
<td style="width: 100%"> </td>
</tr>
{% endif %}
</table>
</li>
{% endfor %}
{% if labels %}</ol>{% else %}</ul>{% endif %}
</li>
{% if num %}</ol>{% else %}</ul>{% endif %}
