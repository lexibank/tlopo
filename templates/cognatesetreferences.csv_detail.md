<table>
{% set glosses = glosses_by_formid(ctx['ID']) %}
{% for fid, group, lname, is_proto, form in get_reconstruction(ctx['ID']) %}
<tr>
{% if is_proto %}
<td><strong>{{ lname }}</strong></td><td> </td>
<td>
<i>&ast;{{ form }}</i>
</td>
<td>
{% for g, cmt, pos, srcs in glosses[fid] %}{% if pos %}({{ pos }}) {% endif %}'{{ g|markdown }}'{% if cmt %} ({{ cmt|markdown }}){% endif %}{% if srcs %}
 ({% for srcid, pages in srcs %}<a href="../references.md#source-{{ srcid }}">{{ srcid }}{% if pages %}: {{ pages }}{% endif %}</a>{% if loop.last == False %}; {% endif %}{% endfor %})
{% endif %}{% if loop.last == False %}; {% endif %}{% endfor %}
</td>
{% else: %}
<td>{{ group }}</td><td>{{ lname }}</td><td><i>{{ form }}</i></td>
<td>
{% for g, cmt, pos, srcs in glosses[fid] %}{% if pos %}({{ pos }}) {% endif %}{% if g %}'{{ g|markdown }}'{% endif %}{% if cmt %} ({{ cmt|markdown }}){% endif %}{% if srcs %}
 ({% for srcid, pages in srcs %}<a href="../references.md#source-{{ srcid }}">{{ srcid }}{% if pages %}: {{ pages }}{% endif %}</a>{% if loop.last == False %}; {% endif %}{% endfor %})
{% endif %}{% if loop.last == False %}; {% endif %}{% endfor %}
</td>
{% endif %}
</tr>
{% endfor %}
</table>

{% for key, forms in get_cfs(ctx['ID']).items() %}
cf. also: {{ key[1] or '' }}
<table>
{% for group, lname, form, glosses in forms %}
<tr>
<td>{{ group }}</td>
<td>{{ lname }}</td>
<td><i>{{ form }}</i></td>
<td>
{% for g, cmt, pos, srcs in glosses %}{% if pos %}({{ pos }}) {% endif %}{% if g %}'{{ g|markdown }}'{% endif %}{% if cmt %} ({{ cmt|markdown }}){% endif %}{% if srcs %}
({% for srcid, pages in srcs %}<a href="../references.md#source-{{ srcid }}">{{ srcid }}{% if pages %}: {{ pages }}{% endif %}</a>{% if loop.last == False %}; {% endif %}{% endfor %})
{% endif %}{% if loop.last == False %}; {% endif %}{% endfor %}
</td>
</tr>
{% endfor %}
</table>
{% endfor %}
