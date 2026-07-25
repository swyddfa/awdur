from __future__ import annotations

from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives


class project_tree(nodes.General, nodes.Element):
    """A marker node used to inject a browsable view of the project into a document."""


class code_block(nodes.General, nodes.Element):
    """A container for an awdur code block."""


def define_codeblock(base: type[Directive]) -> type[Directive]:
    """Define the codeblock directive.

    Accepts the base directive implementation as an argument.
    """

    def run(self):
        result = base.run(self)

        block = code_block(
            "",
            *result,
            kind="code",
            template=self.options.get("template"),
            project=self.options.get("project", "default"),
        )

        if (filename := self.options.get("filename")) is not None:
            block.attributes["filename"] = filename

        return [block]

    return type(
        "AwdurCodeblock",
        (base,),
        {
            "option_spec": {
                **base.option_spec,
                "filename": directives.uri,
                "project": directives.unchanged,
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

        block = code_block(
            "",
            *result,
            kind="template",
            name=template_name,
            project=self.options.get("project", "default"),
        )

        return [block]

    return type(
        "AwdurTemplate",
        (base,),
        {
            "required_arguments": 1,
            "option_spec": {
                **base.option_spec,
                "project": directives.unchanged,
            },
            "run": run,
        },
    )


class ProjectTreeDirective(Directive):
    """A directive that inserts a project file browser into the page."""

    required_arguments = 0
    optional_arguments = 1

    def run(self):
        if len(self.arguments) > 0:
            name = self.arguments[0]
        else:
            name = "default"

        return [project_tree(name=name)]


class project_tree(nodes.General, nodes.Element):
    pass
