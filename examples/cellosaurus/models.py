# THIS FILE IS GENERATED AUTOMATICALLY. DO NOT EDIT
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import ArrayField






# Corresponds to XSD type[s]:
#  typename1.publicationList_publication.authorList_consortium
class AuthorConsortium(models.Model):
    # @name => name
    name = models.TextField("name")
    publication = models.ForeignKey(
        'Publication',
        on_delete=models.CASCADE,
        related_name="authorList_consortium",
        verbose_name="Describes a publication."
    )


# Corresponds to XSD type[s]:
#  typename1.publicationList_publication.authorList_person
class AuthorPerson(models.Model):
    # @name => name
    name = models.TextField("name")
    publication = models.ForeignKey(
        'Publication',
        on_delete=models.CASCADE,
        related_name="authorList_person",
        verbose_name="Describes a publication."
    )


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.derivedFromSiteList_derived-from-site
class DerivedFromSite(models.Model):
    AUTO_ONE_TO_MANY_FIELDS = {
        "site": "Describes a body part or organ.",
    }
    # site is declared as a reverse relation
    #  from Site
    # site = OneToManyField(
    #     Site,
    #     verbose_name="Describes a body part or organ."
    # )
    # site-note => siteNote
    siteNote = models.TextField("siteNote", null=True)

    class Meta:
        verbose_name = (
            "Describes a body part or organ the cell line is derived from."
        )


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.doublingTimeList_doubling-time
class DoublingTime(models.Model):
    AUTO_ONE_TO_MANY_FIELDS = {
        "doublingTimeSources_xrefList_xref":
            "Describes doubling time observed for the cell line.::\n"
            "Describes the collection of cross-references for the entry.::\n"
            "Describes a cross-reference.",
    }
    # doubling-time-value => doublingTimeValue
    doublingTimeValue = models.TextField("doublingTimeValue")
    # doubling-time-note => doublingTimeNote
    doublingTimeNote = models.TextField("doublingTimeNote", null=True)
    # doubling-time-sources.xref-list.xref => doublingTimeSources_xrefList_xref
    # doublingTimeSources_xrefList_xref is declared as a reverse relation
    #  from DoublingTimeSourceXref
    # doublingTimeSources_xrefList_xref = OneToManyField(
    #     DoublingTimeSourceXref,
    #     verbose_name="Describes doubling time observed for the cell line.::\n"
    #     "Describes the collection of cross-references for the "
    #     "entry.::\n"
    #     "Describes a cross-reference."
    # )
    # doubling-time-sources.reference-list.reference =>
    #  doublingTimeSources_referenceList_reference
    doublingTimeSources_referenceList_reference = ArrayField(models.TextField(
        "Describes doubling time observed for the cell line.::\n"
        "Describes the references for short tandem repeats (STRs) for a cell "
        "line.::\n"
        "doublingTimeSources_referenceList_reference::doublingTimeSources_referenceList_reference"
    ), null=True)
    # xs:choice start
    # doubling-time-sources.source-list.source =>
    #  doublingTimeSources_sourceList_source
    doublingTimeSources_sourceList_source = models.TextField(
        "Describes doubling time observed for the cell line.::\n"
        "Describes the sources for short tandem repeats (STRs) for a cell "
        "line.::\n"
        "doublingTimeSources_sourceList_source",
        null=True
    )
    # doubling-time-sources.source-list.reference-list.reference =>
    #  doublingTimeSources_sourceList_referenceList_reference
    doublingTimeSources_sourceList_referenceList_reference = ArrayField(models.TextField(
        "Describes doubling time observed for the cell line.::\n"
        "Describes the sources for short tandem repeats (STRs) for a cell "
        "line.::\n"
        "Describes the references for short tandem repeats (STRs) for a cell "
        "line.::\n"
        "doublingTimeSources_sourceList_referenceList_reference::doublingTimeSources_sourceList_referenceList_reference"
    ), null=True)
    # xs:choice end

    class Meta:
        verbose_name = "Describes doubling time observed for the cell line."


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.hlaTypingList_hla-typing
class HlaTyping(models.Model):
    AUTO_ONE_TO_MANY_FIELDS = {
        "hlaGeneAllelesList_hlaGeneAlleles":
            "Describes a list of HLA gene alleles for a cell line.::\n"
            "hlaGeneAllelesList_hlaGeneAlleles",
        "hlaTypingSource_xref_propertyList_property":
            "Describes the HLA source for a cell line and a HLA typing "
            "list.::\n"
            "Describes a cross-reference.::\n"
            "Describes the collection of properties.::\n"
            "hlaTypingSource_xref_propertyList_property",
    }
    # hla-gene-alleles-list.hla-gene-alleles =>
    #  hlaGeneAllelesList_hlaGeneAlleles
    # hlaGeneAllelesList_hlaGeneAlleles is declared as a reverse relation
    #  from HlaTypingGeneAlleles
    # hlaGeneAllelesList_hlaGeneAlleles = OneToManyField(
    #     HlaTypingGeneAlleles,
    #     verbose_name="Describes a list of HLA gene alleles for a cell "
    #     "line.::\n"
    #     "hlaGeneAllelesList_hlaGeneAlleles"
    # )
    # xs:choice start
    # hla-typing-source.source => hlaTypingSource_source
    hlaTypingSource_source = models.TextField(
        "Describes the HLA source for a cell line and a HLA typing list.::\n"
        "hlaTypingSource_source",
        null=True
    )
    # hla-typing-source.xref.@database => hlaTypingSource_xref_database
    hlaTypingSource_xref_database = models.TextField(
        "Describes the HLA source for a cell line and a HLA typing list.::\n"
        "Describes a cross-reference.::\n"
        "hlaTypingSource_xref_database",
        null=True
    )
    # hla-typing-source.xref.@category => hlaTypingSource_xref_category
    hlaTypingSource_xref_category = models.CharField(
        "Describes the HLA source for a cell line and a HLA typing list.::\n"
        "Describes a cross-reference.::\n"
        "hlaTypingSource_xref_category",
        choices=[
            ("Anatomy/cell type resources", "Anatomy/cell type resources"),
            ("Biological sample resources", "Biological sample resources"),
            ("Cell line collections (Providers)", "Cell line collections (Providers)"),
            ("Cell line databases/resources", "Cell line databases/resources"),
            ("Chemistry resources", "Chemistry resources"),
            ("Encyclopedic resources", "Encyclopedic resources"),
            ("Experimental variables resources", "Experimental variables resources"),
            ("Gene expression databases", "Gene expression databases"),
            ("Medical resources", "Medical resources"),
            ("Metabolomic databases", "Metabolomic databases"),
            ("Organism-specific databases", "Organism-specific databases"),
            ("Polymorphism and mutation databases", "Polymorphism and mutation databases"),
            ("Proteomic databases", "Proteomic databases"),
            ("Reference resources", "Reference resources"),
            ("Sequence databases", "Sequence databases"),
            ("Taxonomy", "Taxonomy")
        ],
        max_length=35,
        null=True
    )
    # hla-typing-source.xref.@accession => hlaTypingSource_xref_accession
    hlaTypingSource_xref_accession = models.TextField(
        "Describes the HLA source for a cell line and a HLA typing list.::\n"
        "Describes a cross-reference.::\n"
        "hlaTypingSource_xref_accession",
        null=True
    )
    # hla-typing-source.xref.property-list.property =>
    #  hlaTypingSource_xref_propertyList_property
    # hlaTypingSource_xref_propertyList_property is declared as a reverse relation
    #  from HlaTypingSourceXrefProperty
    # hlaTypingSource_xref_propertyList_property = OneToManyField(
    #     HlaTypingSourceXrefProperty,
    #     verbose_name="Describes the HLA source for a cell line and a HLA "
    #     "typing list.::\n"
    #     "Describes a cross-reference.::\n"
    #     "Describes the collection of properties.::\n"
    #     "hlaTypingSource_xref_propertyList_property"
    # )
    # hla-typing-source.xref.url => hlaTypingSource_xref_url
    hlaTypingSource_xref_url = models.TextField(
        "Describes the HLA source for a cell line and a HLA typing list.::\n"
        "Describes a cross-reference.::\n"
        "hlaTypingSource_xref_url",
        null=True
    )
    # hla-typing-source.reference.@resource-internal-ref =>
    #  hlaTypingSource_reference_resourceInternalRef
    hlaTypingSource_reference_resourceInternalRef = models.TextField(
        "Describes the HLA source for a cell line and a HLA typing list.::\n"
        "hlaTypingSource_reference::\n"
        "hlaTypingSource_reference_resourceInternalRef",
        null=True
    )
    # xs:choice end

    class Meta:
        verbose_name = (
            "Describes the HLA genes and alleles for the cell line."
        )


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.misspellingList_misspelling
class Misspelling(models.Model):
    AUTO_ONE_TO_MANY_FIELDS = {
        "xrefList_xref":
            "Describes the collection of cross-references for the entry.::\n"
            "Describes a cross-reference.",
    }
    # misspelling-name => misspellingName
    misspellingName = models.TextField("misspellingName")
    # misspelling-note => misspellingNote
    misspellingNote = models.TextField("misspellingNote", null=True)
    # xref-list.xref => xrefList_xref
    # xrefList_xref is declared as a reverse relation
    #  from MisspellingXref
    # xrefList_xref = OneToManyField(
    #     MisspellingXref,
    #     verbose_name="Describes the collection of cross-references for the "
    #     "entry.::\n"
    #     "Describes a cross-reference."
    # )
    # reference-list.reference => referenceList_reference
    referenceList_reference = ArrayField(models.TextField(
        "Describes the references for short tandem repeats (STRs) for a cell "
        "line.::\n"
        "referenceList_reference::referenceList_reference"
    ), null=True)

    class Meta:
        verbose_name = "Describes a misspelling."


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.sequenceVariationList_sequence-variation
class SequenceVariation(models.Model):
    AUTO_ONE_TO_MANY_FIELDS = {
        "variationSources":
            "Describes the sources for sequence variation for a cell line.",
        "xrefList_xref":
            "Describes the collection of cross-references for the entry.::\n"
            "Describes a cross-reference.",
    }
    # @variation-type => variationType
    variationType = models.CharField(
        "variationType",
        choices=[
            ("Gene amplification", "Gene amplification"),
            ("Gene deletion", "Gene deletion"),
            ("Gene fusion", "Gene fusion"),
            ("Mutation", "Mutation")
        ],
        max_length=18
    )
    # @mutation-type => mutationType
    mutationType = models.CharField(
        "mutationType",
        choices=[
            ("Duplication", "Duplication"),
            ("Triplication", "Triplication"),
            ("Quadruplication", "Quadruplication"),
            ("Extensive", "Extensive"),
            ("Simple", "Simple"),
            ("Simple_corrected", "Simple_corrected"),
            ("Simple_edited", "Simple_edited"),
            ("Repeat_expansion", "Repeat_expansion"),
            ("Repeat_expansion_corrected", "Repeat_expansion_corrected"),
            ("Repeat_expansion_edited", "Repeat_expansion_edited"),
            ("Unexplicit", "Unexplicit"),
            ("Unexplicit_corrected", "Unexplicit_corrected"),
            ("Unexplicit_edited", "Unexplicit_edited"),
            ("None_reported", "None_reported")
        ],
        max_length=26,
        null=True
    )
    # @zygosity-type => zygosityType
    zygosityType = models.CharField(
        "zygosityType",
        choices=[
            ("Hemizygous", "Hemizygous"),
            ("Heteroplasmic", "Heteroplasmic"),
            ("Heterozygous", "Heterozygous"),
            ("Homoplasmic", "Homoplasmic"),
            ("Homozygous", "Homozygous"),
            ("Mosaic", "Mosaic"),
            ("Unspecified", "Unspecified"),
            ("-", "-")
        ],
        max_length=13,
        null=True
    )
    # mutation-description => mutationDescription
    mutationDescription = models.TextField("mutationDescription", null=True)
    # variation-note => variationNote
    variationNote = models.TextField("variationNote", null=True)
    # xref-list.xref => xrefList_xref
    # xrefList_xref is declared as a reverse relation
    #  from SequenceVariationXref
    # xrefList_xref = OneToManyField(
    #     SequenceVariationXref,
    #     verbose_name="Describes the collection of cross-references for the "
    #     "entry.::\n"
    #     "Describes a cross-reference."
    # )
    # variation-sources => variationSources
    # variationSources is declared as a reverse relation
    #  from SequenceVariationSource
    # variationSources = OneToManyField(
    #     SequenceVariationSource,
    #     verbose_name="Describes the sources for sequence variation for a "
    #     "cell line."
    # )


