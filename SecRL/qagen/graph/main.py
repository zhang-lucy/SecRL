from extractor import GraphExtractor

import asyncio
extractor = GraphExtractor()


a = asyncio.run(extractor(
    texts=["test_text"],
    prompt_variables={
        "entity_types": ["person"],
        "tuple_delimiter": None,
        "record_delimiter": None,
        "completion_delimiter": None,
    },
)
)

print(a)