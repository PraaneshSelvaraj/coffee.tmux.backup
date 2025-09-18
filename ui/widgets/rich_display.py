from textual.widgets import Static
from rich.console import RenderableType
from ..tabs.home import HomeTab
from ..tabs.install import InstallTab
from ..tabs.update import UpdateTab
from ..tabs.remove import RemoveTab
from ..tabs.base import Tab


class RichDisplay(Static):
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state

    def render(self) -> RenderableType:
        tab = self.app_state.current_tab
        layout = Tab("dummy").build_layout(tab)
        if tab == "Home":
            layout["body"].update(HomeTab().create_home_panel(self.app_state))
        elif tab == "Install":
            layout["body"].update(InstallTab().build_panel(self.app_state))
        elif tab == "Update":
            layout["body"].update(UpdateTab().build_panel(self.app_state))
        elif tab == "Remove":
            layout["body"].update(RemoveTab().build_panel(self.app_state))
        layout["tab_bar"].update(Tab("dummy").create_tab_bar(tab))
        return layout