# Corresponds to XSD type[s]: typename1.cellLineList_cell-line
class CellLine(models.Model):
    AUTO_ONE_TO_MANY_FIELDS = {
        "accessionList_accession":
            "Describes the collection of accession numbers for a cell line.::\n"
            "accessionList_accession",
        "commentList_comment":
            "Describes the collection of comments for a cell line.::\n"
            "Describes a comment concerning the cell line.",
        "derivedFrom_cvTerm":
            "Describes the hierarchy for the cell line.::\n"
            "derivedFrom_cvTerm",
        "diseaseList_cvTerm":
            "Describes the diseases associated with the cell line.::\n"
            "diseaseList_cvTerm",
        "genomeAncestry_populationList_population":
            "Describes the genome ancestry for a cell line.::\n"
            "Describes the population list of a cell line genome ancestry.::\n"
            "genomeAncestry_populationList_population",
        "nameList_name":
            "Describes the collection of names for a cell line.::\n"
            "nameList_name",
        "registrationList_registration":
            "Describes the collection of registrations for a cell line.::\n"
            "registrationList_registration",
        "sameOriginAs_cvTerm":
            "Describes cell lines that originate from same individual as the "
            "cell line.::\n"
            "sameOriginAs_cvTerm",
        "speciesList_cvTerm":
            "Describes the species of origin for the cell line.::\n"
            "speciesList_cvTerm",
        "strList_markerList":
            "Describes the collection of short tandem repeats (STRs) for a "
            "cell line.::\n"
            "Describes the short tandem repeats (STRs) markers for a cell "
            "line.",
        "xrefList_xref":
            "Describes the collection of cross-references for the entry.::\n"
            "Describes a cross-reference.",
    }
    # @category => category
    category = models.CharField(
        "category",
        choices=[
            ("Cancer cell line", "Cancer cell line"),
            ("Conditionally immortalized cell line", "Conditionally immortalized cell line"),
            ("Embryonic stem cell", "Embryonic stem cell"),
            ("Factor-dependent cell line", "Factor-dependent cell line"),
            ("Finite cell line", "Finite cell line"),
            ("Hybrid cell line", "Hybrid cell line"),
            ("Hybridoma", "Hybridoma"),
            ("Induced pluripotent stem cell", "Induced pluripotent stem cell"),
            ("Somatic stem cell", "Somatic stem cell"),
            ("Spontaneously immortalized cell line", "Spontaneously immortalized cell line"),
            ("Stromal cell line", "Stromal cell line"),
            ("Telomerase immortalized cell line", "Telomerase immortalized cell line"),
            ("Transformed cell line", "Transformed cell line"),
            ("Undefined cell line type", "Undefined cell line type")
        ],
        max_length=36
    )
    # @sex => sex
    sex = models.CharField(
        "sex",
        choices=[
            ("Female", "Female"),
            ("Male", "Male"),
            ("Mixed sex", "Mixed sex"),
            ("Sex ambiguous", "Sex ambiguous"),
            ("Sex unspecified", "Sex unspecified")
        ],
        max_length=15,
        null=True
    )
    # @created => created
    created = models.DateField("created")
    # @last-updated => lastUpdated
    lastUpdated = models.DateField("lastUpdated")
    # @entry-version => entryVersion
    entryVersion = models.IntegerField("entryVersion")
    # @age => age
    age = models.JSONField("age", null=True)
    # accession-list.accession => accessionList_accession
    # accessionList_accession is declared as a reverse relation
    #  from CellLineAccession
    # accessionList_accession = OneToManyField(
    #     CellLineAccession,
    #     verbose_name="Describes the collection of accession numbers for a "
    #     "cell line.::\n"
    #     "accessionList_accession"
    # )
    # name-list.name => nameList_name
    # nameList_name is declared as a reverse relation
    #  from CellLineName
    # nameList_name = OneToManyField(
    #     CellLineName,
    #     verbose_name="Describes the collection of names for a cell line.::\n"
    #     "nameList_name"
    # )
    # comment-list.comment => commentList_comment
    # commentList_comment is declared as a reverse relation
    #  from Comment
    # commentList_comment = OneToManyField(
    #     Comment,
    #     verbose_name="Describes the collection of comments for a cell "
    #     "line.::\n"
    #     "Describes a comment concerning the cell line."
    # )
    # xs:choice start
    # str-list.source-list.source => strList_sourceList_source
    strList_sourceList_source = models.TextField(
        "Describes the collection of short tandem repeats (STRs) for a cell "
        "line.::\n"
        "Describes the sources for short tandem repeats (STRs) for a cell "
        "line.::\n"
        "strList_sourceList_source",
        null=True
    )
    # str-list.source-list.reference-list.reference =>
    #  strList_sourceList_referenceList_reference
    strList_sourceList_referenceList_reference = ArrayField(models.TextField(
        "Describes the collection of short tandem repeats (STRs) for a cell "
        "line.::\n"
        "Describes the sources for short tandem repeats (STRs) for a cell "
        "line.::\n"
        "Describes the references for short tandem repeats (STRs) for a cell "
        "line.::\n"
        "strList_sourceList_referenceList_reference::strList_sourceList_referenceList_reference"
    ), null=True)
    # xs:choice end
    # str-list.marker-list => strList_markerList
    # strList_markerList is declared as a reverse relation
    #  from StrMarker
    # strList_markerList = OneToManyField(
    #     StrMarker,
    #     verbose_name="Describes the collection of short tandem repeats "
    #     "(STRs) for a cell line.::\n"
    #     "Describes the short tandem repeats (STRs) markers for"
    #     " a cell line."
    # )
    # disease-list.cv-term => diseaseList_cvTerm
    # diseaseList_cvTerm is declared as a reverse relation
    #  from Disease
    # diseaseList_cvTerm = OneToManyField(
    #     Disease,
    #     verbose_name="Describes the diseases associated with the cell "
    #     "line.::\n"
    #     "diseaseList_cvTerm"
    # )
    # species-list.cv-term => speciesList_cvTerm
    # speciesList_cvTerm is declared as a reverse relation
    #  from Species
    # speciesList_cvTerm = OneToManyField(
    #     Species,
    #     verbose_name="Describes the species of origin for the cell line.::\n"
    #     "speciesList_cvTerm"
    # )
    # derived-from.cv-term => derivedFrom_cvTerm
    # derivedFrom_cvTerm is declared as a reverse relation
    #  from DerivedFrom
    # derivedFrom_cvTerm = OneToManyField(
    #     DerivedFrom,
    #     verbose_name="Describes the hierarchy for the cell line.::\n"
    #     "derivedFrom_cvTerm"
    # )
    # same-origin-as.cv-term => sameOriginAs_cvTerm
    # sameOriginAs_cvTerm is declared as a reverse relation
    #  from SameOriginAs
    # sameOriginAs_cvTerm = OneToManyField(
    #     SameOriginAs,
    #     verbose_name="Describes cell lines that originate from same "
    #     "individual as the cell line.::\n"
    #     "sameOriginAs_cvTerm"
    # )
    # web-page-list => webPageList
    webPageList = ArrayField(models.TextField(
        "Describes web pages for the entry.::webPageList"
    ), null=True)
    # reference-list.reference => referenceList_reference
    referenceList_reference = ArrayField(models.TextField(
        "Describes the references for short tandem repeats (STRs) for a cell "
        "line.::\n"
        "referenceList_reference::referenceList_reference"
    ), null=True)
    # hla-typing-list => hlaTypingList
    hlaTypingList = models.ManyToManyField(
        HlaTyping,
        verbose_name="Describes HLA typing list for a cell line."
    )
    # doubling-time-list => doublingTimeList
    doublingTimeList = models.ManyToManyField(
        DoublingTime,
        verbose_name="Describes the list of doubling time(s) observed for "
        "the cell line."
    )
    # derived-from-site-list => derivedFromSiteList
    derivedFromSiteList = models.ManyToManyField(
        DerivedFromSite,
        verbose_name="Describes the list of body parts or organs the cell "
        "line is derived from."
    )
    # cell-type.cv-term.@terminology => cellType_cvTerm_terminology
    cellType_cvTerm_terminology = models.CharField(
        "Describes the cell-type the cell line is derived from.::\n"
        "cellType_cvTerm::\n"
        "cellType_cvTerm_terminology",
        choices=[
            ("Cellosaurus", "Cellosaurus"),
            ("ChEBI", "ChEBI"),
            ("DrugBank", "DrugBank"),
            ("NCBI-Taxonomy", "NCBI-Taxonomy"),
            ("NCIt", "NCIt"),
            ("ORDO", "ORDO"),
            ("PubChem", "PubChem"),
            ("UBERON", "UBERON"),
            ("CL", "CL")
        ],
        max_length=13,
        null=True
    )
    # cell-type.cv-term.@accession => cellType_cvTerm_accession
    cellType_cvTerm_accession = models.TextField(
        "Describes the cell-type the cell line is derived from.::\n"
        "cellType_cvTerm::\n"
        "cellType_cvTerm_accession",
        null=True
    )
    # cell-type.cv-term => cellType_cvTerm
    cellType_cvTerm = models.TextField(
        "Describes the cell-type the cell line is derived from.::\n"
        "cellType_cvTerm",
        null=True
    )
    # genome-ancestry.population-list.population =>
    #  genomeAncestry_populationList_population
    # genomeAncestry_populationList_population is declared as a reverse relation
    #  from GenomeAncestryPopulation
    # genomeAncestry_populationList_population = OneToManyField(
    #     GenomeAncestryPopulation,
    #     verbose_name="Describes the genome ancestry for a cell line.::\n"
    #     "Describes the population list of a cell line genome "
    #     "ancestry.::\n"
    #     "genomeAncestry_populationList_population"
    # )
    # xs:choice start
    # genome-ancestry.genome-ancestry-source.source =>
    #  genomeAncestry_source_source
    genomeAncestry_source_source = models.TextField(
        "Describes the genome ancestry for a cell line.::\n"
        "Describes the source for a genome ancestry record.::\n"
        "genomeAncestry_source_source",
        null=True
    )
    # genome-ancestry.genome-ancestry-source.reference.@resource-internal-ref =>
    #  genomeAncestry_source_reference_resourceInternalRef
    genomeAncestry_source_reference_resourceInternalRef = models.TextField(
        "Describes the genome ancestry for a cell line.::\n"
        "Describes the source for a genome ancestry record.::\n"
        "genomeAncestry_genomeAncestrySource_reference::\n"
        "genomeAncestry_source_reference_resourceInternalRef",
        null=True
    )
    # xs:choice end
    # misspelling-list => misspellingList
    misspellingList = models.ManyToManyField(
        Misspelling,
        verbose_name="Describes the collection of misspellings for a cell "
        "line."
    )
    # registration-list.registration => registrationList_registration
    # registrationList_registration is declared as a reverse relation
    #  from Registration
    # registrationList_registration = OneToManyField(
    #     Registration,
    #     verbose_name="Describes the collection of registrations for a cell "
    #     "line.::\n"
    #     "registrationList_registration"
    # )
    # sequence-variation-list => sequenceVariationList
    sequenceVariationList = models.ManyToManyField(
        SequenceVariation,
        verbose_name="Describes the sequence variations for a cell line."
    )
    # xref-list.xref => xrefList_xref
    # xrefList_xref is declared as a reverse relation
    #  from CellLineXref
    # xrefList_xref = OneToManyField(
    #     CellLineXref,
    #     verbose_name="Describes the collection of cross-references for the "
    #     "entry.::\n"
    #     "Describes a cross-reference."
    # )

    class Meta:
        verbose_name = "Describes a cell line entry."


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.accessionList_accession
class CellLineAccession(models.Model):
    # @type => type
    type = models.CharField(
        "type",
        choices=[
            ("primary", "primary"),
            ("secondary", "secondary")
        ],
        max_length=9
    )
    accession = models.TextField("accession")
    cell_line = models.ForeignKey(
        'CellLine',
        on_delete=models.CASCADE,
        related_name="accessionList_accession",
        verbose_name="Describes a cell line entry."
    )


