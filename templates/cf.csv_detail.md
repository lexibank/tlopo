{% set items, with_morpheme_gloss = get_cfitems(ctx['ID']) %}
<table id="{{ ctx['ID'] }}">
{% for group, lid, lname, form, mgloss, fn, glosses in items: %}
<tr>
<td>{{ group }}</td>
<td><a href="{{ href_language(lid) }}">{{ lname }}</a></td>
<td style="white-space: nowrap"><i>{{ form }}</i></td>
{% if with_morpheme_gloss %}
<td>{% if mgloss %}[{{ mgloss }}]{% endif %}</td>
{% endif %}
<td>
{% for g, cmt, pos, srcs in glosses %}{% if pos %}[{{ pos }}] {% endif %}{% if g %}'{{ g|markdown }}'{% endif %}{% if cmt %} ({{ cmt|markdown }}){% endif %}{% if srcs %}
({% for srcid, pages, key in srcs %}<a href="{{ href_source(srcid) }}">{{ key }}{% if pages %}: {{ pages }}{% endif %}</a>{% if loop.last == False %}; {% endif %}{% endfor %})
{% endif %}{% if loop.last == False %}; {% endif %}{% endfor %}
{% if fn %}[^{{ fn }}]{% endif %}
</td>
</tr>
{% endfor %}
</table>