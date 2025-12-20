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

        code.attributes["kind"] = "code"
        code.attributes["template"] = self.options.get("template")

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
                "template": directives.unchanged,
            },
            "run": run,
        },
    )


def define_template(base: type[Directive]) -> type[Directive]:
    """Define the template-code directive.

    Accepts the base directive implementation as an argument.
    """

    def run(self):
        # Modify the argument passed to the base implementation.
        template_name = self.arguments.pop(0)
        result = base.run(self)

        if not isinstance(code := result[0], nodes.literal_block):
            print(f"Unable to process {code}")
            return result

        code.attributes["kind"] = "template"
        code.attributes["name"] = template_name

        # Add a header to the code block indicating where it is being saved to.
        header = nodes.container(
            "",
            nodes.literal("", template_name, classes=["awdur-template-name"]),
            classes=["awdur-template-header"],
        )
        result.insert(0, header)

        container = nodes.container("", *result, classes=["awdur-template"])
        return [container]

        return result

    return type(
        "AwdurTemplate",
        (base,),
        {
            "required_arguments": 1,
            "option_spec": {
                **base.option_spec,
            },
            "run": run,
        },
    )