# Corresponds to XSD type[s]: typename1.cellLineList_cell-line.nameList_name
class CellLineName(models.Model):
    # @type => type
    type = models.CharField(
        "type",
        choices=[
            ("identifier", "identifier"),
            ("synonym", "synonym")
        ],
        max_length=10
    )
    name = models.TextField("name")
    cell_line = models.ForeignKey(
        'CellLine',
        on_delete=models.CASCADE,
        related_name="nameList_name",
        verbose_name="Describes a cell line entry."
    )


# Corresponds to XSD type[s]: typename1.cellLineList_cell-line.xrefList_xref
class CellLineXref(models.Model):
    AUTO_ONE_TO_MANY_FIELDS = {
        "propertyList_property":
            "Describes the collection of properties.::\n"
            "propertyList_property",
    }
    # @database => database
    database = models.TextField("database")
    # @category => category
    category = models.CharField(
        "category",
        choices=[
            ("Anatomy/cell type resources", "Anatomy/cell type resources"),
            ("Biological sample resources", "Biological sample resources"),
            ("Cell line collections (Providers)", "Cell line collections (Providers)"),
            ("Cell line databases/resources", "Cell line databases/resources"),
            ("Chemistry resources", "Chemistry resources"),
            ("Encyclopedic resources", "Encyclopedic resources"),
            ("Experimental variables resources", "Experimental variables resources"),
            ("Gene expression databases", "Gene expression databases"),
            ("Medical resources", "Medical resources"),
            ("Metabolomic databases", "Metabolomic databases"),
            ("Organism-specific databases", "Organism-specific databases"),
            ("Polymorphism and mutation databases", "Polymorphism and mutation databases"),
            ("Proteomic databases", "Proteomic databases"),
            ("Reference resources", "Reference resources"),
            ("Sequence databases", "Sequence databases"),
            ("Taxonomy", "Taxonomy")
        ],
        max_length=35
    )
    # @accession => accession
    accession = models.TextField("accession")
    # property-list.property => propertyList_property
    # propertyList_property is declared as a reverse relation
    #  from CellLineXrefProperty
    # propertyList_property = OneToManyField(
    #     CellLineXrefProperty,
    #     verbose_name="Describes the collection of properties.::\n"
    #     "propertyList_property"
    # )
    url = models.TextField("url", null=True)
    cell_line = models.ForeignKey(
        'CellLine',
        on_delete=models.CASCADE,
        related_name="xrefList_xref",
        verbose_name="Describes a cell line entry."
    )

    class Meta:
        verbose_name = "Describes a cross-reference."


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.xrefList_xref.propertyList_property
class CellLineXrefProperty(models.Model):
    # @name => name
    name = models.TextField("name")
    # @value => value
    value = models.TextField("value")
    # @value-type => valueType
    valueType = models.TextField("valueType", null=True)
    # @accession => accession
    accession = models.TextField("accession", null=True)
    cell_line_xref = models.ForeignKey(
        'CellLineXref',
        on_delete=models.CASCADE,
        related_name="propertyList_property",
        verbose_name="Describes a cross-reference."
    )


