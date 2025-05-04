cf. also: {{ ctx['Name'] or '' }}
<table>
{% for item in cldf['cfitems.csv']: %}
{% if item['Cfset_ID'] == ctx['ID'] %}
<tr>
<td>{{ cldf.get_object('FormTable', item['Form_ID']).language.name }}</td>
<td>{{ cldf.get_object('FormTable', item['Form_ID']).cldf.value }}</td>
<td>{{ cldf.get_object('FormTable', item['Form_ID']).cldf.description }}</td>
</tr>
{% endif %}
{% endfor %}
</table>