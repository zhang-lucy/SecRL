# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'GraphExtractionResult' and 'GraphExtractor' models."""

import logging
import numbers
import re
import traceback
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import networkx as nx
import tiktoken

import html
import re
import asyncio


def clean_str(input: Any) -> str:
    """Clean an input string by removing HTML escapes, control characters, and other unwanted characters."""
    # If we get non-string input, just give it back
    if not isinstance(input, str):
        return input

    result = html.unescape(input.strip())
    # https://stackoverflow.com/questions/4324790/removing-control-characters-from-a-string-in-python
    return re.sub(r"[\x00-\x1f\x7f-\x9f]", "", result)


from myllm import call_autogen

# from prompts_1 import CONTINUE_PROMPT, GRAPH_EXTRACTION_PROMPT, LOOP_PROMPT
from prompts_2 import CONTINUE_PROMPT, GRAPH_EXTRACTION_PROMPT, LOOP_PROMPT

DEFAULT_TUPLE_DELIMITER = "<|>"
DEFAULT_RECORD_DELIMITER = "##"
DEFAULT_COMPLETION_DELIMITER = "<|COMPLETE|>"
DEFAULT_ENTITY_TYPES = ["organization", "person", "geo", "event"]


@dataclass
class GraphExtractionResult:
    """Unipartite graph extraction result class definition."""

    output: nx.Graph
    source_docs: dict[Any, Any]