# Corresponds to XSD type[s]: typename1.header_terminologyList_terminology
class Terminology(models.Model):
    # @name => name
    name = models.JSONField("name")
    # @source => source
    source = models.JSONField("source")
    # @description => description
    description = models.JSONField("description")
    # @release => release
    release = models.JSONField("release", null=True)
    url = models.TextField("url")

    class Meta:
        verbose_name = "Describes a terminology used in the Cellosaurus."


# Corresponds to XSD type[s]: typename1
class Cellosaurus(models.Model):
    AUTO_ONE_TO_MANY_FIELDS = {
        "publicationList":
            "Describes the collection of publications for the entry.",
    }
    # header.terminology-name => header_terminologyName
    header_terminologyName = models.TextField(
        "Describes the header.::header_terminologyName"
    )
    header_description = models.TextField(
        "Describes the header.::header_description"
    )
    # header.release.@version => header_release_version
    header_release_version = models.DecimalField(
        "Describes the header.::header_release::\n"
        "header_release_version",
        decimal_places=5,
        max_digits=10
    )
    # header.release.@updated => header_release_updated
    header_release_updated = models.DateField(
        "Describes the header.::header_release::\n"
        "header_release_updated"
    )
    # header.release.@nb-cell-lines => header_release_nbCellLines
    header_release_nbCellLines = models.IntegerField(
        "Describes the header.::header_release::\n"
        "header_release_nbCellLines"
    )
    # header.release.@nb-publications => header_release_nbPublications
    header_release_nbPublications = models.IntegerField(
        "Describes the header.::header_release::\n"
        "header_release_nbPublications"
    )
    # header.terminology-list => header_terminologyList
    header_terminologyList = models.ManyToManyField(
        Terminology,
        verbose_name="Describes the header.::Describes the terminologies "
        "used in the Cellosaurus."
    )
    # cell-line-list => cellLineList
    cellLineList = models.ManyToManyField(
        CellLine,
        verbose_name="Describes the collection of cell lines and parts "
        "thereof."
    )
    # publication-list => publicationList
    # publicationList is declared as a reverse relation
    #  from Publication
    # publicationList = OneToManyField(
    #     Publication,
    #     verbose_name="Describes the collection of publications for the "
    #     "entry."
    # )
    copyright = models.TextField("copyright")

    class Meta:
        verbose_name = "Describes the Cellosaurus XML file."


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.commentList_comment
class Comment(models.Model):
    AUTO_ONE_TO_MANY_FIELDS = {
        "xrefList_xref":
            "Describes the collection of cross-references for the entry.::\n"
            "Describes a cross-reference.",
    }
    # @category => category
    category = models.CharField(
        "category",
        choices=[
            ("Anecdotal", "Anecdotal"),
            ("Biotechnology", "Biotechnology"),
            ("Breed/subspecies", "Breed/subspecies"),
            ("Caution", "Caution"),
            ("Characteristics", "Characteristics"),
            ("Discontinued", "Discontinued"),
            ("Donor information", "Donor information"),
            ("From", "From"),
            ("Group", "Group"),
            ("Karyotypic information", "Karyotypic information"),
            ("Knockout cell", "Knockout cell"),
            ("Microsatellite instability", "Microsatellite instability"),
            ("Miscellaneous", "Miscellaneous"),
            ("Monoclonal antibody isotype", "Monoclonal antibody isotype"),
            ("Monoclonal antibody target", "Monoclonal antibody target"),
            ("Omics", "Omics"),
            ("Part of", "Part of"),
            ("Population", "Population"),
            ("Problematic cell line", "Problematic cell line"),
            ("Selected for resistance to", "Selected for resistance to"),
            ("Senescence", "Senescence"),
            ("Transfected with", "Transfected with"),
            ("Transformant", "Transformant"),
            ("Virology", "Virology")
        ],
        max_length=27
    )
    method = models.TextField("method", null=True)
    # xref-list.xref => xrefList_xref
    # xrefList_xref is declared as a reverse relation
    #  from CommentXref
    # xrefList_xref = OneToManyField(
    #     CommentXref,
    #     verbose_name="Describes the collection of cross-references for the "
    #     "entry.::\n"
    #     "Describes a cross-reference."
    # )
    # cv-term.@terminology => cvTerm_terminology
    cvTerm_terminology = models.CharField(
        "cvTerm::cvTerm_terminology",
        choices=[
            ("Cellosaurus", "Cellosaurus"),
            ("ChEBI", "ChEBI"),
            ("DrugBank", "DrugBank"),
            ("NCBI-Taxonomy", "NCBI-Taxonomy"),
            ("NCIt", "NCIt"),
            ("ORDO", "ORDO"),
            ("PubChem", "PubChem"),
            ("UBERON", "UBERON"),
            ("CL", "CL")
        ],
        max_length=13,
        null=True
    )
    # cv-term.@accession => cvTerm_accession
    cvTerm_accession = models.TextField("cvTerm::cvTerm_accession", null=True)
    # cv-term => cvTerm
    cvTerm = models.TextField("cvTerm", null=True)
    cell_line = models.ForeignKey(
        'CellLine',
        on_delete=models.CASCADE,
        related_name="commentList_comment",
        verbose_name="Describes a cell line entry."
    )

    class Meta:
        verbose_name = "Describes a comment concerning the cell line."


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.commentList_comment.xrefList_xref
class CommentXref(models.Model):
    AUTO_ONE_TO_MANY_FIELDS = {
        "propertyList_property":
            "Describes the collection of properties.::\n"
            "propertyList_property",
    }
    # @database => database
    database = models.TextField("database")
    # @category => category
    category = models.CharField(
        "category",
        choices=[
            ("Anatomy/cell type resources", "Anatomy/cell type resources"),
            ("Biological sample resources", "Biological sample resources"),
            ("Cell line collections (Providers)", "Cell line collections (Providers)"),
            ("Cell line databases/resources", "Cell line databases/resources"),
            ("Chemistry resources", "Chemistry resources"),
            ("Encyclopedic resources", "Encyclopedic resources"),
            ("Experimental variables resources", "Experimental variables resources"),
            ("Gene expression databases", "Gene expression databases"),
            ("Medical resources", "Medical resources"),
            ("Metabolomic databases", "Metabolomic databases"),
            ("Organism-specific databases", "Organism-specific databases"),
            ("Polymorphism and mutation databases", "Polymorphism and mutation databases"),
            ("Proteomic databases", "Proteomic databases"),
            ("Reference resources", "Reference resources"),
            ("Sequence databases", "Sequence databases"),
            ("Taxonomy", "Taxonomy")
        ],
        max_length=35
    )
    # @accession => accession
    accession = models.TextField("accession")
    # property-list.property => propertyList_property
    # propertyList_property is declared as a reverse relation
    #  from CommentXrefProperty
    # propertyList_property = OneToManyField(
    #     CommentXrefProperty,
    #     verbose_name="Describes the collection of properties.::\n"
    #     "propertyList_property"
    # )
    url = models.TextField("url", null=True)
    comment = models.ForeignKey(
        'Comment',
        on_delete=models.CASCADE,
        related_name="xrefList_xref",
        verbose_name="Describes a comment concerning the cell line."
    )

    class Meta:
        verbose_name = "Describes a cross-reference."


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.commentList_comment.xrefList_xref.propertyList_property
class CommentXrefProperty(models.Model):
    # @name => name
    name = models.TextField("name")
    # @value => value
    value = models.TextField("value")
    # @value-type => valueType
    valueType = models.TextField("valueType", null=True)
    # @accession => accession
    accession = models.TextField("accession", null=True)
    comment_xref = models.ForeignKey(
        'CommentXref',
        on_delete=models.CASCADE,
        related_name="propertyList_property",
        verbose_name="Describes a cross-reference."
    )


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.derivedFrom_cvTerm
class DerivedFrom(models.Model):
    # @terminology => terminology
    terminology = models.CharField(
        "terminology",
        choices=[
            ("Cellosaurus", "Cellosaurus"),
            ("ChEBI", "ChEBI"),
            ("DrugBank", "DrugBank"),
            ("NCBI-Taxonomy", "NCBI-Taxonomy"),
            ("NCIt", "NCIt"),
            ("ORDO", "ORDO"),
            ("PubChem", "PubChem"),
            ("UBERON", "UBERON"),
            ("CL", "CL")
        ],
        max_length=13
    )
    # @accession => accession
    accession = models.TextField("accession")
    # cv-term => cvTerm
    cvTerm = models.TextField("cvTerm")
    cell_line = models.ForeignKey(
        'CellLine',
        on_delete=models.CASCADE,
        related_name="derivedFrom_cvTerm",
        verbose_name="Describes a cell line entry."
    )


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.diseaseList_cvTerm
class Disease(models.Model):
    # @terminology => terminology
    terminology = models.CharField(
        "terminology",
        choices=[
            ("Cellosaurus", "Cellosaurus"),
            ("ChEBI", "ChEBI"),
            ("DrugBank", "DrugBank"),
            ("NCBI-Taxonomy", "NCBI-Taxonomy"),
            ("NCIt", "NCIt"),
            ("ORDO", "ORDO"),
            ("PubChem", "PubChem"),
            ("UBERON", "UBERON"),
            ("CL", "CL")
        ],
        max_length=13
    )
    # @accession => accession
    accession = models.TextField("accession")
    # cv-term => cvTerm
    cvTerm = models.TextField("cvTerm")
    cell_line = models.ForeignKey(
        'CellLine',
        on_delete=models.CASCADE,
        related_name="diseaseList_cvTerm",
        verbose_name="Describes a cell line entry."
    )


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.doublingTimeList_doubling-time.doublingTimeSources_xrefList_xref
class DoublingTimeSourceXref(models.Model):
    AUTO_ONE_TO_MANY_FIELDS = {
        "propertyList_property":
            "Describes the collection of properties.::\n"
            "propertyList_property",
    }
    # @database => database
    database = models.TextField("database")
    # @category => category
    category = models.CharField(
        "category",
        choices=[
            ("Anatomy/cell type resources", "Anatomy/cell type resources"),
            ("Biological sample resources", "Biological sample resources"),
            ("Cell line collections (Providers)", "Cell line collections (Providers)"),
            ("Cell line databases/resources", "Cell line databases/resources"),
            ("Chemistry resources", "Chemistry resources"),
            ("Encyclopedic resources", "Encyclopedic resources"),
            ("Experimental variables resources", "Experimental variables resources"),
            ("Gene expression databases", "Gene expression databases"),
            ("Medical resources", "Medical resources"),
            ("Metabolomic databases", "Metabolomic databases"),
            ("Organism-specific databases", "Organism-specific databases"),
            ("Polymorphism and mutation databases", "Polymorphism and mutation databases"),
            ("Proteomic databases", "Proteomic databases"),
            ("Reference resources", "Reference resources"),
            ("Sequence databases", "Sequence databases"),
            ("Taxonomy", "Taxonomy")
        ],
        max_length=35
    )
    # @accession => accession
    accession = models.TextField("accession")
    # property-list.property => propertyList_property
    # propertyList_property is declared as a reverse relation
    #  from DoublingTimeSourceXrefProperty
    # propertyList_property = OneToManyField(
    #     DoublingTimeSourceXrefProperty,
    #     verbose_name="Describes the collection of properties.::\n"
    #     "propertyList_property"
    # )
    url = models.TextField("url", null=True)
    doubling_time = models.ForeignKey(
        'DoublingTime',
        on_delete=models.CASCADE,
        related_name="doublingTimeSources_xrefList_xref",
        verbose_name="Describes doubling time observed for the cell line."
    )

    class Meta:
        verbose_name = "Describes a cross-reference."


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.doublingTimeList_doubling-
#  time.doublingTimeSources_xrefList_xref.propertyList_property
class DoublingTimeSourceXrefProperty(models.Model):
    # @name => name
    name = models.TextField("name")
    # @value => value
    value = models.TextField("value")
    # @value-type => valueType
    valueType = models.TextField("valueType", null=True)
    # @accession => accession
    accession = models.TextField("accession", null=True)
    doubling_time_source_xref = models.ForeignKey(
        'DoublingTimeSourceXref',
        on_delete=models.CASCADE,
        related_name="propertyList_property",
        verbose_name="Describes a cross-reference."
    )


