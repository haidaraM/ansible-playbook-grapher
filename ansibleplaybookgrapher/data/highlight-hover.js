/**
 * This file contains the functions responsible to highlight the plays, roles and tasks when rendering the SVG file in a browser
 * or any SVG reader that support Javascript.
 */

/**
 * The name of the CSS class for highlighted elements
 * @type {string}
 */
const HIGHLIGHT_CLASS = "highlight";

/**
 * The current selected element on the graph
 * @type {null}
 */
let currentSelectedElement = null;

/**
 * Highlight the linked nodes of the given root element
 * @param {Element} parentElement
 * @param {string[]} visitedElements
 */
function highlightLinkedNodes(parentElement, visitedElements = []) {
    $(parentElement).find('link').each(function (index, element) {
        const linkedElementId = $(element).attr('target');
        const edgeId = $(element).attr('edge');

        const currentElement = $(`#${linkedElementId}`);
        currentElement.addClass(HIGHLIGHT_CLASS);

        // Highlight the edge point to the target
        $(`#${edgeId}`).addClass(HIGHLIGHT_CLASS);

        if (!visitedElements.includes(linkedElementId)) {
            visitedElements.push(linkedElementId);
            // Recursively highlight
            highlightLinkedNodes(currentElement, visitedElements);
        }
    })
}


/**
 * Unhighlight the linked nodes of the given root element
 * @param {Element} parentElement
 * @param {string[]} visitedElements
 * @param {boolean} isHover True when we are coming from a mouseleave event. In that case, we should not unhighlight if
 * the parentElement is the current selected element
 */
function unHighlightLinkedNodes(parentElement, visitedElements = [], isHover) {
    const currentSelectedElementId = $(currentSelectedElement).attr('id');
    // Do not unhighlight the current selected element
    if ($(parentElement).attr('id') !== currentSelectedElementId || !isHover) {

        $(parentElement).find('link').each(function (index, element) {
            const linkedElementId = $(element).attr('target');
            const edgeId = $(element).attr('edge');

            const linkedElement = $(`#${linkedElementId}`);

            if (linkedElement.attr('id') !== currentSelectedElementId) {
                linkedElement.removeClass(HIGHLIGHT_CLASS);

                // Unhighlight the edge point to the target
                $(`#${edgeId}`).removeClass(HIGHLIGHT_CLASS);

                if (!visitedElements.includes(linkedElementId)) {
                    visitedElements.push(linkedElementId);
                    // Recursively unhighlight
                    unHighlightLinkedNodes(linkedElement, visitedElements, isHover);
                }
            }

        })
    }

}

/**
 * Hover handler for mouseenter event
 * @param {Event} event
 */
function hoverMouseEnter(event) {
    highlightLinkedNodes(event.currentTarget, []);
}

/**
 * Hover handler for mouseleave event
 * @param {Event} event
 */
function hoverMouseLeave(event) {
    unHighlightLinkedNodes(event.currentTarget, [], true);
}

/**
 * Handler when clicking on some elements
 * @param {Event} event
 */
function clickOnElement(event) {
    const newClickedElement = $(event.currentTarget);

    event.preventDefault(); // Disable the default click behavior since we override it here

    if (newClickedElement.attr('id') === $(currentSelectedElement).attr('id')) { // clicking again on the same element
        newClickedElement.removeClass(HIGHLIGHT_CLASS);
        unHighlightLinkedNodes(currentSelectedElement, [], false);
        currentSelectedElement = null;
    } else { // clicking on a different node

        // Remove highlight from all the nodes linked to the current selected node
        unHighlightLinkedNodes(currentSelectedElement, [], false);
        if (currentSelectedElement) {
            currentSelectedElement.removeClass(HIGHLIGHT_CLASS);
        }

        newClickedElement.addClass(HIGHLIGHT_CLASS);
        highlightLinkedNodes(newClickedElement, []);
        currentSelectedElement = newClickedElement;
    }
}

/**
 * Handler when double clicking on some elements
 * @param {Event} event
 */
function dblClickElement(event) {
    const newElementDlbClicked = event.currentTarget;
    const links = $(newElementDlbClicked).find("a[xlink\\:href]");

    if (links.length > 0) {
        document.location = $(links[0]).attr("xlink:href");
    } else {
        console.log("No links found on this element");
    }
}


$("#svg").ready(function () {
    let playbooks = $("g[id^=playbook_]");
    let plays = $("g[id^=play_]");
    let roles = $("g[id^=role_]");
    let blocks = $("g[id^=block_]");
    let tasks = $("g[id^=pre_task_], g[id^=task_], g[id^=post_task_]");

    playbooks.hover(hoverMouseEnter, hoverMouseLeave);
    playbooks.click(clickOnElement);
    playbooks.dblclick(dblClickElement);

    // Set hover and click events on the plays
    plays.hover(hoverMouseEnter, hoverMouseLeave);
    plays.click(clickOnElement);
    plays.dblclick(dblClickElement);

    // Set hover and click events on the roles
    roles.hover(hoverMouseEnter, hoverMouseLeave);
    roles.click(clickOnElement);
    roles.dblclick(dblClickElement);

    // Set hover and click events on the blocks
    blocks.hover(hoverMouseEnter, hoverMouseLeave);
    blocks.click(clickOnElement);
    blocks.dblclick(dblClickElement);

    // Set hover and click events on the tasks
    tasks.hover(hoverMouseEnter, hoverMouseLeave);
    tasks.click(clickOnElement);
    tasks.dblclick(dblClickElement);

});
