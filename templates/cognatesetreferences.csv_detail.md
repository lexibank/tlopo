<table id="{{ ctx['ID'] }}">
{% set glosses = glosses_by_formid(ctx['ID']) %}
{% set forms, fns = get_reconstruction(ctx['ID']) %}
{% for fid, group, lname, lid, is_proto, form, fn in forms %}
<tr>
{% if is_proto %}
<td><strong>{{ lname }}</strong></td><td> </td>
<td style="white-space: nowrap;">
<i>{{ form }}</i>
</td>
<td>
{% for g, cmt, pos, qual, srcs in glosses[fid] %}{% if qual %}({{ qual }}) {% endif %}{% if pos %}[{{ pos }}] {% endif %}'{{ g|markdown }}'{% if cmt %} ({{ cmt|markdown }}){% endif %}{% if srcs %}
 ({% for srcid, pages in srcs %}<a href="{{ href_source(srcid) }}">{{ srcid }}</a>{% if pages %}: {{ pages|markdown }}{% endif %}{% if loop.last == False %}; {% endif %}{% endfor %})
{% endif %}{% if loop.last == False %}; {% endif %}{% endfor %}
{% if fid in fns %}[^{{ fns[fid] }}]{% endif %}
</td>
{% else: %}
<td>{{ group }}</td><td><a href="{{ href_language(lid) }}">{{ lname }}</a></td><td><i>{{ form }}</i></td>
<td>
{% for g, cmt, pos, qual, srcs in glosses[fid] %}{% if qual %}({{ qual }}) {% endif %}{% if pos %}[{{ pos }}] {% endif %}{% if g %}'{{ g|markdown }}'{% endif %}{% if cmt %} ({{ cmt|markdown }}){% endif %}{% if srcs %}
 ({% for srcid, pages in srcs %}<a href="{{ href_source(srcid) }}">{{ srcid }}{% if pages %}: {{ pages }}{% endif %}</a>{% if loop.last == False %}; {% endif %}{% endfor %})
{% endif %}{% if loop.last == False %}; {% endif %}{% endfor %}
{% if fid in fns %}[^{{ fns[fid] }}]{% endif %}
</td>
{% endif %}
</tr>
{% endfor %}
</table>

{% for key, forms in get_cfs(ctx['ID']).items() %}
cf. also: {{ key[1] or '' }}
<table>
{% for group, lid, lname, form, glosses, fn in forms %}
<tr>
<td>{{ group }}</td>
<td><a href="{{ href_language(lid) }}">{{ lname }}</a></td>
<td><i>{{ form }}</i></td>
<td>
{% for g, cmt, pos, srcs in glosses %}{% if pos %}[{{ pos }}] {% endif %}{% if g %}'{{ g|markdown }}'{% endif %}{% if cmt %} ({{ cmt|markdown }}){% endif %}{% if srcs %}
({% for srcid, pages in srcs %}<a href="{{ href_source(srcid) }}">{{ srcid }}{% if pages %}: {{ pages }}{% endif %}</a>{% if loop.last == False %}; {% endif %}{% endfor %})
{% endif %}{% if loop.last == False %}; {% endif %}{% endfor %}
{% if fn %}[^{{ fn }}]{% endif %}
</td>
</tr>
{% endfor %}
</table>
{% endfor %}
