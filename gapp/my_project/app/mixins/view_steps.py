"""
Multi-step view mixins for complex forms.
"""

import logging
from typing import Any

from django.template.loader import render_to_string

# Configure logger for this module.
logger = logging.getLogger(__name__)


def render_stepwise_form_with_navigation_buttons(context: dict[str, Any]) -> str:
    """
    Renders a multi-step form with navigation buttons to move between steps.

    :param context: A dictionary containing the 'form_class' as class type of step-wise forms and
                     'step_index' specifying current index in flow.
    :return: Returns rendered HTML string representing currently active page/form section based on passed parameters.
             Navigation links/buttons are displayed for moving forward, backward or to previously visited pages if any (not implemented).
    """

    try:
        # Extracting form class and step_index from context dictionary with default values
        form_class = str(context["form_class"])
        step_index = int(context.get("step_index", 0))

        if not hasattr(form_class, "__init__"):
            raise ValueError("The provided 'form_class' should be a valid Python class")

        # Simulating the construction of HTML string based on active form class and index
        html_output = "<div id='multi-step-form'>\n"
        for i in range(
            5
        ):  # Assuming there are at most five steps; adjust as per actual requirement
            step_class_name = f"step{i}" if hasattr(form_class, "__iter__") else None

            try:
                step_class: type[dict[str, Any]] = getattr(form_class, step_class_name)

                html_output += f"<div id='step-{i + 1}'>\n"

                # Simulating rendering of the form with navigation buttons
                rendered_step_content = "<p>Rendered content based on active 'form_class' and current index {}</p>".format(
                    step_index
                )

                render_context = {"request": None, f"step_{i+1}": rendered_step_content}
                if step_index == i:
                    html_output += str(render_to_string(rendered_context))

            except AttributeError as e:
                logger.error(
                    f"Attribute error while accessing {step_class_name}: {str(e)}"
                )

            finally:  # Clean up
                try:
                    (
                        delattr(form_class, f"step{i}")
                        if hasattr(form_class, "__iter__")
                        else None
                    )
                except Exception as cleanup_error:
                    logger.warning(
                        f"Cleanup failed for step class attribute removal: {cleanup_error}"
                    )

        html_output += "</div>\n"

        return html_output

    except (KeyError, ValueError) as e:
        raise Exception(
            f"An error occurred while processing the multi-step form: {str(e)}"
        )


# Example Usage
class MultiStepForm(dict):
    step0 = "Content for Step 1"
    step1 = "Content for Step 2"


form_context = {
    "form_class": MultiStepForm,
    "step_index": 1,
}

html_output = render_stepwise_form_with_navigation_buttons(form_context)
print(html_output)


def _render_stepwise_form_with_navigation_buttons_in_context(
    form_class: str, step_index: int = 0
) -> str:
    """
    Helper function that renders a multi-step form with navigation buttons within an existing context.

    Args:
        - form_class (str): The class of the step-wise form to render as HTML string. Must be convertible into Django Form or similar object capable of rendering fields and validation error handling in your framework's terms.

            Example usage: 'myapp.forms.MyForm'

        - step_index (int, optional): Specifies current index within flow; defaults to 0.

    :return str: Rendered HTML string with form for a given class name `form_class` at specified
                   position indexed by an integer value of the argument as described above.

    """

    try:
        if not isinstance(step_index, int):
            raise TypeError(
                f"Argument 'step' must be an integer. Got {type(step_index)} instead."
            )

        step_class = form_class.split(".")[-1]
        rendered_html = "<div id='form-step-{index}'>{'<a href="  # /">Prev</a><button type="submit">Next</button>' if index > 0 else ''}</p>".format(index=step_index)

    except Exception as e:
        raise ValueError(
            f"An error occurred while rendering the form with navigation buttons. Details: {str(e)}"
        ) from None

    return rendered_html