class GraphExtractor:
    """Unipartite graph extractor class definition."""

    _join_descriptions: bool
    _tuple_delimiter_key: str
    _record_delimiter_key: str
    _entity_types_key: str
    _input_text_key: str
    _completion_delimiter_key: str
    _entity_name_key: str
    _input_descriptions_key: str
    _extraction_prompt: str
    _summarization_prompt: str
    _loop_args: dict[str, Any]
    _max_gleanings: int
    _graph: nx.Graph = nx.Graph()
    _is_directed_graph: bool = False

    def __init__(
        self,
        tuple_delimiter_key: str | None = None,
        record_delimiter_key: str | None = None,
        input_text_key: str | None = None,
        entity_types_key: str | None = None,
        completion_delimiter_key: str | None = None,
        prompt: str | None = None,
        join_descriptions=True,
        encoding_model: str | None = None,
        max_gleanings: int | None = None,
        existing_text: str | None = None,
    ):
        """Init method definition."""
        # TODO: streamline construction
        self._join_descriptions = join_descriptions
        self._input_text_key = input_text_key or "input_text"
        self._tuple_delimiter_key = tuple_delimiter_key or "tuple_delimiter"
        self._record_delimiter_key = record_delimiter_key or "record_delimiter"
        self._completion_delimiter_key = (
            completion_delimiter_key or "completion_delimiter"
        )
        self._entity_types_key = entity_types_key or "entity_types"
        self._extraction_prompt = prompt or GRAPH_EXTRACTION_PROMPT
        self._max_gleanings = max_gleanings if max_gleanings is not None else 0

        # Construct the looping arguments
        encoding = tiktoken.get_encoding(encoding_model or "cl100k_base")
        yes = encoding.encode("YES")
        no = encoding.encode("NO")
        self._loop_args = {"logit_bias": {yes[0]: 100, no[0]: 100}, "max_tokens": 1}

        if existing_text:
            self._graph = self._naprocess_results(
                results={0: existing_text},
                tuple_delimiter=DEFAULT_TUPLE_DELIMITER,
                record_delimiter=DEFAULT_RECORD_DELIMITER,
                graph=self._graph
            )

    async def process_single_doc(
        self, text: list[str], prompt_variables: dict[str, Any] | None = None
    ) -> str:
        """Call method definition."""
        result = None
        prompt_variables = self.process_var(prompt_variables)
        try:
            # Invoke the entity extraction
            result = await self._process_document(text, prompt_variables)

            result.replace("## Entities and Relationships:", "")
            result.replace("## Entities:", "")
            result.replace("## Relationships:", "")
            result.replace("## Entities", "")
            result.replace("## Relationships", "")
            print(result)
        except Exception as e:
            logging.exception("error extracting graph")
            print(text)
        return result

    def process_var(self, prompt_variables):
        if prompt_variables is None:
            prompt_variables = {}
        # Wire defaults into the prompt variables
        prompt_variables = {
            **prompt_variables,
            self._tuple_delimiter_key: prompt_variables.get(self._tuple_delimiter_key)
            or DEFAULT_TUPLE_DELIMITER,
            self._record_delimiter_key: prompt_variables.get(self._record_delimiter_key)
            or DEFAULT_RECORD_DELIMITER,
            self._completion_delimiter_key: prompt_variables.get(
                self._completion_delimiter_key
            )
            or DEFAULT_COMPLETION_DELIMITER,
            self._entity_types_key: ",".join(
                prompt_variables[self._entity_types_key] or DEFAULT_ENTITY_TYPES
            ),
        }  
        return prompt_variables   
     
    async def __call__(
        self, texts: list[str], prompt_variables: dict[str, Any] | None = None
    ) -> GraphExtractionResult:
        """Call method definition."""

        all_records: dict[int, str] = {}
        source_doc_map: dict[int, str] = {}
        prompt_variables = self.process_var(prompt_variables)

        for doc_index, text in enumerate(texts):
            result = await self.process_single_doc(text, prompt_variables)
            if result is None:
                continue
            source_doc_map[doc_index] = text
            all_records[doc_index] = result

        output = await self._process_results(
            all_records,
            prompt_variables.get(self._tuple_delimiter_key, DEFAULT_TUPLE_DELIMITER),
            prompt_variables.get(self._record_delimiter_key, DEFAULT_RECORD_DELIMITER),
        )

        return GraphExtractionResult(
            output=output,
            source_docs=source_doc_map,
        )

    async def _process_document(
        self, text: str, prompt_variables: dict[str, str]
    ) -> str:
        response = await call_autogen(
            self._extraction_prompt,
            variables={
                **prompt_variables,
                self._input_text_key: text,

            },
        )
        results = response.output or ""

        # Repeat to ensure we maximize entity count
        for i in range(self._max_gleanings):
            glean_response = await call_autogen(
                CONTINUE_PROMPT,
                name=f"extract-continuation-{i}",
                history=response.history or [],
            )
            results += glean_response.output or ""

            # if this is the final glean, don't bother updating the continuation flag
            if i >= self._max_gleanings - 1:
                break

            continuation = await call_autogen(
                LOOP_PROMPT,
                name=f"extract-loopcheck-{i}",
                history=glean_response.history or [],
                model_parameters=self._loop_args,
            )
            if continuation.output != "YES":
                break

        return results


    async def iterative_build(
        self,
        texts: list[str],
        prompt_variables: dict[str, Any] | None = None,
    ):
        prompt_variables = self.process_var(prompt_variables)

        for doc_index, text in enumerate(texts):
            entity_text = self.graph_to_text(self._graph)
            prompt_variables["previous_entities"] = entity_text[0]
            result = await self.process_single_doc(text, prompt_variables)
            if result is None:
                continue

            self._graph = await self._process_results(
                results={doc_index: result},
                tuple_delimiter=prompt_variables.get(self._tuple_delimiter_key),
                record_delimiter=prompt_variables.get(self._record_delimiter_key),
                graph=self._graph
            )
            

    @staticmethod
    def graph_to_text(
        graph: nx.Graph,
        tuple_delimiter: str = '<|>',
        record_delimiter: str = '##'
    ) -> str:
        """Convert a graph back to the text representation.

        Args:
            - graph: A NetworkX graph.
            - tuple_delimiter: Delimiter between tuples in an output record.
            - record_delimiter: Delimiter between records.

        Returns:
            - str: Text representation of the graph.
        """
        nodes = []
        edges = []

        # Process nodes
        for node, data in graph.nodes(data=True):
            record = f'("entity"{tuple_delimiter}{node}{tuple_delimiter}{data["type"]}{tuple_delimiter}{data["description"]})'
            nodes.append(record)
        
        # Process edges
        for source, target, data in graph.edges(data=True):
            description = data.get('description', '')
            weight = data.get('weight', 1.0)
            record = f'("relationship"{tuple_delimiter}{source}{tuple_delimiter}{target}{tuple_delimiter}{description}{tuple_delimiter}{weight})'
            edges.append(record)

        record_delimiter = '\n' + record_delimiter + '\n'
        print( record_delimiter.join(nodes))
        print("----------------------------")
        return record_delimiter.join(nodes), record_delimiter.join(edges)

    async def _process_results(
        self,
        results: dict[int, str],
        tuple_delimiter: str,
        record_delimiter: str,
        graph: nx.Graph = nx.Graph(),
    ) -> nx.Graph:
        """Parse the result string to create an undirected unipartite graph.

        Args:
            - results - dict of results from the extraction chain
            - tuple_delimiter - delimiter between tuples in an output record, default is '<|>'
            - record_delimiter - delimiter between records, default is '##'
        Returns:
            - output - unipartite graph in graphML format
        """
        for source_doc_id, extracted_data in results.items():
            records = [r.strip() for r in extracted_data.split(record_delimiter)]

            for record in records:
                record = re.sub(r"^\(|\)$", "", record.strip())
                record_attributes = record.split(tuple_delimiter)

                if record_attributes[0] == '"entity"' and len(record_attributes) >= 4:
                    # add this record as a node in the G
                    entity_name = clean_str(record_attributes[1].upper())
                    entity_type = clean_str(record_attributes[2].upper())
                    entity_description = clean_str(record_attributes[3])

                    if entity_name in graph.nodes():
                        node = graph.nodes[entity_name]
                        if self._join_descriptions:
                            node["description"] = "\n".join(
                                list({
                                    *_unpack_descriptions(node),
                                    entity_description,
                                })
                            )
                        else:
                            if len(entity_description) > len(node["description"]):
                                node["description"] = entity_description
                        node["source_id"] = ", ".join(
                            list({
                                *_unpack_source_ids(node),
                                str(source_doc_id),
                            })
                        )
                        node["entity_type"] = (
                            entity_type if entity_type != "" else node["entity_type"]
                        )
                    else:
                        graph.add_node(
                            entity_name,
                            type=entity_type,
                            description=entity_description,
                            source_id=str(source_doc_id),
                        )

                if (
                    record_attributes[0] == '"relationship"'
                    and len(record_attributes) >= 5
                ):
                    # print(record_attributes)
                    # add this record as edge
                    source = clean_str(record_attributes[1].upper())
                    target = clean_str(record_attributes[2].upper())
                    edge_description = clean_str(record_attributes[3])
                    edge_source_id = clean_str(str(source_doc_id))
                    weight = (
                        float(record_attributes[-1])
                        if isinstance(record_attributes[-1], numbers.Number)
                        else 1.0
                    )
                    if source not in graph.nodes():
                        graph.add_node(
                            source,
                            type="",
                            description="",
                            source_id=edge_source_id,
                        )
                    if target not in graph.nodes():
                        graph.add_node(
                            target,
                            type="",
                            description="",
                            source_id=edge_source_id,
                        )
                    if graph.has_edge(source, target):
                        edge_data = graph.get_edge_data(source, target)
                        if edge_data is not None:
                            # weight += edge_data["weight"]
                            if self._join_descriptions:
                                edge_description = "\n".join(
                                    list({
                                        *_unpack_descriptions(edge_data),
                                        edge_description,
                                    })
                                )
                            edge_source_id = ", ".join(
                                list({
                                    *_unpack_source_ids(edge_data),
                                    str(source_doc_id),
                                })
                            )
                    graph.add_edge(
                        source,
                        target,
                        weight=weight,
                        description=edge_description,
                        source_id=edge_source_id,
                    )

        return graph

    def _naprocess_results(
        self,
        results: dict[int, str],
        tuple_delimiter: str,
        record_delimiter: str,
        graph: nx.Graph = nx.Graph(),
    ) -> nx.Graph:
        """Parse the result string to create an undirected unipartite graph.

        Args:
            - results - dict of results from the extraction chain
            - tuple_delimiter - delimiter between tuples in an output record, default is '<|>'
            - record_delimiter - delimiter between records, default is '##'
        Returns:
            - output - unipartite graph in graphML format
        """
        for source_doc_id, extracted_data in results.items():
            records = [r.strip() for r in extracted_data.split(record_delimiter)]

            for record in records:
                record = re.sub(r"^\(|\)$", "", record.strip())
                record_attributes = record.split(tuple_delimiter)

                if record_attributes[0] == '"entity"' and len(record_attributes) >= 4:
                    # add this record as a node in the G
                    entity_name = clean_str(record_attributes[1].upper())
                    entity_type = clean_str(record_attributes[2].upper())
                    entity_description = clean_str(record_attributes[3])

                    if entity_name in graph.nodes():
                        node = graph.nodes[entity_name]
                        if self._join_descriptions:
                            node["description"] = "\n".join(
                                list({
                                    *_unpack_descriptions(node),
                                    entity_description,
                                })
                            )
                        else:
                            if len(entity_description) > len(node["description"]):
                                node["description"] = entity_description
                        node["source_id"] = ", ".join(
                            list({
                                *_unpack_source_ids(node),
                                str(source_doc_id),
                            })
                        )
                        node["entity_type"] = (
                            entity_type if entity_type != "" else node["entity_type"]
                        )
                    else:
                        graph.add_node(
                            entity_name,
                            type=entity_type,
                            description=entity_description,
                            source_id=str(source_doc_id),
                        )

                if (
                    record_attributes[0] == '"relationship"'
                    and len(record_attributes) >= 5
                ):
                    # add this record as edge
                    source = clean_str(record_attributes[1].upper())
                    target = clean_str(record_attributes[2].upper())
                    edge_description = clean_str(record_attributes[3])
                    edge_source_id = clean_str(str(source_doc_id))
                    weight = (
                        float(record_attributes[-1])
                        if isinstance(record_attributes[-1], numbers.Number)
                        else 1.0
                    )
                    if source not in graph.nodes():
                        graph.add_node(
                            source,
                            type="",
                            description="",
                            source_id=edge_source_id,
                        )
                    if target not in graph.nodes():
                        graph.add_node(
                            target,
                            type="",
                            description="",
                            source_id=edge_source_id,
                        )
                    if graph.has_edge(source, target):
                        edge_data = graph.get_edge_data(source, target)
                        if edge_data is not None:
                            if self._join_descriptions:
                                edge_description = "\n".join(
                                    list({
                                        *_unpack_descriptions(edge_data),
                                        edge_description,
                                    })
                                )
                            edge_source_id = ", ".join(
                                list({
                                    *_unpack_source_ids(edge_data),
                                    str(source_doc_id),
                                })
                            )
                    graph.add_edge(
                        source,
                        target,
                        description=edge_description,
                        source_id=edge_source_id,
                    )

        return graph


def _unpack_descriptions(data: Mapping) -> list[str]:
    value = data.get("description", None)
    return [] if value is None else value.split("\n")
    return [] if value is None else value.split("\n")


def _unpack_source_ids(data: Mapping) -> list[str]:
    value = data.get("source_id", None)
    return [] if value is None else value.split(", ")