# Corresponds to XSD type[s]:
#  typename1.publicationList_publication.editorList_consortium
class EditorConsortium(models.Model):
    # @name => name
    name = models.TextField("name")
    publication = models.ForeignKey(
        'Publication',
        on_delete=models.CASCADE,
        related_name="editorList_consortium",
        verbose_name="Describes a publication."
    )


# Corresponds to XSD type[s]:
#  typename1.publicationList_publication.editorList_person
class EditorPerson(models.Model):
    # @name => name
    name = models.TextField("name")
    publication = models.ForeignKey(
        'Publication',
        on_delete=models.CASCADE,
        related_name="editorList_person",
        verbose_name="Describes a publication."
    )


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.genomeAncestry_populationList_population
class GenomeAncestryPopulation(models.Model):
    # @population-name => populationName
    populationName = models.CharField(
        "populationName",
        choices=[
            ("African", "African"),
            ("Native American", "Native American"),
            ("East Asian, North", "East Asian, North"),
            ("East Asian, South", "East Asian, South"),
            ("South Asian", "South Asian"),
            ("European, North", "European, North"),
            ("European, South", "European, South")
        ],
        max_length=17
    )
    # @population-percentage => populationPercentage
    populationPercentage = models.TextField("populationPercentage")
    cell_line = models.ForeignKey(
        'CellLine',
        on_delete=models.CASCADE,
        related_name="genomeAncestry_populationList_population",
        verbose_name="Describes a cell line entry."
    )


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.hlaTypingList_hla-typing.hlaGeneAllelesList_hlaGeneAlleles
class HlaTypingGeneAlleles(models.Model):
    # @alleles => alleles
    alleles = models.TextField("alleles")
    # @gene => gene
    gene = models.TextField("gene")
    hla_typing = models.ForeignKey(
        'HlaTyping',
        on_delete=models.CASCADE,
        related_name="hlaGeneAllelesList_hlaGeneAlleles",
        verbose_name="Describes the HLA genes and alleles for the cell "
        "line."
    )


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.hlaTypingList_hla-typing.hlaTypingSource_xref_propertyList_property
class HlaTypingSourceXrefProperty(models.Model):
    # @name => name
    name = models.TextField("name")
    # @value => value
    value = models.TextField("value")
    # @value-type => valueType
    valueType = models.TextField("valueType", null=True)
    # @accession => accession
    accession = models.TextField("accession", null=True)
    hla_typing = models.ForeignKey(
        'HlaTyping',
        on_delete=models.CASCADE,
        related_name="hlaTypingSource_xref_propertyList_property",
        verbose_name="Describes the HLA genes and alleles for the cell "
        "line."
    )


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.misspellingList_misspelling.xrefList_xref
class MisspellingXref(models.Model):
    AUTO_ONE_TO_MANY_FIELDS = {
        "propertyList_property":
            "Describes the collection of properties.::\n"
            "propertyList_property",
    }
    # @database => database
    database = models.TextField("database")
    # @category => category
    category = models.CharField(
        "category",
        choices=[
            ("Anatomy/cell type resources", "Anatomy/cell type resources"),
            ("Biological sample resources", "Biological sample resources"),
            ("Cell line collections (Providers)", "Cell line collections (Providers)"),
            ("Cell line databases/resources", "Cell line databases/resources"),
            ("Chemistry resources", "Chemistry resources"),
            ("Encyclopedic resources", "Encyclopedic resources"),
            ("Experimental variables resources", "Experimental variables resources"),
            ("Gene expression databases", "Gene expression databases"),
            ("Medical resources", "Medical resources"),
            ("Metabolomic databases", "Metabolomic databases"),
            ("Organism-specific databases", "Organism-specific databases"),
            ("Polymorphism and mutation databases", "Polymorphism and mutation databases"),
            ("Proteomic databases", "Proteomic databases"),
            ("Reference resources", "Reference resources"),
            ("Sequence databases", "Sequence databases"),
            ("Taxonomy", "Taxonomy")
        ],
        max_length=35
    )
    # @accession => accession
    accession = models.TextField("accession")
    # property-list.property => propertyList_property
    # propertyList_property is declared as a reverse relation
    #  from MisspellingXrefProperty
    # propertyList_property = OneToManyField(
    #     MisspellingXrefProperty,
    #     verbose_name="Describes the collection of properties.::\n"
    #     "propertyList_property"
    # )
    url = models.TextField("url", null=True)
    misspelling = models.ForeignKey(
        'Misspelling',
        on_delete=models.CASCADE,
        related_name="xrefList_xref",
        verbose_name="Describes a misspelling."
    )

    class Meta:
        verbose_name = "Describes a cross-reference."


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.misspellingList_misspelling.xrefList_xref.propertyList_property
class MisspellingXrefProperty(models.Model):
    # @name => name
    name = models.TextField("name")
    # @value => value
    value = models.TextField("value")
    # @value-type => valueType
    valueType = models.TextField("valueType", null=True)
    # @accession => accession
    accession = models.TextField("accession", null=True)
    misspelling_xref = models.ForeignKey(
        'MisspellingXref',
        on_delete=models.CASCADE,
        related_name="propertyList_property",
        verbose_name="Describes a cross-reference."
    )


