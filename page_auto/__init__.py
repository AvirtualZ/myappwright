import asyncio
import typing
from loguru import logger

from playwright.async_api import Page, BrowserContext, Locator

from page_auto import actions


class PageAuto:
    def __init__(self, page: Page, context: BrowserContext, task_id, delay=1):
        self.page = page
        self.target: Locator = None
        self.context = context
        self.task_id = task_id
        self.delay = delay
        self.logs = []

    def get_locator(self) -> Locator | Page:
        return self.target if self.target else self.page

    def get_by_label(
            self,
            text: typing.Union[str, typing.Pattern[str]],
            *,
            exact: typing.Optional[bool] = None,
    ) -> "PageAuto":
        logger.info(f'定位元素【get_by_label】：{text} ，任务ID：{self.task_id}')
        self.logs.append(text)
        self.target = self.get_locator().get_by_label(text=text, exact=exact)
        return self

    def locator(
            self,
            selector_or_locator: typing.Union[str, "Locator"],
            has_text: typing.Optional[typing.Union[str, typing.Pattern[str]]] = None,
            has_not_text: typing.Optional[typing.Union[str, typing.Pattern[str]]] = None,
            has: typing.Optional["Locator"] = None,
            has_not: typing.Optional["Locator"] = None,
    ) -> "PageAuto":
        logger.info(f'定位元素【locator】：{selector_or_locator} ，任务ID：{self.task_id}')
        self.logs.append(selector_or_locator)
        self.target = self.get_locator().locator(
            selector_or_locator,
            has_text=has_text,
            has_not_text=has_not_text,
            has=has,
            has_not=has_not,
        )
        return self

    def get_by_alt_text(
            self,
            text: typing.Union[str, typing.Pattern[str]],
            *,
            exact: typing.Optional[bool] = None,
    ) -> "PageAuto":
        logger.info(f'定位元素【get_by_alt_text】：{text} ，任务ID：{self.task_id}')
        self.logs.append(f'{text}')
        self.target = self.get_locator().get_by_alt_text(text=text, exact=exact)
        return self

    def get_by_placeholder(
            self,
            text: typing.Union[str, typing.Pattern[str]],
            *,
            exact: typing.Optional[bool] = None,
    ) -> "PageAuto":
        logger.info(f'定位元素【get_by_placeholder】：{text} ，任务ID：{self.task_id}')
        self.logs.append(f'{text}')
        self.target = self.get_locator().get_by_placeholder(text=text, exact=exact)
        return self

    def get_by_test_id(
            self, test_id: typing.Union[str, typing.Pattern[str]]
    ) -> "PageAuto":
        logger.info(f'定位元素【get_by_test_id】：{test_id} ，任务ID：{self.task_id}')
        self.logs.append(f'{test_id}')
        self.target = self.get_locator().get_by_test_id(test_id=test_id)
        return self

    def get_by_text(
            self,
            text: typing.Union[str, typing.Pattern[str]],
            *,
            exact: typing.Optional[bool] = None,
    ) -> "PageAuto":
        logger.info(f'定位元素【get_by_text】：{text} ，任务ID：{self.task_id}')
        self.logs.append(f'{text}')
        self.target = self.get_locator().get_by_text(text=text, exact=exact)
        return self

    def get_by_title(
            self,
            text: typing.Union[str, typing.Pattern[str]],
            *,
            exact: typing.Optional[bool] = True,
    ) -> "PageAuto":
        logger.info(f'定位元素【get_by_title】：{text} ，任务ID：{self.task_id}')
        self.logs.append(f'{text}')
        self.target = self.page.get_by_title(text=text, exact=exact)
        return self

    def get_by_role(
            self,
            role: typing.Literal[
                "alert",
                "alertdialog",
                "application",
                "article",
                "banner",
                "blockquote",
                "button",
                "caption",
                "cell",
                "checkbox",
                "code",
                "columnheader",
                "combobox",
                "complementary",
                "contentinfo",
                "definition",
                "deletion",
                "dialog",
                "directory",
                "document",
                "emphasis",
                "feed",
                "figure",
                "form",
                "generic",
                "grid",
                "gridcell",
                "group",
                "heading",
                "img",
                "insertion",
                "link",
                "list",
                "listbox",
                "listitem",
                "log",
                "main",
                "marquee",
                "math",
                "menu",
                "menubar",
                "menuitem",
                "menuitemcheckbox",
                "menuitemradio",
                "meter",
                "navigation",
                "none",
                "note",
                "option",
                "paragraph",
                "presentation",
                "progressbar",
                "radio",
                "radiogroup",
                "region",
                "row",
                "rowgroup",
                "rowheader",
                "scrollbar",
                "search",
                "searchbox",
                "separator",
                "slider",
                "spinbutton",
                "status",
                "strong",
                "subscript",
                "superscript",
                "switch",
                "tab",
                "table",
                "tablist",
                "tabpanel",
                "term",
                "textbox",
                "time",
                "timer",
                "toolbar",
                "tooltip",
                "tree",
                "treegrid",
                "treeitem",
            ],
            *,
            checked: typing.Optional[bool] = None,
            disabled: typing.Optional[bool] = None,
            expanded: typing.Optional[bool] = None,
            level: typing.Optional[int] = None,
            name: typing.Optional[typing.Union[str, typing.Pattern[str]]] = None,
            pressed: typing.Optional[bool] = None,
            selected: typing.Optional[bool] = None,
            exact: typing.Optional[bool] = None,
    ) -> "PageAuto":
        logger.info(f'定位元素【get_by_role】：{role}-{name}，任务ID：{self.task_id}')
        self.logs.append(f'{role}-{name}')
        self.target = self.get_locator().get_by_role(
            role=role,
            checked=checked,
            disabled=disabled,
            expanded=expanded,
            level=level,
            name=name,
            pressed=pressed,
            selected=selected,
            exact=exact,
        )
        return self

    async def click(self, custom_delay=0, nth=0, timeout: float = 3000, parent=False) -> bool:
        return await actions.click(self.target, self.task_id, self.logs, custom_delay, nth, timeout=timeout, parent=parent)

    async def fill(self, value, custom_delay=0, nth=0) -> bool:
        return await actions.fill(self.target, value, self.task_id, self.logs, custom_delay, nth)

    async def is_visible(self):
        logger.info(f'元素【is_visible】 {self.logs}，任务ID：{self.task_id}')
        return await self.target.count() > 0

    async def all_click(self, custom_delay=0, timeout: float = None) -> bool:
        return await actions.all_click(self.target, self.task_id, self.logs, custom_delay, timeout=timeout)

    async def all(self):
        return await self.target.all()

    async def filter_by_attribute(self, attribute, value):
        all_locators: typing.List[Locator] = await self.all()
        return [item for item in all_locators if item if value in await item.get_attribute(attribute)]
