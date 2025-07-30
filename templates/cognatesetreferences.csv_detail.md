<table id="{{ ctx['ID'] }}">
{% set glosses = glosses_by_formid(ctx['ID']) %}
{% set forms, fns, sgs = get_reconstruction(ctx['ID']) %}
{% set ns = namespace(subgroup=None) %}
{% for fid, group, lname, lid, is_proto, form, mgloss, fn, _ in forms %}
{% if fid in sgs and sgs[fid] != ns.subgroup %}
<tr><td colspan="4"><i>{{ sgs[fid] }}</i></td></tr>
{% set ns.subgroup = sgs[fid] %}
{% endif %}
<tr>
{% if is_proto %}
<td><strong>{{ lname }}</strong></td><td> </td>
<td style="white-space: nowrap;">
<i>{{ form }}</i>
</td>
<td>{% if mgloss %}[{{ mgloss }}] {% endif %}
{% for g, cmt, pos, qual, srcs in glosses[fid] %}{% if qual %}({{ qual }}) {% endif %}{% if pos %}[{{ pos }}] {% endif %}'{{ g|markdown }}'{% if cmt %} ({{ cmt|markdown }}){% endif %}{% if srcs %}
 ({% for srcid, pages, key in srcs %}<a href="{{ href_source(srcid) }}">{{ key }}</a>{% if pages %}: {{ pages|markdown }}{% endif %}{% if loop.last == False %}; {% endif %}{% endfor %})
{% endif %}{% if loop.last == False %}; {% endif %}{% endfor %}
{% if fid in fns %}[^{{ fns[fid] }}]{% endif %}
</td>
{% else: %}
<td>{{ group }}</td><td><a href="{{ href_language(lid) }}">{{ lname }}</a></td><td style="white-space: nowrap;"><i>{{ form }}</i></td>
<td>{% if mgloss %}[{{ mgloss }}] {% endif %}
{% for g, cmt, pos, qual, srcs in glosses[fid] %}{% if qual %}({{ qual }}) {% endif %}{% if pos %}[{{ pos }}] {% endif %}{% if g %}'{{ g|markdown }}'{% endif %}{% if cmt %} ({{ cmt|markdown }}){% endif %}{% if srcs %}
 ({% for srcid, pages, key in srcs %}<a href="{{ href_source(srcid) }}">{{ key }}{% if pages %}: {{ pages }}{% endif %}</a>{% if loop.last == False %}; {% endif %}{% endfor %})
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
<td>{% if group %}{{ group }}{% endif %}</td>
<td><a href="{{ href_language(lid) }}">{{ lname }}</a></td>
<td style="white-space: nowrap;"><i>{% if not group %}&ast;{% endif %}{{ form }}</i></td>
<td>
{% for g, cmt, pos, srcs in glosses %}{% if pos %}[{{ pos }}] {% endif %}{% if g %}'{{ g|markdown }}'{% endif %}{% if cmt %} ({{ cmt|markdown }}){% endif %}{% if srcs %}
({% for srcid, pages, key in srcs %}<a href="{{ href_source(srcid) }}">{{ key }}{% if pages %}: {{ pages }}{% endif %}</a>{% if loop.last == False %}; {% endif %}{% endfor %})
{% endif %}{% if loop.last == False %}; {% endif %}{% endfor %}
{% if fn %}[^{{ fn }}]{% endif %}
</td>
</tr>
{% endfor %}
</table>
{% endfor %}
