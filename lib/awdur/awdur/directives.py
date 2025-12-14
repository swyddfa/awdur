from __future__ import annotations

import typing

from docutils import nodes
from docutils.parsers.rst import directives

if typing.TYPE_CHECKING:
    from docutils.parsers.rst import Directive


def define_codeblock(base: type[Directive]) -> type[Directive]:
    """Define the codeblock directive.

    Accepts the base directive implementation as an argument.
    """

    def run(self):
        result = base.run(self)

        if not isinstance(code := result[0], nodes.literal_block):
            print(f"Unable to process {code}")
            return result

        if (filename := self.options.get("filename")) is not None:
            code.attributes["filename"] = filename

            # Add a header to the code block indicating where it is being saved to.
            header = nodes.container(
                "",
                nodes.literal("", filename, classes=["awdur-codeblock-filename"]),
                classes=["awdur-codeblock-header"],
            )
            result.insert(0, header)

            container = nodes.container("", *result, classes=["awdur-codeblock"])
            return [container]

        return result

    return type(
        "AwdurCodeblock",
        (base,),
        {
            "option_spec": {
                **base.option_spec,
                "filename": directives.uri,
            },
            "run": run,
        },
    )
