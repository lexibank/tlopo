{% set items, with_morpheme_gloss = get_cfitems(ctx['ID']) %}
<table id="{{ ctx['ID'] }}">
{% for group, lname, form, mgloss, fn, glosses in items: %}
<tr>
<td>{{ group }}</td>
<td>{{ lname }}</td>
<td><i>{{ form }}</i></td>
{% if with_morpheme_gloss %}
<td>[{{ mgloss }}]</td>
{% endif %}
<td>
{% for g, cmt, pos, srcs in glosses %}{% if pos %}({{ pos }}) {% endif %}{% if g %}'{{ g|markdown }}'{% endif %}{% if cmt %} ({{ cmt|markdown }}){% endif %}{% if srcs %}
({% for srcid, pages in srcs %}<a href="{{ href_source(srcid) }}">{{ srcid }}{% if pages %}: {{ pages }}{% endif %}</a>{% if loop.last == False %}; {% endif %}{% endfor %})
{% endif %}{% if loop.last == False %}; {% endif %}{% endfor %}
{% if fn %}[^{{ fn }}]{% endif %}
</td>
</tr>
{% endfor %}
</table>