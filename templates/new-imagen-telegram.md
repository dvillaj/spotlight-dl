**A new image has been downloaded from spotlight-dl ({{actual_images}})**

{% if title != "Unknown" %}
[{{title}}]({{image_url_landscape}})
{% else %}
[Newly Downloaded Image]({{image_url_landscape}})
{% endif %}
{% if description %}
{{description | replace('.', '.<br>')}}
{% endif %}
{% if copyright %}
{{copyright}}
{% endif %}
[Powered by SpotLight-Dl]({{home_url}})
