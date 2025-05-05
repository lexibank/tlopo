{# 
 Render a Cognateset.
 
 - cognates
 or table of cognates with alingnments!
 #}
{% import 'util.md' as util %}


{% if ctx.data['Pre_Note'] %}{{ ctx.data['Pre_Note'] }}{% endif %}

<table>
{% for cog in ctx.cognates: %}
<tr>
{% if cog.form.language.data['Is_Proto'] %}
<td><strong>{{ cog.form.language.name }}</strong></td><td> </td>
<td>
<i>&ast;{{ cog.form.cldf.value }}</i>
{{ util.references(cog.form.references, with_internal_ref_link=1) }}
</td>
<td>
{% for gloss in cldf.cached_rows('glosses.csv') if gloss['Form_ID'] == cog.form.id %}
‘{{ gloss['Name']|markdown }}’{% if gloss['Comment'] %} ({{ gloss['Comment']|markdown }}){% endif %}{% if gloss['Source']: %} ({% for src in gloss['Source']: %}<a href="#source-{{ src }}">{{ src }}</a>{% if loop.last == False %}; {% endif %}{% endfor %}){% endif %}{% if loop.last == False %}; {% endif %} 
{% endfor %}
</td>
{% else: %}
<td>{{ cog.form.language.data['Group'] }}</td><td>{{ cog.form.language.name }}</td><td><i>{{ cog.form.cldf.value }}</i></td>
<td>
{% for gloss in cldf.cached_rows('glosses.csv') if gloss['Form_ID'] == cog.form.id %}
{% if gloss['Part_Of_Speech'] %}({{ gloss['Part_Of_Speech'] }}) {% endif %}{% if gloss['Name'] %}‘{{ gloss['Name']|markdown }}’{% endif %}{% if gloss['Comment'] %} ({{ gloss['Comment']|markdown }}){% endif %}{% if gloss['Source']: %} ({% for src in gloss['Source']: %}<a href="#source-{{ src }}">{{ src }}</a>{% if loop.last == False %}; {% endif %}{% endfor %}){% endif %}{% if loop.last == False %}; {% endif %} 
{% endfor %}
</td>
{% endif %}
</tr>
{% endfor %}
</table>

{% for cf in cldf['cf.csv']: %}
{% if cf['Cognateset_ID'] == ctx.id %}
cf. also: {{ cf['Name'] or '' }}
<table>
{% for item in cldf['cfitems.csv']: %}
{% if item['Cfset_ID'] == cf['ID'] %}
<tr>
<td>{{ cldf.get_object('FormTable', item['Form_ID']).language.name }}</td>
<td>{{ cldf.get_object('FormTable', item['Form_ID']).cldf.value }}</td>
<td>{{ cldf.get_object('FormTable', item['Form_ID']).cldf.description }}</td>
</tr>
{% endif %}
{% endfor %}
</table>
{% endif %}
{% endfor %}

{% if ctx.data['Post_Note'] %}{{ ctx.data['Post_Note'] }}{% endif %}