# Corresponds to XSD type[s]: typename1.publicationList_publication
class Publication(models.Model):
    AUTO_ONE_TO_MANY_FIELDS = {
        "authorList_consortium":
            "Describes the authors of a publication.::\n"
            "authorList_consortium",
        "authorList_person":
            "Describes the authors of a publication.::\n"
            "authorList_person",
        "editorList_consortium":
            "Describes the editors of a publication.::\n"
            "editorList_consortium",
        "editorList_person":
            "Describes the editors of a publication.::\n"
            "editorList_person",
        "xrefList_xref":
            "Describes the collection of cross-references for the entry.::\n"
            "Describes a cross-reference.",
    }
    # @type => type
    type = models.CharField(
        "type",
        choices=[
            ("article", "article"),
            ("book chapter", "book chapter"),
            ("patent", "patent"),
            ("thesis BSc", "thesis BSc"),
            ("thesis MD", "thesis MD"),
            ("thesis MDSc", "thesis MDSc"),
            ("thesis MSc", "thesis MSc"),
            ("thesis PD", "thesis PD"),
            ("thesis PhD", "thesis PhD"),
            ("thesis VMD", "thesis VMD")
        ],
        max_length=12
    )
    # @date => date
    date = models.TextField("date", null=True)
    # @journal-name => journalName
    journalName = models.TextField("journalName", null=True)
    # @volume => volume
    volume = models.TextField("volume", null=True)
    # @first-page => firstPage
    firstPage = models.TextField("firstPage", null=True)
    # @last-page => lastPage
    lastPage = models.TextField("lastPage", null=True)
    # @publisher => publisher
    publisher = models.TextField("publisher", null=True)
    # @city => city
    city = models.TextField("city", null=True)
    # @database => database
    database = models.TextField("database", null=True)
    # @patent => patent
    patent = models.TextField("patent", null=True)
    # @institution => institution
    institution = models.TextField("institution", null=True)
    # @country => country
    country = models.TextField("country", null=True)
    # @location => location
    location = models.TextField("location", null=True)
    # @internal-id => internalId
    internalId = models.TextField("internalId")
    title = models.TextField("title")
    # xs:choice start
    # editor-list.consortium => editorList_consortium
    # editorList_consortium is declared as a reverse relation
    #  from EditorConsortium
    # editorList_consortium = OneToManyField(
    #     EditorConsortium,
    #     verbose_name="Describes the editors of a publication.::\n"
    #     "editorList_consortium"
    # )
    # editor-list.person => editorList_person
    # editorList_person is declared as a reverse relation
    #  from EditorPerson
    # editorList_person = OneToManyField(
    #     EditorPerson,
    #     verbose_name="Describes the editors of a publication.::\n"
    #     "editorList_person"
    # )
    # xs:choice end
    # xs:choice start
    # author-list.consortium => authorList_consortium
    # authorList_consortium is declared as a reverse relation
    #  from AuthorConsortium
    # authorList_consortium = OneToManyField(
    #     AuthorConsortium,
    #     verbose_name="Describes the authors of a publication.::\n"
    #     "authorList_consortium"
    # )
    # author-list.person => authorList_person
    # authorList_person is declared as a reverse relation
    #  from AuthorPerson
    # authorList_person = OneToManyField(
    #     AuthorPerson,
    #     verbose_name="Describes the authors of a publication.::\n"
    #     "authorList_person"
    # )
    # xs:choice end
    # xref-list.xref => xrefList_xref
    # xrefList_xref is declared as a reverse relation
    #  from PublicationXref
    # xrefList_xref = OneToManyField(
    #     PublicationXref,
    #     verbose_name="Describes the collection of cross-references for the "
    #     "entry.::\n"
    #     "Describes a cross-reference."
    # )
    cellosaurus = models.ForeignKey(
        'Cellosaurus',
        on_delete=models.CASCADE,
        related_name="publicationList",
        verbose_name="Describes the Cellosaurus XML file."
    )

    class Meta:
        verbose_name = "Describes a publication."


