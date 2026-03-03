"""Pydantic models that mirror the Croissant JSON-LD response."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OrgNode(BaseModel):
    type: str | None = Field(None, alias="type")
    sc_name: str | None = Field(None, alias="scName")


class FileObjectNode(BaseModel):
    type: str | None = Field(None, alias="type")
    id: str | None = Field(None, alias="id")
    sc_name: str | None = Field(None, alias="scName")
    sc_content_url: str | None = Field(None, alias="scContentUrl")
    sc_encoding_format: str | None = Field(None, alias="scEncodingFormat")
    sc_content_size: int | None = Field(None, alias="scContentSize")
    cr_sha256: str | None = Field(None, alias="crSha256")
    sc_author: str | None = Field(None, alias="scAuthor")
    sc_date_published: str | None = Field(None, alias="scDatePublished")
    sc_date_modified: str | None = Field(None, alias="scDateModified")
    sc_in_language: str | None = Field(None, alias="scInLanguage")
    sc_number_of_pages: int | None = Field(None, alias="scNumberOfPages")
    sc_word_count: int | None = Field(None, alias="scWordCount")
    ddpv_token_count: int | None = Field(None, alias="ddpvTokenCount")
    ddpv_char_count: int | None = Field(None, alias="ddpvCharCount")
    dct_subject: str | None = Field(None, alias="dctSubject")
    olac_discourse_type: str | None = Field(None, alias="olacDiscourseType")
    sc_keywords: list[str] | None = Field(None, alias="scKeywords")
    dcat_theme: list[str] | None = Field(None, alias="dcatTheme")
    dcat_theme_taxonomy: str | None = Field(None, alias="dcatThemeTaxonomy")

    model_config = {"populate_by_name": True}


class DatasetNode(BaseModel):
    type: str | None = Field(None, alias="type")
    id: str | None = Field(None, alias="id")
    sc_name: str | None = Field(None, alias="scName")
    sc_temporal_coverage: str | None = Field(None, alias="scTemporalCoverage")
    sc_spatial_coverage: str | None = Field(None, alias="scSpatialCoverage")
    sc_in_language: str | None = Field(None, alias="scInLanguage")
    sc_creator: OrgNode | None = Field(None, alias="scCreator")
    sc_publisher: OrgNode | None = Field(None, alias="scPublisher")
    sc_license: str | None = Field(None, alias="scLicense")
    sc_version: str | None = Field(None, alias="scVersion")
    cr_is_live_dataset: bool | None = Field(None, alias="crIsLiveDataset")
    distribution: list[FileObjectNode] | None = None

    model_config = {"populate_by_name": True}


class SamplingInfo(BaseModel):
    total_matched: int = Field(alias="totalMatched")
    limit: int
    returned: int
    random_sample: bool = Field(alias="randomSample")

    model_config = {"populate_by_name": True}


class CroissantResponse(BaseModel):
    context: list | None = Field(None, alias="context")
    generated_at: str | None = Field(None, alias="generatedAt")
    sampling_info: SamplingInfo | None = Field(None, alias="samplingInfo")
    graph: list[DatasetNode] | None = Field(None, alias="graph")

    model_config = {"populate_by_name": True}
