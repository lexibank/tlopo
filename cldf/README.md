<a name="ds-cldfmetadatajson"> </a>

# Wordlist The lexicon of Proto Oceanic

**CLDF Metadata**: [cldf-metadata.json](./cldf-metadata.json)

**Sources**: [sources.bib](./sources.bib)

property | value
 --- | ---
[dc:bibliographicCitation](http://purl.org/dc/terms/bibliographicCitation) | Ross, Pawley and Osmond. The lexicon of Proto Oceanic
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF Wordlist](http://cldf.clld.org/v1.0/terms.rdf#Wordlist)
[dc:identifier](http://purl.org/dc/terms/identifier) | http://hdl.handle.net/1885/106908
[dc:license](http://purl.org/dc/terms/license) | https://creativecommons.org/licenses/by/4.0/
[dc:spatial](http://purl.org/dc/terms/spatial) | <dl><dt>B.1</dt><dd>Admiralties and St Matthias Islands</dd><dt>B.2</dt><dd>Schouten (NNG) and Sarmi-Jayapura (possibly NNG)</dd><dt>B.3</dt><dd>The Ngero-Vitiaz linkage (NNG)</dd><dt>B.4</dt><dd>Huon Gulf (NNG)</dd><dt>B.5</dt><dd>Papuan Tip</dd><dt>B.6</dt><dd>New Britain and New Ireland (MM)</dd><dt>B.7</dt><dd>Northwest Solomonic linkage (MM)</dd><dt>B.8</dt><dd>Southeast Solomonic and Temotu</dd><dt>B.9</dt><dd>North Vanuatu</dd><dt>B.10</dt><dd>Central Vanuatu</dd><dt>B.11</dt><dd>South Vanuatu</dd><dt>B.12</dt><dd>Loyalty Islands and New Caledonia</dd><dt>B.13</dt><dd>Micronesian languages and Yapese</dd><dt>B.14</dt><dd>Fiji</dd><dt>B.15</dt><dd>Polynesia</dd></dl>
[dcat:accessURL](http://www.w3.org/ns/dcat#accessURL) | https://github.com/lexibank/tlopo
[prov:wasDerivedFrom](http://www.w3.org/ns/prov#wasDerivedFrom) | <ol><li><a href="https://github.com/lexibank/tlopo/tree/f53ae69">lexibank/tlopo f53ae69</a></li><li><a href="https://github.com/glottolog/glottolog/tree/v5.2">Glottolog v5.2</a></li><li><a href="https://github.com/concepticon/concepticon-data/tree/339dff57">Concepticon v3.4.0-62-g339dff57</a></li><li><a href="https://github.com/cldf-clts/clts/tree/v2.3.0">CLTS v2.3.0</a></li></ol>
[prov:wasGeneratedBy](http://www.w3.org/ns/prov#wasGeneratedBy) | <ol><li><strong>lingpy-rcParams</strong>: <a href="./lingpy-rcParams.json">lingpy-rcParams.json</a></li><li><strong>python</strong>: 3.12.3</li><li><strong>python-packages</strong>: <a href="./requirements.txt">requirements.txt</a></li></ol>
[rdf:ID](http://www.w3.org/1999/02/22-rdf-syntax-ns#ID) | tlopo
[rdf:type](http://www.w3.org/1999/02/22-rdf-syntax-ns#type) | http://www.w3.org/ns/dcat#Distribution


## <a name="table-formscsv"></a>Table [forms.csv](./forms.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF FormTable](http://cldf.clld.org/v1.0/terms.rdf#FormTable)
[dc:extent](http://purl.org/dc/terms/extent) | 43073


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Local_ID](http://purl.org/dc/terms/identifier) | `string` | 
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | References [languages.csv::ID](#table-languagescsv)
[Parameter_ID](http://cldf.clld.org/v1.0/terms.rdf#parameterReference) | `string` | References [parameters.csv::ID](#table-parameterscsv)
[Value](http://cldf.clld.org/v1.0/terms.rdf#value) | `string` | 
[Form](http://cldf.clld.org/v1.0/terms.rdf#form) | `string` | 
[Segments](http://cldf.clld.org/v1.0/terms.rdf#segments) | list of `string` (separated by ` `) | 
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
`Cognacy` | `string` | 
`Loan` | `boolean` | 
`Graphemes` | `string` | 
`Profile` | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | Description of the meaning of the word (possibly in language-specific terms).
`Sic` | `boolean` | For a form that differs from the expected reflex in some way this flag asserts that a copying mistake has not occurred.
`Doubt` | `boolean` | In particular reconstructions, i.e. proto-forms in etymological dictionaries, are often marked as being somewhat doubtful (typically displayed as proto-form prefixed with a '?' or similar).
`Morpheme_Gloss` | `string` | Some forms (often multi-word expressions) are listed with morpheme glosses.

## <a name="table-languagescsv"></a>Table [languages.csv](./languages.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF LanguageTable](http://cldf.clld.org/v1.0/terms.rdf#LanguageTable)
[dc:extent](http://purl.org/dc/terms/extent) | 761


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Glottocode](http://cldf.clld.org/v1.0/terms.rdf#glottocode) | `string` | 
`Glottolog_Name` | `string` | 
[ISO639P3code](http://cldf.clld.org/v1.0/terms.rdf#iso639P3code) | `string` | 
[Macroarea](http://cldf.clld.org/v1.0/terms.rdf#macroarea) | `string` | 
[Latitude](http://cldf.clld.org/v1.0/terms.rdf#latitude) | `decimal`<br>&ge; -90<br>&le; 90 | 
[Longitude](http://cldf.clld.org/v1.0/terms.rdf#longitude) | `decimal`<br>&ge; -180<br>&le; 180 | 
`Family` | `string` | 
`Abbr` | `string` | Abbreviation for the (proto-)language name.
`Group` | `string` | Etymological dictionaries often operate with an assumed internal classification. This column lists such groups.
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | Etymological (or comparative) dictionaries typically compare lexical data from many source dictionaries.<br>References [sources.bib::BibTeX-key](./sources.bib)
`Is_Proto` | `boolean` | Specifies whether a language is a proto-language (and thus its forms reconstructed proto-forms).
[Classification](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | Classification within Oceanic, given as /-separated nodes.
`Alternative_Names` | `string` | 
`Note` | `string` | 
`Map` | `string` | 
`Icon` | `string` | 

## <a name="table-parameterscsv"></a>Table [parameters.csv](./parameters.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF ParameterTable](http://cldf.clld.org/v1.0/terms.rdf#ParameterTable)
[dc:extent](http://purl.org/dc/terms/extent) | 19942


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Concepticon_ID](http://cldf.clld.org/v1.0/terms.rdf#concepticonReference) | `string` | 
`Concepticon_Gloss` | `string` | 

## <a name="table-cognatescsv"></a>Table [cognates.csv](./cognates.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF CognateTable](http://cldf.clld.org/v1.0/terms.rdf#CognateTable)
[dc:extent](http://purl.org/dc/terms/extent) | 41052


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Form_ID](http://cldf.clld.org/v1.0/terms.rdf#formReference) | `string` | References [forms.csv::ID](#table-formscsv)
[Form](http://linguistics-ontology.org/gold/2010/FormUnit) | `string` | 
[Cognateset_ID](http://cldf.clld.org/v1.0/terms.rdf#cognatesetReference) | `string` | References [cognatesets.csv::ID](#table-cognatesetscsv)
`Doubt` | `boolean` | 
`Cognate_Detection_Method` | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
[Alignment](http://cldf.clld.org/v1.0/terms.rdf#alignment) | list of `string` (separated by ` `) | 
`Alignment_Method` | `string` | 
`Alignment_Source` | `string` | 

## <a name="table-chapterscsv"></a>Table [chapters.csv](./chapters.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF ContributionTable](http://cldf.clld.org/v1.0/terms.rdf#ContributionTable)
[dc:extent](http://purl.org/dc/terms/extent) | 67


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
[Contributor](http://cldf.clld.org/v1.0/terms.rdf#contributor) | `string` | 
[Citation](http://cldf.clld.org/v1.0/terms.rdf#citation) | `string` | 
`Volume_Number` | `integer` | 
`Volume` | `string` | 
`Table_Of_Contents` | `json` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
`Source_To_Sections` | `json` | 

## <a name="table-cognatesetscsv"></a>Table [cognatesets.csv](./cognatesets.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF CognatesetTable](http://cldf.clld.org/v1.0/terms.rdf#CognatesetTable)
[dc:extent](http://purl.org/dc/terms/extent) | 2829


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | A recognizable label for the cognateset, typically the reconstructed proto-form and the reconstructed meaning.
[Form_ID](http://cldf.clld.org/v1.0/terms.rdf#formReference) | `string` | Links to the reconstructed proto-form in FormTable.<br>References [forms.csv::ID](#table-formscsv)
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
`Doubt` | `boolean` | Flag indicating (un)certainty of the reconstruction.
`Level` | `string` | 

## <a name="table-cfcsv"></a>Table [cf.csv](./cf.csv)

Etymological dictionaries sometimes mention "negative" results, e.g. groups of lexemes that appear to be cognates but are (temporarily) dismissed as proper cognates; for example the "noise" and "near" categories in the ACD. This includes the better defined category of loans where members of the group will be listed in BorrowingTable.

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 929


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | The title of a table of related forms; typically hints at the type of relation between the forms or between the group of forms and an etymon.
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
`Category` | `string` | An optional category for groups of forms such as "loans".
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Cognateset_ID](http://cldf.clld.org/v1.0/terms.rdf#cognatesetReference) | `string` | Links to an etymon, if the group of lexemes is related to one.<br>References [cognatesets.csv::ID](#table-cognatesetscsv)
`CognatesetReference_ID` | `string` | References [cognatesetreferences.csv::ID](#table-cognatesetreferencescsv)
[Chapter_ID](http://cldf.clld.org/v1.0/terms.rdf#contributionReference) | `string` | References [chapters.csv::ID](#table-chapterscsv)

## <a name="table-cfitemscsv"></a>Table [cfitems.csv](./cfitems.csv)

Membership of forms in a "cf" group is mediated through this association table unless more meaningful alternatives are available, like BorrowingTable for loans.

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 3938


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
`Cfset_ID` | `string` | References [cf.csv::ID](#table-cfcsv)
[Form_ID](http://cldf.clld.org/v1.0/terms.rdf#formReference) | `string` | References [forms.csv::ID](#table-formscsv)
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
`Footnote_Number` | `string` | 
`Ordinal` | `integer` | 
`Gloss_IDs` | list of `string` (separated by ` `) | References [glosses.csv::ID](#table-glossescsv)

## <a name="table-examplegroupscsv"></a>Table [examplegroups.csv](./examplegroups.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 110


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Example_IDs](http://cldf.clld.org/v1.0/terms.rdf#exampleReference) | list of `string` (separated by ` `) | References [examples.csv::ID](#table-examplescsv)
`Number` | `string` | 
[Context](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 

## <a name="table-examplescsv"></a>Table [examples.csv](./examples.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF ExampleTable](http://cldf.clld.org/v1.0/terms.rdf#ExampleTable)
[dc:extent](http://purl.org/dc/terms/extent) | 146


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | References [languages.csv::ID](#table-languagescsv)
[Primary_Text](http://cldf.clld.org/v1.0/terms.rdf#primaryText) | `string` | The example text in the source language.
[Analyzed_Word](http://cldf.clld.org/v1.0/terms.rdf#analyzedWord) | list of `string` (separated by `	`) | The sequence of words of the primary text to be aligned with glosses
[Gloss](http://cldf.clld.org/v1.0/terms.rdf#gloss) | list of `string` (separated by `	`) | The sequence of glosses aligned with the words of the primary text
[Translated_Text](http://cldf.clld.org/v1.0/terms.rdf#translatedText) | `string` | The translation of the example text in a meta language
[Meta_Language_ID](http://cldf.clld.org/v1.0/terms.rdf#metaLanguageReference) | `string` | References the language of the translated text<br>References [languages.csv::ID](#table-languagescsv)
[LGR_Conformance](http://cldf.clld.org/v1.0/terms.rdf#lgrConformance) | `string`<br>Valid choices:<br> `WORD_ALIGNED` `MORPHEME_ALIGNED` | The level of conformance of the example with the Leipzig Glossing Rules
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
`Reference_Label` | `string` | 
`label` | `string` | 
`Movement_Gloss` | list of `string` (separated by `	`) | 

## <a name="table-mediacsv"></a>Table [media.csv](./media.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF MediaTable](http://cldf.clld.org/v1.0/terms.rdf#MediaTable)
[dc:extent](http://purl.org/dc/terms/extent) | 331


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
[Media_Type](http://cldf.clld.org/v1.0/terms.rdf#mediaType) | `string`<br>Regex: `[^/]+/.+` | 
[Download_URL](http://cldf.clld.org/v1.0/terms.rdf#downloadUrl) | `anyURI` | 
[Path_In_Zip](http://cldf.clld.org/v1.0/terms.rdf#pathInZip) | `string` | 
[Chapter_ID](http://cldf.clld.org/v1.0/terms.rdf#contributionReference) | `string` | References [chapters.csv::ID](#table-chapterscsv)
[Conforms_To](http://purl.org/dc/terms/conformsTo) | `string` | 

## <a name="table-cognatesetreferencescsv"></a>Table [cognatesetreferences.csv](./cognatesetreferences.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 3092


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Cognateset_ID](http://cldf.clld.org/v1.0/terms.rdf#cognatesetReference) | `string` | References [cognatesets.csv::ID](#table-cognatesetscsv)
[Chapter_ID](http://cldf.clld.org/v1.0/terms.rdf#contributionReference) | `string` | References [chapters.csv::ID](#table-chapterscsv)
[Form_IDs](http://cldf.clld.org/v1.0/terms.rdf#formReference) | list of `string` (separated by ` `) | References [forms.csv::ID](#table-formscsv)
`Subgroup_Mapping` | `json` | 
`Footnote_Numbers` | `json` | 
`Gloss_IDs` | list of `string` (separated by ` `) | References [glosses.csv::ID](#table-glossescsv)

## <a name="table-glossescsv"></a>Table [glosses.csv](./glosses.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 45683


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
`Taxon_IDs` | list of `string` (separated by ` `) | References [taxa.csv::ID](#table-taxacsv)
`qualifier` | `string` | 
[Form_ID](http://cldf.clld.org/v1.0/terms.rdf#formReference) | `string` | Links to the form in FormTable.<br>References [forms.csv::ID](#table-formscsv)
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
`Part_Of_Speech` | `string` | 

## <a name="table-taxacsv"></a>Table [taxa.csv](./taxa.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 1281


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[GBIF_ID](http://cldf.clld.org/v1.0/terms.rdf#gbifReference) | `string` | 
[name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
`name_eng` | `string` | 
`rank` | `string`<br>Valid choices:<br> `SPECIES` `GENUS` | 
`kingdom` | `string` | 
`phylum` | `string` | 
`class` | `string` | 
`order` | `string` | 
`family` | `string` | 
`genus` | `string` | 
`genus_eng` | `string` | 
`family_eng` | `string` | 
`synonyms` | list of `string` (separated by `; `) | 
`sections` | `json` | 

## <a name="table-treescsv"></a>Table [trees.csv](./trees.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF TreeTable](http://cldf.clld.org/v1.0/terms.rdf#TreeTable)
[dc:extent](http://purl.org/dc/terms/extent) | 1


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | Name of tree as used in the tree file, i.e. the tree label in a Nexus file or the 1-based index of the tree in a newick file
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | Describe the method that was used to create the tree, etc.
[Tree_Is_Rooted](http://cldf.clld.org/v1.0/terms.rdf#treeIsRooted) | `boolean`<br>Valid choices:<br> `Yes` `No` | Whether the tree is rooted (Yes) or unrooted (No) (or no info is available (null))
[Tree_Type](http://cldf.clld.org/v1.0/terms.rdf#treeType) | `string`<br>Valid choices:<br> `summary` `sample` | Whether the tree is a summary (or consensus) tree, i.e. can be analysed in isolation, or whether it is a sample, resulting from a method that creates multiple trees
[Tree_Branch_Length_Unit](http://cldf.clld.org/v1.0/terms.rdf#treeBranchLengthUnit) | `string`<br>Valid choices:<br> `change` `substitutions` `years` `centuries` `millennia` | The unit used to measure evolutionary time in phylogenetic trees.
[Media_ID](http://cldf.clld.org/v1.0/terms.rdf#mediaReference) | `string` | References a file containing a Newick representation of the tree, labeled with identifiers as described in the LanguageTable (the [Media_Type](https://cldf.clld.org/v1.0/terms.html#mediaType) column of this table should provide enough information to chose the appropriate tool to read the newick)<br>References [media.csv::ID](#table-mediacsv)
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)