# Corresponds to XSD type[s]:
#  typename1.publicationList_publication.xrefList_xref
class PublicationXref(models.Model):
    AUTO_ONE_TO_MANY_FIELDS = {
        "propertyList_property":
            "Describes the collection of properties.::\n"
            "propertyList_property",
    }
    # @database => database
    database = models.TextField("database")
    # @category => category
    category = models.CharField(
        "category",
        choices=[
            ("Anatomy/cell type resources", "Anatomy/cell type resources"),
            ("Biological sample resources", "Biological sample resources"),
            ("Cell line collections (Providers)", "Cell line collections (Providers)"),
            ("Cell line databases/resources", "Cell line databases/resources"),
            ("Chemistry resources", "Chemistry resources"),
            ("Encyclopedic resources", "Encyclopedic resources"),
            ("Experimental variables resources", "Experimental variables resources"),
            ("Gene expression databases", "Gene expression databases"),
            ("Medical resources", "Medical resources"),
            ("Metabolomic databases", "Metabolomic databases"),
            ("Organism-specific databases", "Organism-specific databases"),
            ("Polymorphism and mutation databases", "Polymorphism and mutation databases"),
            ("Proteomic databases", "Proteomic databases"),
            ("Reference resources", "Reference resources"),
            ("Sequence databases", "Sequence databases"),
            ("Taxonomy", "Taxonomy")
        ],
        max_length=35
    )
    # @accession => accession
    accession = models.TextField("accession")
    # property-list.property => propertyList_property
    # propertyList_property is declared as a reverse relation
    #  from PublicationXrefProperty
    # propertyList_property = OneToManyField(
    #     PublicationXrefProperty,
    #     verbose_name="Describes the collection of properties.::\n"
    #     "propertyList_property"
    # )
    url = models.TextField("url", null=True)
    publication = models.ForeignKey(
        'Publication',
        on_delete=models.CASCADE,
        related_name="xrefList_xref",
        verbose_name="Describes a publication."
    )

    class Meta:
        verbose_name = "Describes a cross-reference."


