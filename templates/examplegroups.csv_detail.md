{% set num, cmt, lname, lgroup, src, reflabel, ex = get_eg(ctx['ID']) %}
{% if num %}({{ num }}) {% endif %}{{ lname }}{% if lgroup %} ({{ lgroup }}){% endif %}{% if cmt %}: {{ cmt }}{% endif %}{% if src %}: ([{{ reflabel }}]({{ href_source(src) }})){% endif %}
{% for label, text, gloss, translation in ex: %}
<table class="igt{% if label %} labeled{% endif %}">
<caption>‘{{ translation }}’</caption>
<tr>
{% if label %}<td>{{ label }}</td>{% endif %}
{% for i in text: %}
<td><i>{{ i }}</i></td>
{% endfor %}
<td style="width: 100%"> </td>
</tr>
<tr>
{% if label %}<td>&nbsp;</td>{% endif %}
{% for i in gloss: %}
<td>{{ i }}</td>
{% endfor %}
<td style="width: 100%"> </td>
</tr>
</table>
{% endfor %}