from __future__ import annotations

import typing

from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives

if typing.TYPE_CHECKING:
    from typing import Any


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
        )

        for attr in code_block.user_attributes:
            if (attr_value := self.options.get(attr)) is not None:
                block.attributes[attr] = attr_value

        return [block]

    return type(
        "AwdurCodeblock",
        (base,),
        {
            "option_spec": {
                **base.option_spec,
                **{a: directives.unchanged for a in code_block.user_attributes},
            },
            "run": run,
        },
    )


class code_block(nodes.General, nodes.Element):
    """A container for an awdur code block."""

    user_attributes: tuple[str, ...] = (
        "in-project",
        "in-file",
        "in-slot",
        "at-revision",
    )

    valid_attributes: tuple[str, ...] = (
        # valid_attributes not present on all docutils versions
        getattr(nodes.Element, "valid_attributes", tuple())
        + user_attributes
        + ("kind",)
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
            project=self.options.get("in-project"),
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


class ProjectDirective(Directive):
    """A directive that declares a project and any associated project level settings."""

    required_arguments = 0
    optional_arguments = 1

    has_content = True

    def run(self):
        if len(self.arguments) > 0:
            name = self.arguments[0]
        else:
            name = "default"

        container = nodes.container()
        self.state.nested_parse(self.content, self.content_offset, container)

        return [project(name=name), *container.children]


class project(nodes.General, nodes.Element):
    """A marker node used to signal where the project overview should be inserted
    into a document."""

    user_attributes: tuple[str, ...] = tuple()

    valid_attributes: tuple[str, ...] = (
        # valid_attributes not present on all docutils versions
        getattr(nodes.Element, "valid_attributes", tuple())
        + user_attributes
        + ("name",)
    )


class file(nodes.General, nodes.Element):
    """A marker node used to signal where file info should be inserted
    into a document."""

    user_attributes: tuple[str, ...] = (
        "in-project",
        "use-template",
        # TODO: do any of these make sense?
        # "in-file",
        # "in-slot",
        # "at-revision",
    )

    valid_attributes: tuple[str, ...] = (
        # valid_attributes not present on all docutils versions
        getattr(nodes.Element, "valid_attributes", tuple())
        + user_attributes
        + ("filename",)
    )


class FileDirective(Directive):
    """A directive that sets file level settings for one or more files."""

    required_arguments = 1
    optional_arguments = 0

    has_content = True

    option_spec: dict[str, Any] = {
        a: directives.unchanged for a in file.user_attributes
    }

    def run(self):
        file_node = file(filename=self.arguments[0])

        for attr in file_node.user_attributes:
            if (attr_value := self.options.get(attr)) is not None:
                file_node.attributes[attr] = attr_value

        container = nodes.container()
        self.state.nested_parse(self.content, self.content_offset, container)

        return [file_node, *container.children]