# Corresponds to XSD type[s]:
#  typename1.publicationList_publication.xrefList_xref.propertyList_property
class PublicationXrefProperty(models.Model):
    # @name => name
    name = models.TextField("name")
    # @value => value
    value = models.TextField("value")
    # @value-type => valueType
    valueType = models.TextField("valueType", null=True)
    # @accession => accession
    accession = models.TextField("accession", null=True)
    publication_xref = models.ForeignKey(
        'PublicationXref',
        on_delete=models.CASCADE,
        related_name="propertyList_property",
        verbose_name="Describes a cross-reference."
    )


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.registrationList_registration
class Registration(models.Model):
    # @registry => registry
    registry = models.JSONField("registry")
    # @registration-number => registrationNumber
    registrationNumber = models.JSONField("registrationNumber")
    cell_line = models.ForeignKey(
        'CellLine',
        on_delete=models.CASCADE,
        related_name="registrationList_registration",
        verbose_name="Describes a cell line entry."
    )


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.sameOriginAs_cvTerm
class SameOriginAs(models.Model):
    # @terminology => terminology
    terminology = models.CharField(
        "terminology",
        choices=[
            ("Cellosaurus", "Cellosaurus"),
            ("ChEBI", "ChEBI"),
            ("DrugBank", "DrugBank"),
            ("NCBI-Taxonomy", "NCBI-Taxonomy"),
            ("NCIt", "NCIt"),
            ("ORDO", "ORDO"),
            ("PubChem", "PubChem"),
            ("UBERON", "UBERON"),
            ("CL", "CL")
        ],
        max_length=13
    )
    # @accession => accession
    accession = models.TextField("accession")
    # cv-term => cvTerm
    cvTerm = models.TextField("cvTerm")
    cell_line = models.ForeignKey(
        'CellLine',
        on_delete=models.CASCADE,
        related_name="sameOriginAs_cvTerm",
        verbose_name="Describes a cell line entry."
    )


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.sequenceVariationList_sequence-variation.variationSources
class SequenceVariationSource(models.Model):
    # xs:choice start
    source = models.TextField("source", null=True)
    # reference-list.reference => referenceList_reference
    referenceList_reference = ArrayField(models.TextField(
        "Describes the references for short tandem repeats (STRs) for a cell "
        "line.::\n"
        "referenceList_reference::referenceList_reference"
    ), null=True)
    # xs:choice end
    sequence_variation = models.ForeignKey(
        'SequenceVariation',
        on_delete=models.CASCADE,
        related_name="variationSources",
        verbose_name="sequence_variation"
    )

    class Meta:
        verbose_name = (
            "Describes the sources for sequence variation for a cell line."
        )


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.sequenceVariationList_sequence-variation.xrefList_xref
class SequenceVariationXref(models.Model):
    AUTO_ONE_TO_MANY_FIELDS = {
        "propertyList_property":
            "Describes the collection of properties.::\n"
            "propertyList_property",
    }
    # @database => database
    database = models.TextField("database")
    # @category => category
    category = models.CharField(
        "category",
        choices=[
            ("Anatomy/cell type resources", "Anatomy/cell type resources"),
            ("Biological sample resources", "Biological sample resources"),
            ("Cell line collections (Providers)", "Cell line collections (Providers)"),
            ("Cell line databases/resources", "Cell line databases/resources"),
            ("Chemistry resources", "Chemistry resources"),
            ("Encyclopedic resources", "Encyclopedic resources"),
            ("Experimental variables resources", "Experimental variables resources"),
            ("Gene expression databases", "Gene expression databases"),
            ("Medical resources", "Medical resources"),
            ("Metabolomic databases", "Metabolomic databases"),
            ("Organism-specific databases", "Organism-specific databases"),
            ("Polymorphism and mutation databases", "Polymorphism and mutation databases"),
            ("Proteomic databases", "Proteomic databases"),
            ("Reference resources", "Reference resources"),
            ("Sequence databases", "Sequence databases"),
            ("Taxonomy", "Taxonomy")
        ],
        max_length=35
    )
    # @accession => accession
    accession = models.TextField("accession")
    # property-list.property => propertyList_property
    # propertyList_property is declared as a reverse relation
    #  from SequenceVariationXrefProperty
    # propertyList_property = OneToManyField(
    #     SequenceVariationXrefProperty,
    #     verbose_name="Describes the collection of properties.::\n"
    #     "propertyList_property"
    # )
    url = models.TextField("url", null=True)
    sequence_variation = models.ForeignKey(
        'SequenceVariation',
        on_delete=models.CASCADE,
        related_name="xrefList_xref",
        verbose_name="sequence_variation"
    )

    class Meta:
        verbose_name = "Describes a cross-reference."


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.sequenceVariationList_sequence-
#  variation.xrefList_xref.propertyList_property
class SequenceVariationXrefProperty(models.Model):
    # @name => name
    name = models.TextField("name")
    # @value => value
    value = models.TextField("value")
    # @value-type => valueType
    valueType = models.TextField("valueType", null=True)
    # @accession => accession
    accession = models.TextField("accession", null=True)
    sequence_variation_xref = models.ForeignKey(
        'SequenceVariationXref',
        on_delete=models.CASCADE,
        related_name="propertyList_property",
        verbose_name="Describes a cross-reference."
    )


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.derivedFromSiteList_derived-from-site.site
class Site(models.Model):
    AUTO_ONE_TO_MANY_FIELDS = {
        "cvTerm": "",
    }
    # @site-type => siteType
    siteType = models.CharField(
        "siteType",
        choices=[
            ("In situ", "In situ"),
            ("Metastatic", "Metastatic")
        ],
        max_length=10
    )
    # cv-term => cvTerm
    # cvTerm is declared as a reverse relation
    #  from SiteCvTerm
    # cvTerm = OneToManyField(SiteCvTerm, verbose_name="cvTerm")
    derived_from_site = models.ForeignKey(
        'DerivedFromSite',
        on_delete=models.CASCADE,
        related_name="site",
        verbose_name="Describes a body part or organ the cell line is "
        "derived from."
    )

    class Meta:
        verbose_name = "Describes a body part or organ."


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.derivedFromSiteList_derived-from-site.site.cvTerm
class SiteCvTerm(models.Model):
    # @terminology => terminology
    terminology = models.CharField(
        "terminology",
        choices=[
            ("Cellosaurus", "Cellosaurus"),
            ("ChEBI", "ChEBI"),
            ("DrugBank", "DrugBank"),
            ("NCBI-Taxonomy", "NCBI-Taxonomy"),
            ("NCIt", "NCIt"),
            ("ORDO", "ORDO"),
            ("PubChem", "PubChem"),
            ("UBERON", "UBERON"),
            ("CL", "CL")
        ],
        max_length=13
    )
    # @accession => accession
    accession = models.TextField("accession")
    # cv-term => cvTerm
    cvTerm = models.TextField("cvTerm")
    site = models.ForeignKey(
        'Site',
        on_delete=models.CASCADE,
        related_name="cvTerm",
        verbose_name="Describes a body part or organ."
    )


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.speciesList_cvTerm
class Species(models.Model):
    # @terminology => terminology
    terminology = models.CharField(
        "terminology",
        choices=[
            ("Cellosaurus", "Cellosaurus"),
            ("ChEBI", "ChEBI"),
            ("DrugBank", "DrugBank"),
            ("NCBI-Taxonomy", "NCBI-Taxonomy"),
            ("NCIt", "NCIt"),
            ("ORDO", "ORDO"),
            ("PubChem", "PubChem"),
            ("UBERON", "UBERON"),
            ("CL", "CL")
        ],
        max_length=13
    )
    # @accession => accession
    accession = models.TextField("accession")
    # cv-term => cvTerm
    cvTerm = models.TextField("cvTerm")
    cell_line = models.ForeignKey(
        'CellLine',
        on_delete=models.CASCADE,
        related_name="speciesList_cvTerm",
        verbose_name="Describes a cell line entry."
    )


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.strList_markerList_marker
class StrMarker(models.Model):
    AUTO_ONE_TO_MANY_FIELDS = {
        "markerDataList_markerData":
            "Describes the collection of STR marker data for a cell line.::\n"
            "Describes the STR marker data for a cell line.",
    }
    # @id => cellosaurus_id
    cellosaurus_id = models.TextField("cellosaurus_id")
    # @conflict => conflict
    conflict = models.BooleanField("conflict")
    # marker-data-list.marker-data => markerDataList_markerData
    # markerDataList_markerData is declared as a reverse relation
    #  from StrMarkerData
    # markerDataList_markerData = OneToManyField(
    #     StrMarkerData,
    #     verbose_name="Describes the collection of STR marker data for a "
    #     "cell line.::\n"
    #     "Describes the STR marker data for a cell line."
    # )
    cell_line = models.ForeignKey(
        'CellLine',
        on_delete=models.CASCADE,
        related_name="strList_markerList",
        verbose_name="Describes a cell line entry."
    )

    class Meta:
        verbose_name = (
            "Describes a short tandem repeats (STRs) marker for a cell line."
        )


# Corresponds to XSD type[s]: typename1.cellLineList_cell-
#  line.strList_markerList_marker.markerDataList_markerData
class StrMarkerData(models.Model):
    # marker-alleles => markerAlleles
    markerAlleles = models.TextField("markerAlleles")
    # xs:choice start
    # source-list.source => sourceList_source
    sourceList_source = models.TextField(
        "Describes the sources for short tandem repeats (STRs) for a cell "
        "line.::\n"
        "sourceList_source",
        null=True
    )
    # source-list.reference-list.reference => sourceList_referenceList_reference
    sourceList_referenceList_reference = ArrayField(models.TextField(
        "Describes the sources for short tandem repeats (STRs) for a cell "
        "line.::\n"
        "Describes the references for short tandem repeats (STRs) for a cell "
        "line.::\n"
        "sourceList_referenceList_reference::sourceList_referenceList_reference"
    ), null=True)
    # xs:choice end
    str_marker = models.ForeignKey(
        'StrMarker',
        on_delete=models.CASCADE,
        related_name="markerDataList_markerData",
        verbose_name="Describes a short tandem repeats (STRs) marker for a "
        "cell line."
    )

    class Meta:
        verbose_name = "Describes the STR marker data for a cell line."
