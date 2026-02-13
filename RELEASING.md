# Releasing tlopo

Recreate the CLDF dataset:

```shell
cldfbench lexibank.makecldf lexibank_tlopo.py --glottolog-version v5.2
```

Validate it:
```shell
cldf validate cldf/
```

Create the metadata:
```shell
cldfbench cldfreadme lexibank_tlopo.py
```


Make sure the HTML pages which are ingested by the clld app can be rendered:

```shell
cldfbench tlopo.render
```
