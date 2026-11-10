"""Pro Person zwei To-do-Listen: der Vorrat und eine Einkaufsliste aus allem, was leer oder fast leer ist."""

from __future__ import annotations

from homeassistant.components.todo import TodoItem, TodoItemStatus, TodoListEntity, TodoListEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ST_DA, ST_LEER, ST_WENIG, STATUS_LABEL
from .entity import PersonEntity, setup_per_person
from .hub import parse_status


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add: AddEntitiesCallback) -> None:
    await setup_per_person(hass, entry, add, (VorratTodo, EinkaufTodo))


class _Base(PersonEntity, TodoListEntity):
    _platform = "todo"

    @staticmethod
    def _desc_to_status(item: TodoItem) -> str:
        if item.status == TodoItemStatus.COMPLETED:
            return ST_LEER
        st = parse_status(item.description, ST_DA)
        return ST_DA if st == ST_LEER else st


class VorratTodo(_Base):
    """Vorrat: abgehakt = leer, Beschreibung „fast leer“ = fast leer, offen = da."""

    _key = "vorrat"
    _attr_icon = "mdi:fridge-outline"
    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
        | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
    )

    @property
    def todo_items(self) -> list[TodoItem]:
        return [
            TodoItem(
                uid=i["id"],
                summary=i["name"],
                status=TodoItemStatus.COMPLETED if i["st"] == ST_LEER else TodoItemStatus.NEEDS_ACTION,
                description=STATUS_LABEL[ST_WENIG] if i["st"] == ST_WENIG else None,
            )
            for i in self.hub.vorrat()
        ]

    async def async_create_todo_item(self, item: TodoItem) -> None:
        st = self._desc_to_status(item)
        existing = self.hub.vorrat_find(item.summary or "")
        self.hub.vorrat_set(existing, item.summary, st)
        self._data.changed()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        st = self._desc_to_status(item)
        self.hub.vorrat_set(item.uid, item.summary, st)
        self._data.changed()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        for uid in uids:
            self.hub.vorrat_delete(uid)
        self._data.changed()


class EinkaufTodo(_Base):
    """Einkaufsliste: alles, was leer oder fast leer ist. Abhaken = gekauft, also wieder da."""

    _key = "einkauf"
    _attr_icon = "mdi:cart-outline"
    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
    )

    @property
    def todo_items(self) -> list[TodoItem]:
        return [
            TodoItem(
                uid=i["id"],
                summary=i["name"],
                status=TodoItemStatus.NEEDS_ACTION,
                description=STATUS_LABEL[i["st"]],
            )
            for i in self.hub.vorrat()
            if i["st"] in (ST_LEER, ST_WENIG)
        ]

    async def async_create_todo_item(self, item: TodoItem) -> None:
        existing = self.hub.vorrat_find(item.summary or "")
        self.hub.vorrat_set(existing, item.summary, ST_LEER)
        self._data.changed()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        if item.status == TodoItemStatus.COMPLETED:
            self.hub.vorrat_set(item.uid, item.summary, ST_DA)
        else:
            self.hub.vorrat_set(item.uid, item.summary)
        self._data.changed()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        for uid in uids:
            self.hub.vorrat_delete(uid)
        self._data.changed()
